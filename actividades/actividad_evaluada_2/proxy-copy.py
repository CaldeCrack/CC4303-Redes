#!/usr/bin/python3
import os, signal, sys, threading, jsockets

def childdeath(signum, frame):
    os.waitpid(-1, os.WNOHANG)


def copy_sock(conn1, conn2, file, text):
    while True:
        try:
            data = conn1.recv(1500)
        except:
            data = None
        if not data: break
        with open(file, "a", encoding="utf8") as f:
            f.write(f"\n\n{text} server\n{data.decode()}")
        conn2.send(data)

    conn2.close()
    print('lost')


# Este el servidor de un socket ya conectado
# y el cliente del verdadero servidor (host, portout)
def proxy(conn, host, portout, file):
    conn2 = jsockets.socket_tcp_connect(host, portout)
    if conn2 is None:
        print(f"conexión rechazada por {host}, {portout}")
        sys.exit(1)
    print('Cliente conectado')

	# copy_sock() corre en ambos threads, uno de conn->conn2 y otro de conn2->conn
    newthread1 = threading.Thread(target=copy_sock, daemon=True, args=(conn, conn2, file, ">>> to"))
    newthread1.start()
    copy_sock(conn2, conn, file, "<<< from")
    print('Cliente desconectado')


if len(sys.argv) != 5:
    print(f"Use: {sys.argv[0]} port-in host port-out file")
    sys.exit(1)


portin = sys.argv[1]
host = sys.argv[2]
portout = sys.argv[3]
file = sys.argv[4]
signal.signal(signal.SIGCHLD, childdeath)
s = jsockets.socket_tcp_bind(portin)


if s is None:
    print('bind falló')
    sys.exit(1)


while True:
    conn, addr = s.accept()
    pid = os.fork()
    if pid == 0: # Este es el hijo
        s.close() # Cierro el socket que no voy a usar
        proxy(conn, host, portout, file)
        sys.exit(0)
    else:
        conn.close() # Cierro el socket que no voy a usar
