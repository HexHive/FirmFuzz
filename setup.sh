#!/bin/bash

#Setting up GCC and make
sudo apt update
sudo apt install gcc make bc qemu

#Setting up the toolchains
sudo mkdir -p /opt/cross
sudo cp toolchains/* /opt/cross
cd /opt/cross
sudo tar -xf arm-linux-musleabi.tar.xz 
sudo tar -xf mipseb-linux-musl.tar.xz 
sudo tar -xf mipsel-linux-musl.tar.xz 
cd -

mkdir -p ./framework/kernel_firmfuzz/build/mipseb
mkdir -p ./framework/kernel_firmfuzz/build/mipsel
mkdir -p ./framework/kernel_firmfuzz_armel/build/armel

cp ./framework/kernel_firmfuzz/config.mipseb ./framework/kernel_firmfuzz/build/mipseb/.config
cp ./framework/kernel_firmfuzz/config.mipsel ./framework/kernel_firmfuzz/build/mipsel/.config
cp ./framework/kernel_firmfuzz_armel/config.armel ./framework/kernel_firmfuzz_armel/build/armel/.config

# Adding toolchains to PATH
echo "PATH=$PATH:/opt/cross/mipsel-linux-musl/bin:/opt/cross/mipseb-linux-musl/bin:/opt/cross/arm-linux-musleabi/bin" >> ~/.profile
source ~/.profile

# Make the kernels
cd ./framework/kernel_firmfuzz
make ARCH=mips CROSS_COMPILE=mipseb-linux-musl- O=./build/mipseb -j8
make ARCH=mips CROSS_COMPILE=mipsel-linux-musl- O=./build/mipsel -j8
cd - && cd ./framework/kernel_firmfuzz_armel
make ARCH=arm CROSS_COMPILE=arm-linux-musleabi- O=./build/armel zImage -j8

