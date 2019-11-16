#!/bin/bash
source ./env_var.config

if [ -z "$1" ]
then
    echo "Not being run in standalone mode"
else
  ARCH="$1"
fi

set -u
qemu-system-mips -m 256 -M malta -kernel ${KERNEL_DIR}/${ARCH}/vmlinux -drive if=ide,format=raw,file=${IMAGE} -append "rw debug ignore_loglevel print-fatal-signals=1 firmadyne.syscall=1 console=ttyS0 nandsim.parts=64,64,64,64,64,64,64,64,64,64 panic=1 rdinit=/firmadyne/preInit.sh root=/dev/sda1" -no-reboot -serial file:${IMAGE_DIR}/qemu.initial.serial.log -display none -net nic,vlan=0 -net socket,vlan=0,listen=:2000 -net nic,vlan=1 -net socket,vlan=1,listen=:2001 -net nic,vlan=2 -net socket,vlan=2,listen=:2002 -net nic,vlan=3 -net socket,vlan=3,listen=:2003
