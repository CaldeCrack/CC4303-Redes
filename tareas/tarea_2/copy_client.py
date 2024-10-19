#!/usr/bin/python3
# Selective-Repeat simulation
import jsockets, sys
from threading import Thread, Lock
from datetime import datetime, timedelta
from queue import PriorityQueue


if len(sys.argv) != 5:
	print(f"Use: {sys.argv[0]} pack_sz win_sz host port")
	sys.exit(1)

WIN_SZ_LIMIT: int = 32767
MUTEX: Lock = Lock()
pack_sz: int = int(sys.argv[1])
win_sz: int = int(sys.argv[2])
host: str = sys.argv[3]
port: str = sys.argv[4]

if not (1 <= win_sz <= WIN_SZ_LIMIT):
	print(f"win_sz should be between 1 and 32767 (given {win_sz})")
	sys.exit(1)


class Packet:
	def __init__(self, sqn: bytes | int, data: bytes | None = None, ack: bool = False) -> None:
		if type(sqn) == int:
			self.sqn: bytes = sqn.to_bytes(2, "big")
			self.int_sqn: int = sqn
		else:
			self.sqn: bytes = sqn
			self.int_sqn: int = int.from_bytes(sqn, "big")
		self.data: bytes | None = data
		self.ack: bool = ack

	def received(self) -> None:
		MUTEX.acquire()
		self.ack = True
		MUTEX.release()

	@property
	def data(self) -> bytes:
		return self._data

	@data.setter
	def data(self, value: bytes) -> None:
		MUTEX.acquire()
		self._data = value
		MUTEX.release()

	def __repr__(self):
		return self.__str__()

	def __str__(self) -> str:
		return f"sqn={self.int_sqn} | ack={self.ack} | data={self.data[0:5] if self.data else None}..."

recv_window: list[Packet] = []
sndr_window: list[Packet] = []
for i in range(win_sz):
	packet: Packet = Packet(i)
	recv_window.append(packet)
	sndr_window.append(packet)
sndr_min: int = 0
sndr_max: int = win_sz - 1

sndr_errors: int = 0
recv_errors: int = 0

def sequence_number():
	num: int = 0
	limit: int = 65535
	while num <= limit:
		byte_number: bytes = num.to_bytes(2, "big")
		yield byte_number
		num = (num + 1) % limit

def advance_window(win: list[Packet], sndr: bool = False) -> int:
	while win[0].ack:
		if sndr:
			sys.stdout.buffer.write(win[0].data)
		del win[0]
		if not sndr:
			next_index: int = (win[-1].int_sqn + 1) % WIN_SZ_LIMIT
			packet: Packet = Packet(next_index)
			recv_window.append(packet)
			sndr_window.append(packet)
	return win[0].int_sqn

# ########### RECEPTOR ###########
def Rdr(s, pack_sz: int, win_sz: int):
	global recv_errors
	recv_min: int = 0
	recv_max: int = win_sz - 1

	while True:
		try:
			rec: bytes = s.recv(pack_sz)
			recv_sqn: int = int.from_bytes(rec[0:2], "big")
			data: bytes = rec[2:]

			if (recv_min <= recv_sqn <= recv_max):
				recv_window[recv_sqn - recv_min].received()
				recv_window[recv_sqn - recv_min].data = data
				recv_min = advance_window(recv_window)
				recv_max = recv_min + win_sz - 1
			else:
				recv_errors += 1

			if not data:
				break
		except:
			break
	print("Receiver finished")

s = jsockets.socket_udp_connect(host, port)
if s is None:
	print('Could not open socket')
	sys.exit(1)

receiver: Thread = Thread(target=Rdr, args=(s, pack_sz, win_sz))
receiver.start()


# ########### EMISOR ###########
def peek_time(pq) -> datetime:
	return pq.queue[0][0]

def peek_packet(pq) -> Packet:
	return pq.queue[0][1]

timeouts: PriorityQueue = PriorityQueue() # time, packet
timeout: float = 0.5
sqn = sequence_number()
n: bytes = next(sqn)
data: bytes = b'\x11'

while True:
	int_n: int = int.from_bytes(n, "big")
	if sndr_min <= int_n <= sndr_max and data:
		data = sys.stdin.buffer.read(pack_sz - 2)

		# envío de paquetes
		if data:
			sndr_window[int_n - sndr_min].data = data
			delta: timedelta = timedelta(seconds=timeout)
			expire = (datetime.now() + delta, sndr_window[int_n - sndr_min])
			timeouts.put(expire)
			s.send(n + data)
			n = next(sqn)

	# manejar timeouts
	if datetime.now() >= peek_time(timeouts):
		index: int = peek_packet(timeouts).int_sqn - sndr_min

		if (packet := peek_packet(timeouts)).int_sqn < sndr_min or packet.int_sqn > sndr_max or packet.ack:
			timeouts.get()
			sndr_min = advance_window(sndr_window, True)
			sndr_max = sndr_min + win_sz - 1
		else: # retransmitir paquete
			sndr_errors += 1
			s.send(packet.sqn + packet.data)
			timeouts.get()
			delta = timedelta(seconds=timeout)
			expire = (datetime.now() + delta, packet)
			timeouts.put(expire)

	if timeouts.empty() and not data:
		s.send(n)
		print("\nSender finished")
		break

print(f"{sndr_errors = }")
print(f"{recv_errors = }")

receiver.join()
s.close()
