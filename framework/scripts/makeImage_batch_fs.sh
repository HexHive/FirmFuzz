#!/bin/bash
source ./env_var.config
source ./test.sh

sudo rm -rf $IMAGE_DIR
rm -f ~/research/IoT_Research/initramfs_data.cpio.gz
set -e #abort script at first error
set -u #Attempt to use undefined variable causes error

function cleanup {
  ./cleanup_fs.sh ${ARCH}
  ./remove_prob.sh $RAW_IMAGE_DIR
  ./run_batch_fs.sh $RAW_IMAGE_DIR
}


trap cleanup EXIT

mkdir -p $IMAGE_DIR
IMAGE_NAME=$(echo $1 | rev | cut -d"/" -f1 | rev | cut -d _ -f 1 | cut -d"." -f1)
echo ">> IMAGE BEING TESTED: $IMAGE_NAME"

make_image $1 

echo "----Checking arch of image/adding NVRAMlib----"
if sudo $IMAGE_SCRIPTS/getArch.sh $1 | grep -q 'mipseb'; then
  echo '>> MIPSEB ARCH DETECTED'
  export ARCH="mipseb"
  cp $IMAGE_LIB/libnvram.so.mipseb $IMAGE_DIR/firmadyne/libnvram.so
  chmod a+x $IMAGE_DIR/firmadyne/libnvram.so

  echo "---Adding poison CI files---"
  cp ./fuzzer/test_mipseb $IMAGE_DIR/test
  cp ./fuzzer/ci_file $IMAGE_DIR/


elif sudo $IMAGE_SCRIPTS/getArch.sh $1 | grep -q 'mipsel'; then
  echo '>> MIPSEL ARCH DETECTED'
  export ARCH="mipsel"
  cp $IMAGE_LIB/libnvram.so.mipsel $IMAGE_DIR/firmadyne/libnvram.so
  chmod a+x $IMAGE_DIR/firmadyne/libnvram.so

  echo "---Adding poison CI files---"
  cp ./fuzzer/test_mipsel $IMAGE_DIR/test
  cp ./fuzzer/ci_file $IMAGE_DIR/

elif sudo $IMAGE_SCRIPTS/getArch.sh $1 | grep -q 'armel'; then
  echo '>> ARMEL ARCH DETECTED'
  export ARCH="armel"
  cp $IMAGE_LIB/libnvram.so.armel $IMAGE_DIR/firmadyne/libnvram.so
  chmod a+x $IMAGE_DIR/firmadyne/libnvram.so

  echo "---Adding poison CI files---"
  cp ./fuzzer/test_armel $IMAGE_DIR/test
  cp ./fuzzer/ci_file $IMAGE_DIR/

else
  export ARCH=$(sudo $IMAGE_SCRIPTS/getArch.sh $1)
  echo 'Add nvram support for this arch'
  mv $1 ${IMAGE_NAME}_$ARCH.tar.gz
  mv ${IMAGE_NAME}_$ARCH.tar.gz $UNKNOWN_ARCH
  continue
fi

echo "---Removing reset-detect binary(WNAP320)---"
rm -f $IMAGE_DIR/usr/bin/reset_detect
sync
sleep 3

echo "---Inferring network for the image----"
$IMAGE_SCRIPTS/inferNetwork_fs.sh

echo "---Saving the stable snapshot of the image---"
mkdir -p $FINAL_IMAGE/$IMAGE_NAME 
umount_image $DEVICE
mv $IMAGE $FINAL_IMAGE/$IMAGE_NAME

cp $KERNEL_DIR/../drivers/firmfuzz/devfs_stubs.c $IMAGE_SCRIPTS/run.sh $IMAGE_SCRIPTS/env_var.config $FINAL_IMAGE/$IMAGE_NAME/

if [ "$ARCH" == "armel" ]; then
  cp remake_kernel_armel.sh $FINAL_IMAGE/$IMAGE_NAME/remake_kernel.sh
else
  cp remake_kernel.sh $FINAL_IMAGE/$IMAGE_NAME/
fi

echo "----Moving images to a scratch dir----"
mkdir -p $FINAL_IMAGE/scratch_fs
mv $FINAL_IMAGE/$IMAGE_NAME $FINAL_IMAGE/scratch_fs
