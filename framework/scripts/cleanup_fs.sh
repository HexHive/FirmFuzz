#!/bin/bash
source ./env_var.config
umount_image() {
  umount $1                                      
  kpartx -d "${IMAGE}"                                                            
  #losetup -d "$1" &>/dev/null                                              
  #dmsetup remove $(basename "$1") &>/dev/null
}
ROOT_DIR="$HOME"
HOME_DIR="$ROOT_DIR/firmfuzz"
KERNEL_DIR="$HOME_DIR/framework/kernel_firmfuzz/drivers/firmfuzz/"
KERNEL_DIR_ARMEL="$HOME_DIR/framework/kernel_firmfuzz_armel/drivers/firmfuzz/"

echo ">>Removing temp dev count files"
rm -f CurrDevNum.txt dev_stubs.txt

echo ">>Removing temp device directory"
sudo rm -rf workdir/

echo ">>Removing scratch directory with raw image"
umount_image /dev/mapper/loop0p1
sudo rm -rf $HOME_DIR/scratch

echo ">>Copying initial devfiles to kernel"
cp $HOME_DIR/framework/scripts/devfs_stubs_orig.c $KERNEL_DIR/devfs_stubs.c
cp $HOME_DIR/framework/scripts/devfs_stubs_orig.c $KERNEL_DIR_ARMEL/devfs_stubs.c

echo ">>Copying default device directory"
cp $HOME_DIR/framework/scripts/mapper/dev.tgz $HOME_DIR/framework/scripts/

echo ">>Remaking kernel"
cd $KERNEL_DIR/../../

if [ "$1" == "mipseb" ]; then 
  sudo env "PATH=$TEST_PATH" make ARCH=mips CROSS_COMPILE=mipseb-linux-musl- O=./build/mipseb/ -j8
elif [ "$1" == "mipsel" ]; then
  sudo env "PATH=$TEST_PATH" make ARCH=mips CROSS_COMPILE=mipsel-linux-musl- O=./build/mipsel/ -j8
elif [ "$1" == "armel" ]; then
  cd $KERNEL_DIR_ARMEL/../../
  sudo env "PATH=$TEST_PATH" make ARCH=arm CROSS_COMPILE=arm-linux-musleabi- O=./build/armel zImage -j8
else 
  sudo env "PATH=$TEST_PATH" make ARCH=mips CROSS_COMPILE=mipseb-linux-musl- O=./build/mipseb/ -j8
  sudo env "PATH=$TEST_PATH"  make ARCH=mips CROSS_COMPILE=mipsel-linux-musl- O=./build/mipsel/ -j8
  cd $KERNEL_DIR_ARMEL/../../
  sudo env "PATH=$TEST_PATH" make ARCH=arm CROSS_COMPILE=arm-linux-musleabi- O=./build/armel zImage -j8
fi

cd -

