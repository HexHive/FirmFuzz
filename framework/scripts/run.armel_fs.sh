#!/bin/bash

source ./env_var.config

if [ -z "$1" ]
then
    echo "Not being run in standalone mode"
else
  ARCH="$1"
fi

QEMU_AUDIO_DRV=none qemu-system-arm -m 256 -M virt -display none -serial file:${IMAGE_DIR}/qemu.initial.serial.log -drive if=none,file=${IMAGE},format=raw,id=rootfs -device virtio-blk-device,drive=rootfs -kernel ${KERNEL_DIR_ARMEL}/${ARCH}/arch/arm/boot/zImage -append "root=/dev/vda1 console=ttyS0 rw debug ignore_loglevel print-fatal-signals=1 firmadyne.syscall=1 nandsim.parts=64,64,64,64,64,64,64,64,64,64 panic=1" -serial file:${IMAGE_DIR}/qemu.initial.serial.log -no-reboot -device virtio-net-device,netdev=net1 -netdev socket,listen=:2000,id=net1 -device virtio-net-device,netdev=net2 -netdev socket,listen=:2001,id=net2 -device virtio-net-device,netdev=net3 -netdev socket,listen=:2002,id=net3 -device virtio-net-device,netdev=net4 -netdev socket,listen=:2003,id=net4
