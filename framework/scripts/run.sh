#!/bin/bash
source ./env_var.config
ARCH="mipseb"
set -u
IID=1

TAPDEV_0=tap${IID}_0
HOSTNETDEV_0=${TAPDEV_0}
echo "Creating TAP device ${TAPDEV_0}..."
sudo tunctl -t ${TAPDEV_0} -u ${USER}


echo "Bringing up TAP device..."
sudo ip link set ${HOSTNETDEV_0} up
sudo ip addr add 192.168.10.2/24 dev ${HOSTNETDEV_0}

echo "Adding route to 192.168.10.1..."
sudo ip route add 192.168.10.1 via 192.168.10.1 dev ${HOSTNETDEV_0}


function cleanup {
    pkill -P $$
    
echo "Deleting route..."
sudo ip route flush dev ${HOSTNETDEV_0}

echo "Bringing down TAP device..."
sudo ip link set ${TAPDEV_0} down


echo "Deleting TAP device ${TAPDEV_0}..."
sudo tunctl -d ${TAPDEV_0}

}

trap cleanup EXIT

echo "Starting firmware emulation... use Ctrl-a + x to exit"
sleep 1s

 qemu-system-mips -m 256 -M malta -kernel ${KERNEL_DIR}/${ARCH}/vmlinux \
     -drive if=ide,format=qcow2,file=image.qcow2 -append "root=/dev/sda1 console=ttyS0 nandsim.parts=64,64,64,64,64,64,64,64,64,64 rw debug ignore_loglevel print-fatal-signals=1 user_debug=31 firmadyne.syscall=0 rdinit=/firmadyne/preInit.sh" \
     -qmp tcp:localhost:3133,server,nowait -serial mon:stdio -nographic -no-reboot \
    -net nic,vlan=0 -net tap,vlan=0,id=net0,ifname=${TAPDEV_0},script=no -net nic,vlan=1 -net socket,vlan=1,listen=:2001 -net nic,vlan=2 -net socket,vlan=2,listen=:2002 -net nic,vlan=3 -net socket,vlan=3,listen=:2003 | tee qemu.final.serial.log
