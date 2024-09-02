#!/usr/bin/python3
import sys, os

def main(file_size: int, file_amount: int):
	# Delete files in folder
	path = os.path.dirname(os.path.abspath(__file__))
	path += "/files"
	folder = os.listdir(path)
	for f in folder:
		os.remove(f"{path}/{f}")

	# Create files
	size_bytes = file_size * 1024 * 1024
	for i in range(file_amount):
		with open(f"files/archivo_{i}.bin", 'wb') as f:
			f.write(os.urandom(size_bytes))

if len(sys.argv) == 3:
	main(int(sys.argv[1]), int(sys.argv[2]))
else:
	print(f"Error\nExpected amount of parameters: 2\nGiven:{len(sys.argv) - 1}")
