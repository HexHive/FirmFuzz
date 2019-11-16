Introduction
============

This contains the modified ARM kernel for the FIRMADYNE framework, which
includes an in-tree `firmadyne` module to perform instrumentation and
emulation.

This module can be configured using the following parameters:

| Parameter | Default   | Values | Description |
| --------- | --------- | ------ | ----------- |
| devfs     | 1 (on)    | 0, 1   | Create stubs in devfs and emulate behavior |
| execute   | 1 (on)    | 0 - 5  | Counter to execute `/firmadyne/console` after 4th `execve()` syscall (requires syscall hooks), 0 to disable |
| reboot    | 1 (on)    | 0, 1   | Attempt to emulate system reboot by re-executing `/sbin/init` |
| procfs    | 1 (on)    | 0, 1   | Create stubs in procfs and emulate behavior |
| syscall   | 255 (all) | 0 - 16 | Output log bitmask for hooking system calls using the `kprobe` framework, 0 to disable |

Usage
=====

Create the kernel build output directory:

`mkdir -p build/armel`

Copy the configuration file into the build directory:

`cp config.armel build/armel/.config`

Assuming that the appropriate cross-compiler is installed in `/opt/cross/arm-linux-musleabi`, execute:

`make ARCH=arm CROSS_COMPILE=/opt/cross/arm-linux-musleabi/bin/arm-linux-musleabi- O=./build/armel zImage -j8`

The output kernel image will be generated at the following location:

`build/armel/arch/arm/boot/zImage`

Notes
=====

This instrumented ARM kernel is built for the `ARCH_VIRT` virtual machine
target, which uses [VirtIO](http://wiki.libvirt.org/page/Virtio) to
perform hardware virtualization. In conjunction with newer versions of QEMU,
this allows up to `NUM_VIRTIO_TRANSPORTS` (32) VirtIO transports to be attached
to the emulated machine, avoiding the PCI bus. This provides greater emulation
flexibility by supporting more virtualized block and network devices.

As a result, this kernel is much newer in order to fully support VirtIO
on ARM, which had previously been under development. However, this kernel
has not been fully tested across our entire dataset.

Although the ARM platform is bi-endian, currently upstream QEMU does not support
any emulated big-endian ARM targets. As future work, it may be useful to
investigate alternative forks of QEMU that do support big-endian ARM, such as
the [Xilinx fork](https://github.com/Xilinx/qemu) for BE8. Additionally, it may
be useful to add support for 64-bit ARM (AArch64) systems, which may grow
increasingly prevalent.

Pull requests are greatly appreciated!
