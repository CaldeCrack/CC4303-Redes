#!/usr/bin/python3
import sys, os

def main(file_size: int, file_amount: int):
	# Create folder if not exists
	path = os.path.dirname(os.path.abspath(__file__))
	folder: str = f"{path}/files"
	if not os.path.exists(folder):
		os.makedirs(folder)

	# Create files
	size_bytes = file_size * 1024 * 1024
	for i in range(file_amount):
		with open(f"files/archivo_{file_size}_{i}.bin", 'wb') as f:
			f.write(os.urandom(size_bytes))

if len(sys.argv) == 3:
	main(int(sys.argv[1]), int(sys.argv[2]))
else:
	print(f"Wrong amount of parameters\n- Expected: 3\n- Given:{len(sys.argv) - 1}")
