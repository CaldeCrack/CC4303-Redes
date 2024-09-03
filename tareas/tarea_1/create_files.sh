#!/bin/sh

# Crear 3 archivos grandes
./create_files.py 500 3

# Crear 20 archivos medianos
./create_files.py 75 20

# Crear 100 archivos pequeños
./create_files.py 15 100
