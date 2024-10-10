#!/usr/bin/python3
# Selective-Repeat simulation
import jsockets, sys, threading, DoubleLinkedQueue as dlq

if len(sys.argv) != 5:
	print(f"Use: {sys.argv[0]} pack_sz win_sz host port")
	sys.exit(1)

pack_sz: int = int(sys.argv[1])
win_sz: int = int(sys.argv[2])
host: str = sys.argv[3]
port: str = sys.argv[4]

if not (1 <= sys.argv[2] <= 32767):
	print(f"win_sz should be between 1 and 32767 (given {win_sz})")
	sys.exit(1)

def sequence_number():
	num: int = 0
	limit: int = 65535
	while num <= limit:
		byte_number = num.to_bytes(2, "big")
		yield byte_number
		num = (num + 1) % limit

# receptor
def Rdr(s, pack_sz, win_sz):
	win_min: int = 1
	win_max: int = win_sz
	cola = dlq.DoubleLinkedQueue

	while True:
		try:
			data = s.recv(pack_sz)
			recv_sqn: int = int.from_bytes(data[0:2], "big")

			if not (win_min <= recv_sqn <= win_max):
				pass
			if recv_sqn == win_min:
				win_min = recv_sqn
				win_max = recv_sqn + win_max

			if not data:
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

# emisor
while True:
	byte_s = sys.stdin.buffer.read(pack_sz)
	if not byte_s:
		s.shutdown(jsockets.socket.SHUT_WR)
		break
	s.send(byte_s)

newthread.join()
s.close()
