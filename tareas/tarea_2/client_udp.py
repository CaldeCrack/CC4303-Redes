#!/usr/bin/python3
# Selective-Repeat simulation
import jsockets, sys, threading

def Rdr(s, size):
	while True:
		try:
			data = s.recv(size)
			if not data:
				break
			sys.stdout.buffer.write(data)
		except:
			break

if len(sys.argv) != 4:
	print(f"Use: {sys.argv[0]} size host port")
	sys.exit(1)

s = jsockets.socket_tcp_connect(sys.argv[2], sys.argv[3])
if s is None:
	print('Could not open socket')
	sys.exit(1)

size: int = int(sys.argv[1])
newthread = threading.Thread(target=Rdr, args=(s, size))
newthread.start()

while True:
	byte_s = sys.stdin.buffer.read(size)
	if not byte_s:
		s.shutdown(jsockets.socket.SHUT_WR) # sin esta línea no terminaba de ejecutarse el código
		break
	s.send(byte_s)

newthread.join()
s.close()
