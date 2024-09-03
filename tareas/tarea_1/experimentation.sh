#!/bin/bash

# Configuración inicial
mkdir -p files
folder_path="./files"

if [ ! -n "$(ls -A ${folder_path})" ]
then
	./create_files.sh
else
	echo "Archivos ya existen"
fi

rm -f time.txt

# Ejecutar los procesos sobre los archivos
sizes=(128 1024 8192)
for size in "${sizes[@]}"
do
	echo -e "\n----- size:${size} -----"
	echo -e "\n----- size:${size} -----" >> time.txt

	# 1 archivo grande
	echo "Generando tiempo de 1 archivo grande"
	echo -e "\n- 1 archivo grande" >> time.txt
	echo -n -e "Archivo: ${folder_path}/archivo_500_0.bin\nTiempo: " >> time.txt
	{ time ./client_bw.py ${size} localhost 1818 < ${folder_path}/archivo_500_0.bin > result.bin ; } 2>&1 | grep real | cut -f 2 >> time.txt

	echo "Generando tiempo de 3 archivos grandes en paralelo"
	echo -e "\n- 3 archivos grandes" >> time.txt
	for i in {0..2}
	do
		echo -n -e "Archivo: ${folder_path}/archivo_500_${i}.bin\nTiempo: " >> time.txt
		{ time ./client_bw.py ${size} localhost 1818 < files/archivo_500_${i}.bin > result.bin ; } 2>&1 | grep real | cut -f 2 >> time.txt &
	done
	wait

	echo "Generando tiempo de 20 archivos medianos en paralelo"
	echo -e "\n- 20 archivos medianos" >> time.txt
	for i in {0..19}
	do
		echo -n -e "Archivo: ${folder_path}/archivo_75_${i}.bin\nTiempo: " >> time.txt
		{ time ./client_bw.py ${size} localhost 1818 < files/archivo_75_${i}.bin > result.bin ; } 2>&1 | grep real | cut -f 2 >> time.txt &
	done
	wait

	echo "Generando tiempo de 100 archivos pequeños en paralelo"
	echo -e "\n- 100 archivos pequeños" >> time.txt
	for i in {0..99}
	do
		echo -n -e "Archivo: ${folder_path}/archivo_15_${i}.bin\nTiempo: " >> time.txt
		{ time ./client_bw.py ${size} localhost 1818 < files/archivo_15_${i}.bin > result.bin ; } 2>&1 | grep real | cut -f 2 >> time.txt &
	done
	wait
done

echo ""
