#!/bin/bash

set -e
set -u
source ./env_var.config 

while true
do
  SECONDS=0
  echo "Running firmware : terminating after 60 secs..."
  timeout --preserve-status --signal SIGINT 60 "${IMAGE_SCRIPTS}/run.${ARCH}_fs.sh" 

  if [ "$SECONDS" -eq 60 ]; then 
    echo "----Stable state reached, inferring network----"
    "${IMAGE_SCRIPTS}/makeNetwork_fs.py" -f "${IMAGE_DIR}/qemu.initial.serial.log" -q -o "${IMAGE_SCRIPTS}/run.sh" -a "${ARCH}" -q -d
    break
    
  else
    echo "SECONDS ELAPSED:$SECONDS" >> ~/seconds.txt
    echo "---Checking if panic occurred because of missing device---"
    grep -q "Woops" ${IMAGE_DIR}/qemu.initial.serial.log 

    echo "----Dev missing----"
    if [ "${ARCH}" = "mipseb" ] || [ "${ARCH}" = "mipsel" ]; then
      sudo python ${IMAGE_SCRIPTS}/mapper/parser.py ${IMAGE_DIR}/qemu.initial.serial.log ${MIPS_DEV}
    else
      sudo python ${IMAGE_SCRIPTS}/mapper/parser.py ${IMAGE_DIR}/qemu.initial.serial.log ${ARMEL_DEV}
    fi
    sleep 2

    echo "----Recreating device nodes----"
    sudo tar -czf dev.tgz -C workdir/ .
    sleep 2

    sudo rm -rf workdir/

    echo "---Recreating tarball----"
    sudo tar -xf dev.tgz -C $IMAGE_DIR/dev/
    sleep 2
    sync
    sleep 3

    echo "----Recreating kernel----"
    if [ "${ARCH}" != "armel" ]; then 

      cd ${KERNEL_DIR}/..

      if [ "${ARCH}" = "mipseb" ]; then 
        sudo env "PATH=$TEST_PATH" make ARCH=mips CROSS_COMPILE=mipseb-linux-musl- O=./build/mipseb -j8 
      elif [ "${ARCH}" = "mipsel" ]; then
        sudo env "PATH=$TEST_PATH" make ARCH=mips CROSS_COMPILE=mipsel-linux-musl- O=./build/mipsel -j8 
      else
        echo "${ARCH} architecture not supported, exiting..."
        exit 1
      fi

    else 
      
      cd ${KERNEL_DIR_ARMEL}/..
      sudo env "PATH=$TEST_PATH" make ARCH=arm CROSS_COMPILE=arm-linux-musleabi- O=./build/armel zImage -j8
    fi
    cd -

  fi
done
