#!/bin/bash

PATH = "./files"

sizes = (128, 1024, 2048)

for size in sizes {
	# 1 archivo grande
	{ time ./client_bw.py {size} localhost 1818 < files/archivo_0.bin > result.bin ; } 2>> time.txt
}

