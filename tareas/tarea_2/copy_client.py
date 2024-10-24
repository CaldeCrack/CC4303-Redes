#!/usr/bin/python3
# Selective-Repeat simulation
import jsockets, sys
from threading import Thread, Lock
from datetime import datetime, timedelta
from queue import PriorityQueue


if len(sys.argv) != 5:
	print(f"Use: {sys.argv[0]} pack_sz win_sz host port", file=sys.stderr)
	sys.exit(1)

SQN_LIMIT: int = 65536 # suma 1 al usar en módulo
WIN_SZ_LIMIT: int = 32767
MUTEX: Lock = Lock()
pack_sz: int = int(sys.argv[1])
win_sz: int = int(sys.argv[2])
host: str = sys.argv[3]
port: str = sys.argv[4]

if not (1 <= win_sz <= WIN_SZ_LIMIT):
	print(f"win_sz should be between 1 and 32_767 (inclusive)\ngiven {win_sz}", file=sys.stderr)
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
		self.timeout: float = 0.5

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
	while num < SQN_LIMIT:
		byte_number: bytes = num.to_bytes(2, "big")
		yield byte_number
		num = (num + 1) % SQN_LIMIT

def advance_window(win: list[Packet], sndr: bool = False) -> int:
	global timeout
	while win[0].ack:
		if sndr:
			sys.stdout.buffer.write(win[0].data)
			if not win[0].retransmission:
				timeout = 3.0 * ((win[0].recv_time - win[0].sndr_time) / timedelta(milliseconds=1)) / 1000.0
		else:
			packet: Packet = Packet((win[-1].int_sqn + 1) % SQN_LIMIT)
			recv_window.append(packet)
			sndr_window.append(packet)
		del win[0]
	return win[0].int_sqn

def in_window(sqn: int, lower: int, upper: int) -> bool:
	if lower < upper:
		return lower <= sqn <= upper
	else:
		return lower <= sqn < SQN_LIMIT or 0 <= sqn <= upper

# ########### RECEPTOR ###########
def Rdr(s, pack_sz: int, win_sz: int):
	global recv_errors
	recv_min: int = 0
	recv_max: int = win_sz - 1

	while True:
		rec: bytes = s.recv(pack_sz)
		recv_sqn: int = int.from_bytes(rec[0:2], "big")
		data: bytes = rec[2:]

		if in_window(recv_sqn, recv_min, recv_max):
			index: int = (recv_sqn - recv_min) % SQN_LIMIT
			if recv_window[index].ack or recv_sqn != recv_min:
				recv_errors += 1
			recv_window[index].received()
			recv_window[index].data = data
			recv_window[index].received_time()
			recv_min = advance_window(recv_window)
			recv_max = (recv_min + win_sz - 1) % SQN_LIMIT
		else:
			recv_errors += 1

		if not data:
			break

	print(f"{recv_errors = :_}", file=sys.stderr)

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
	if in_window(int_n, sndr_min, sndr_max) and data:
		data = sys.stdin.buffer.read(pack_sz - 2)

		# envío de paquetes
		if data:
			index: int = (int_n - sndr_min) % SQN_LIMIT
			sndr_window[index].data = data
			sndr_window[index].sent_time()
			sndr_window[index].timeout = timeout
			delta: timedelta = timedelta(seconds=sndr_window[index].timeout)
			expire = (datetime.now() + delta, sndr_window[index])
			timeouts.put(expire)
			s.send(n + data)
			n = next(sqn)

	# manejar 'ACKs'
	if not timeouts.empty():
		if (packet := peek_packet(timeouts)).ack or not in_window(packet.int_sqn, sndr_min, sndr_max):
			timeouts.get()
			sndr_min = advance_window(sndr_window, True)
			sndr_max = (sndr_min + win_sz - 1) % SQN_LIMIT
		elif peek_time(timeouts) <= datetime.now(): # retransmitir paquete
			packet.sent_time()
			packet.retransmitted()
			s.send(packet.sqn + packet.data)
			timeouts.get()
			delta = timedelta(seconds=packet.timeout)
			expire = (datetime.now() + delta, packet)
			timeouts.put(expire)
			sndr_errors += 1
	elif not data:
		print(f"Using: pack_size={pack_sz:_} | max_window={win_sz:_}", file=sys.stderr)
		print(f"{sndr_errors = :_}", file=sys.stderr)
		s.send(n)
		break

receiver.join()
s.close()