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
sizes=(1024)
for size in "${sizes[@]}"
do
	echo -e "\n----- size:${size} -----"
	echo -e "\n----- size:${size} -----" >> time.txt

	# 1 archivo grande
	echo "Generando tiempo de 1 archivo grande"
	echo -e "\n- 1 archivo grande" >> time.txt
	echo -n -e "Archivo: ${folder_path}/archivo_500_0.bin\nTiempo: " >> time.txt
	{ time ./client_bw.py ${size} anakena.dcc.uchile.cl 1820 < ${folder_path}/archivo_500_0.bin > result.bin ; } 2>&1 | grep real | cut -f 2 >> time.txt

	echo "Generando tiempo de 3 archivos grandes en paralelo"
	echo -e "\n- 3 archivos grandes" >> time.txt
	for i in {0..2}
	do
		(
			time_output=$({ time ./client_bw.py ${size} anakena.dcc.uchile.cl 1820 < files/archivo_500_${i}.bin > result.bin ; } 2>&1)
			{
				flock -x 200
				echo -n -e "Archivo: ${folder_path}/archivo_500_${i}.bin\nTiempo: " >> time.txt
				echo "$time_output" | grep real | cut -f 2 >> time.txt
			} 200>time.txt.lock
		) &
	done
	wait

	echo "Generando tiempo de 20 archivos medianos en paralelo"
	echo -e "\n- 20 archivos medianos" >> time.txt
	for i in {0..19}
	do
		(
			time_output=$({ time ./client_bw.py ${size} anakena.dcc.uchile.cl 1820 < files/archivo_75_${i}.bin > result.bin ; } 2>&1)
			{
				flock -x 200
				echo -n -e "Archivo: ${folder_path}/archivo_75_${i}.bin\nTiempo: " >> time.txt
				echo "$time_output" | grep real | cut -f 2 >> time.txt
			} 200>time.txt.lock
		) &
	done
	wait

	echo "Generando tiempo de 100 archivos pequeños en paralelo"
	echo -e "\n- 100 archivos pequeños" >> time.txt
	for i in {0..99}
	do
		(
			time_output=$({ time ./client_bw.py ${size} anakena.dcc.uchile.cl 1820 < files/archivo_15_${i}.bin > result.bin ; } 2>&1)
			{
				flock -x 200
				echo -n -e "Archivo: ${folder_path}/archivo_15_${i}.bin\nTiempo: " >> time.txt
				echo "$time_output" | grep real | cut -f 2 >> time.txt
			} 200>time.txt.lock
		) &
	done
	wait
done

rm -f time.txt.lock
rm -f result.bin
echo ""
