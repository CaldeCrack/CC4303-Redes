#!/usr/bin/python3
# Selective-Repeat simulation
import jsockets, sys, threading


WIN_SZ_LIMIT = 32767

if len(sys.argv) != 5:
	print(f"Use: {sys.argv[0]} pack_sz win_sz host port")
	sys.exit(1)

pack_sz: int = int(sys.argv[1])
win_sz: int = int(sys.argv[2])
host: str = sys.argv[3]
port: str = sys.argv[4]

if not (1 <= sys.argv[2] <= WIN_SZ_LIMIT):
	print(f"win_sz should be between 1 and 32767 (given {win_sz})")
	sys.exit(1)

def sequence_number():
	num: int = 0
	limit: int = 65535
	while num <= limit:
		byte_number = num.to_bytes(2, "big")
		yield byte_number
		num = (num + 1) % limit

def advance_window(window: list) -> None:
	while window[0][1]:
		del window[0]
		window.append(((window[-1][0] + 1) % WIN_SZ_LIMIT, False))

# receptor
def Rdr(s, pack_sz, win_sz):
	win_min: int = 0
	win_max: int = win_sz - 1
	# window = DLQ(win_sz)
	window: list = [(i, False) for i in range(win_sz)]

	while True:
		try:
			data = s.recv(pack_sz)
			recv_sqn: int = int.from_bytes(data[0:2], "big")
			index: int = recv_sqn - win_min
			window[index] = (recv_sqn, True)

			if recv_sqn == win_min:
				win_min = recv_sqn
				win_max = recv_sqn + win_max
				advance_window(window)

			if len(data) == 2:
				break
			sys.stdout.buffer.write(data)
		except:
			break

s = jsockets.socket_udp_connect(host, port)
if s is None:
	print('Could not open socket')
	sys.exit(1)

newthread = threading.Thread(target=Rdr, args=(s, pack_sz, win_sz))
newthread.start()
sqn = sequence_number()

# emisor
while True:
	byte_s = sys.stdin.buffer.read(pack_sz - 2)
	if not byte_s:
		s.shutdown(jsockets.socket.SHUT_WR)
		break
	s.send(next(sqn) + byte_s)

newthread.join()
s.close()
