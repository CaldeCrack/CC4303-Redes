#!/bin/bash

# Crear 3 archivos grandes
./create_file.py 500 3

# Crear 20 archivos medianos
./create_file.py 75 20

# Crear 100 archivos pequeños
./create_file.py 15 100
