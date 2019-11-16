#!/bin/bash
source ./env_var.config
cp devfs_stubs.c $KERNEL_DIR/../drivers/firmfuzz/
cd $KERNEL_DIR/..
ARCH=$1
make ARCH=mips CROSS_COMPILE=$ARCH-linux-musl- O=./build/$ARCH -j8
