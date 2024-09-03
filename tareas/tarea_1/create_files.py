#!/usr/bin/python3
import sys, os

def create_files(file_size: int, file_amount: int):
	size_bytes = file_size * 1024 * 1024
	for i in range(file_amount):
		print(f"Creando archivo_{file_size}_{i}.bin de tamaño {file_size}MB")
		with open(f"files/archivo_{file_size}_{i}.bin", 'wb') as f:
			f.write(os.urandom(size_bytes))

if len(sys.argv) == 3:
	create_files(int(sys.argv[1]), int(sys.argv[2]))
else:
	print(f"Wrong amount of parameters\n- Expected: 3\n- Given:{len(sys.argv) - 1}")
