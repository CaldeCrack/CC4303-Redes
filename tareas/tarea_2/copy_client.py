#!/usr/bin/python3
# Selective-Repeat simulation
import jsockets, sys, threading, queue
from datetime import datetime, timedelta


WIN_SZ_LIMIT = 32767

if len(sys.argv) != 5:
	print(f"Use: {sys.argv[0]} pack_sz win_sz host port")
	sys.exit(1)

pack_sz: int = int(sys.argv[1])
win_sz: int = int(sys.argv[2])
host: str = sys.argv[3]
port: str = sys.argv[4]

if not (1 <= win_sz <= WIN_SZ_LIMIT):
	print(f"win_sz should be between 1 and 32767 (given {win_sz})")
	sys.exit(1)

recv_window: list = [(i, False) for i in range(win_sz)] # sequence number, ack
sndr_window: list = [(i, False, None) for i in range(win_sz)] # sequence number, ack, data

def sequence_number():
	num: int = 0
	limit: int = 65535
	while num <= limit:
		byte_number = num.to_bytes(2, "big")
		yield byte_number
		num = (num + 1) % limit

def advance_window(win: list, q=None) -> int:
	while win[0][1]:
		del win[0]
		win.append(((win[-1][0] + 1) % WIN_SZ_LIMIT, False))
		if q:
			q.get()
	return win[0][0]

# ########### RECEPTOR ###########
def Rdr(s, pack_sz, win_sz):
	recv_min: int = 0
	recv_max: int = win_sz - 1

	while True:
		try:
			recv_sqn: int = int.from_bytes(s.recv(2), "big")
			data: bytes = s.recv(pack_sz - 2)
			index: int = recv_sqn - recv_min

			if (recv_min <= recv_sqn <= recv_max):
				recv_window[index] = (recv_sqn, True)
				sndr_window[index] = (recv_sqn, True, data)

			if recv_sqn == recv_min:
				recv_min = advance_window(recv_window)
				recv_max = recv_min + win_sz

			sys.stdout.buffer.write(data)
			if len(data) == 2:
				break
		except:
			break

s = jsockets.socket_udp_connect(host, port)
if s is None:
	print('Could not open socket')
	sys.exit(1)

receiver = threading.Thread(target=Rdr, args=(s, pack_sz, win_sz))
receiver.start()


# ########### EMISOR ###########
def peek_time(pq):
	return pq.queue[0][0]

def peek_value(pq) -> int:
	return pq.queue[0][1]

timeout: float = 0.5
sqn = sequence_number()
sndr_min: int = 0
sndr_max: int = win_sz - 1
timeouts = queue.PriorityQueue() # time, sequence number
n: int = next(sqn)

while True:
	byte_s = sys.stdin.buffer.read(pack_sz - 2)
	int_n: int = int.from_bytes(n, "big")

	if sndr_min <= int_n <= sndr_max and byte_s:
		s.send(n + byte_s)
		sndr_window[int_n - sndr_min] = (int_n, False, byte_s)
		delta = timedelta(seconds=timeout)
		expire = (datetime.now() + delta, int_n)
		timeouts.put(expire)
		n = next(sqn)
	elif not byte_s:
		s.send(n)

	if datetime.now() >= peek_time(timeouts):
		# print(timeouts.qsize())
		index: int = peek_value(timeouts) - sndr_min
		if not (packet := sndr_window[index])[1]: # retransmitir paquete
			timeouts.get()
			s.send(packet[0].to_bytes(2, "big") + packet[2])
			delta = timedelta(seconds=timeout)
			expire = (datetime.now() + delta, int_n)
			timeouts.put(expire)
		elif sndr_min == peek_value(timeouts):
			sndr_min = advance_window(sndr_window, timeouts)
			sndr_max = sndr_min + win_sz

	if timeouts.empty():
		break

receiver.join()
s.close()
