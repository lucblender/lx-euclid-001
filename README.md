# lx-euclid

lx-euclid by AtoVproject & Lucas Bonvin

The AtoVproject lx-euclid is a 4-channel trigger sequencer with a standout feature: two touch-sensitive rings that redefine hands-on control. These rings, paired with full colour circular display, offer an unparalleled, intuitive interface designed for fast, real-time performance. The touch rings make it incredibly easy to interact with your sequences, allowing you to apply mutes, fills, and resets on the fly. This immediate tactile response puts creative control directly at your fingertips, making it perfect for both live improvisation and studio work.

![lx-euclid picture](/pictures/lx-euclid.png)

More info about the module can be found on its [product page](https://atovproject.de/products/atovproject-lx-euclid) and if you want to get yours, go to [AtoVproject store](https://atovproject.de/store).

- [lx-euclid](#lx-euclid)
  - [Installation of last firmware](#installation-of-last-firmware)
  - [Build an UF2 image from source](#build-an-uf2-image-from-source)
    - [Requirement](#requirement)
      - [Main repository : lx-euclid](#main-repository--lx-euclid)
      - [Micropython](#micropython)
      - [dir2uf2](#dir2uf2)
    - [Build the image with provided shell script](#build-the-image-with-provided-shell-script)
  - [License](#license)

## Installation of last firmware

Download the last UF2 image in the [releases](https://github.com/lucblender/lx-euclid-001/releases/)

- Power off your eurorack system
- Remove the module from your eurorack system
- Plug the USB-C cable in the module and plug it to your computer **while** pressing the USB boot button
  - When connected to your computer, a drive should open (like a USB stick)
- Drag and drop the downloaded UF2 file
  - After this action, the module will reboot with the new software
- Remove USB-C cable, rewire your module into your eurorack system and power up your rack

## Build an UF2 image from source

**This chapter is for advanced programmer only that want to play with the current *develop* code or want to create custom micropython firmware.**

The following instruction are for Linux users. For Windows user, Ubuntu WSL is highly recommended.

### Requirement

To build and UF2 image, you will need:

- [This repository](#main-repository--lx-euclid)
  - micropython sources
  - build scripts
- [Micropython sources](#micropython)
  - Will allow you to create a custom micropython UF2
- [dir2uf2](#dir2uf2)
  - Python based tool to pack a directory of files into a LFSV2 filesystem and save as .uf2

#### Main repository : lx-euclid

```git clone https://github.com/lucblender/lx-euclid-001.git```

#### Micropython

More detailed information can be found in the [Raspberry Pi Pico Python SDK PDF book](https://datasheets.raspberrypi.com/pico/raspberry-pi-pico-python-sdk.pdf).

Install micropython and submodules:

``` shell
git clone https://github.com/micropython/micropython.git --branch master
cd micropython
make -C ports/rp2 submodules

```

#### dir2uf2

dir2uf2 require python to work.

``` shell
sudo apt-get install python3
sudo apt-get install python3-pip
```

When python3 is installed, you can clone the git and install the required python packages:

``` shell
git clone git@github.com:Gadgetoid/dir2uf2.git
cd dir2uf2
pip3 install -r requirements-micropython-1.23.0.txt
```

### Build the image with provided shell script

The shell script [build-uf2.sh](/shell%20scripts/build-uf2.sh) will create a complete UF2 image ready for upload to the lx-euclid module. This script will:

- Copy all the python source of this repository into the micropython repository rp2 port
- Build a first UF2 micropython image including lx-euclid code
- Copy needed binaries (pictures in bin format) into the dir2uf2 directory
- Create the final UF2 image derived from the micropython image with binaries in the filesystem
- Copy this UF2 image in the desired path

Many from this script require path to specific directories. All those paths needs to be edited and added to the [lx-euclid.env](/shell%20scripts/lx-euclid.env) file:

- line 3, LX_EUCLID_REPO_DIRECTORY : this repository path
- line 5, MICROPYTHON_DIRECTORY : micropython repository path
- line 7, DIR_2_UF2_FOLDER : dir2uf2 repository path
- line 9, UF2_OUTPUT_FILE : output file path

When the [lx-euclid.env](/shell%20scripts/lx-euclid.env) file is correctly edited, you can launch the compilation with:

```shell
./build-uf2.sh
```

With your newly created UF2 image, you can upload it to the lx-euclid module following the instruction in the [Installation of last firmware](#installation-of-last-firmware) chapter.

## License

This project is licensed under the [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) License. You may use, modify, and share it for non-commercial purposes.
