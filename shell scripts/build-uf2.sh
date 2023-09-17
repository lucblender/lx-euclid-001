#!/bin/bash

cd micropython/ports/rp2/
make -j4
cp ./build-RPI_PICO/firmware.uf2 /mnt/c/Users/lucas/Documents/randomGit/lx-euclid-001/uf2/lx-euclid-001.uf2