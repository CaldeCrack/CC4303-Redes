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
	def __init__(self, sqn: bytes | int) -> None:
		if type(sqn) == int:
			self.sqn: bytes = sqn.to_bytes(2, "big")
			self.int_sqn: int = sqn
		else:
			self.sqn: bytes = sqn
			self.int_sqn: int = int.from_bytes(sqn, "big")
		self.data: bytes | None = None
		self.ack: bool = False
		self.sndr_time: datetime | None = None
		self.recv_time: datetime | None = None
		self.retransmission: bool = False

	def received(self) -> None:
		MUTEX.acquire()
		self.ack = True
		MUTEX.release()

	def sent_time(self) -> None:
		MUTEX.acquire()
		self.sndr_time = datetime.now()
		MUTEX.release()

	def received_time(self) -> None:
		MUTEX.acquire()
		self.recv_time = datetime.now()
		MUTEX.release()

	def retransmitted(self) -> None:
		MUTEX.acquire()
		self.retransmission = True
		MUTEX.release()

	@property
	def data(self) -> bytes:
		return self._data

	@data.setter
	def data(self, value: bytes) -> None:
		MUTEX.acquire()
		self._data = value
		MUTEX.release()

	def __lt__(self, other) -> bool:
		return self.int_sqn < other.int_sqn


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
timeout: float = 0.5

def sequence_number():
	num: int = 0
	limit: int = 65535
	while num <= limit:
		byte_number: bytes = num.to_bytes(2, "big")
		yield byte_number
		num = (num + 1) % limit

def advance_window(win: list[Packet], sndr: bool = False) -> int:
	global timeout
	while win[0].ack:
		if sndr:
			sys.stdout.buffer.write(win[0].data)
			# en el mismo momento en que se recibe el paquete se obtiene el 'ACK' dada la memoria compartida
			if not win[0].retransmission:
				timeout = 3.0 * ((win[0].recv_time - win[0].sndr_time) / timedelta(milliseconds=1)) / 1000.0
		del win[0]
		if not sndr:
			packet: Packet = Packet((win[-1].int_sqn + 1) % WIN_SZ_LIMIT)
			recv_window.append(packet)
			sndr_window.append(packet)
	return win[0].int_sqn

# ########### RECEPTOR ###########
def Rdr(s, pack_sz: int, win_sz: int):
	global recv_errors
	latest: int = -1
	recv_min: int = 0
	recv_max: int = win_sz - 1

	while True:
		rec: bytes = s.recv(pack_sz)
		recv_sqn: int = int.from_bytes(rec[0:2], "big")
		data: bytes = rec[2:]

		if (recv_min <= recv_sqn <= recv_max):
			if recv_window[recv_sqn - recv_min].ack: # paquete reentregado
				recv_errors += 1
			elif recv_sqn != latest + 1: # paquete en desorden
				latest = recv_sqn
				recv_errors += 1
			recv_window[recv_sqn - recv_min].received()
			recv_window[recv_sqn - recv_min].data = data
			recv_window[recv_sqn - recv_min].received_time()
			recv_min = advance_window(recv_window)
			recv_max = recv_min + win_sz - 1
		else: # paquete fuera de la ventana de recepción
			recv_errors += 1

		latest = max(latest, recv_sqn)
		if not data:
			break

	print("\n- Receiver finished")
	print(f"{recv_errors = }")

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
			sndr_window[int_n - sndr_min].sent_time()
			delta: timedelta = timedelta(seconds=timeout)
			expire = (datetime.now() + delta, sndr_window[int_n - sndr_min])
			timeouts.put(expire)
			s.send(n + data)
			n = next(sqn)

	# manejar timeouts
	if datetime.now() >= peek_time(timeouts):
		index: int = (packet := peek_packet(timeouts)).int_sqn - sndr_min

		if packet.ack or packet.int_sqn < sndr_min or packet.int_sqn > sndr_max:
			timeouts.get()
			sndr_min = advance_window(sndr_window, True)
			sndr_max = sndr_min + win_sz - 1
		else: # retransmitir paquete
			packet.retransmitted()
			s.send(packet.sqn + packet.data)
			timeouts.get()
			delta = timedelta(seconds=timeout)
			expire = (datetime.now() + delta, packet)
			timeouts.put(expire)
			sndr_errors += 1

	if timeouts.empty() and not data:
		print("\n- Sender finished")
		print(f"{sndr_errors = }")
		s.send(n)
		break

receiver.join()
s.close()
