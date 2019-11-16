#!/bin/bash
source ./env_var.config
cp devfs_stubs.c $KERNEL_DIR_ARMEL/../drivers/firmfuzz/
cd $KERNEL_DIR_ARMEL/..
ARCH=$1
make ARCH=arm CROSS_COMPILE=arm-linux-musleabi- O=./build/armel zImage -j8
