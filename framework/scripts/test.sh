#!/bin/bash
source ./env_var.config
set -e
make_image() {
  
  mkdir -p $IMAGE_DIR
  mkdir -p $SCRATCH_DIR

  echo "----Copying Filesystem Tarball----"                                       
  mkdir -p "${SCRATCH_DIR}"                                                          
  chmod a+rwx "${SCRATCH_DIR}"                                                       
  chown -R "${USER}" "${SCRATCH_DIR}"                                                
  chgrp -R "${USER}" "${SCRATCH_DIR}"                                                
  cp $1 $SCRATCH_DIR/
  
  echo "----Creating QEMU Image----"                                              
  qemu-img create -f raw "${IMAGE}" 1G                                            
  chmod a+rw "${IMAGE}"                                                           
                                                                                  
  #-e enables interpretation of \n                                                
  echo "----Creating Partition Table----"                                         
  echo -e "o\nn\np\n1\n\n\nw" | /sbin/fdisk "${IMAGE}"                            
                                                                                  
  echo "----Mounting QEMU Image----"                                              
  kpartx_out="$(kpartx -a -s -v "${IMAGE}")"                                      
  echo $kpartx_out                                                                
  DEVICE="$(echo $kpartx_out | cut -d ' ' -f 3)"                                  
  DEVICE="/dev/mapper/$DEVICE"                                                    
  sleep 1                            
  
  echo "----Creating Filesystem----"                                              
  mkfs.ext2 "${DEVICE}"                                                           
  sync                                                                            
                                                                                  
  echo "----Making QEMU Image Mountpoint----"                                     
  if [ ! -e "${IMAGE_DIR}" ]; then                                                
      mkdir "${IMAGE_DIR}"                                                        
      chown "${USER}" "${IMAGE_DIR}"                                              
  fi                                                                              
                                                                                  
  echo "----Mounting QEMU Image Partition 1----"                                  
  mount "${DEVICE}" "${IMAGE_DIR}"                                                
                                                                                  
  echo "----Extracting Filesystem Tarball----"                                    
  tar -xf ${SCRATCH_DIR}/*.tar.gz -C "${IMAGE_DIR}"                             
  rm ${SCRATCH_DIR}/*.tar.gz                                                  
                                                                                  
  echo "----Creating FIRMADYNE Directories----"                                   
  mkdir "${IMAGE_DIR}/firmadyne/"                                                 
  mkdir "${IMAGE_DIR}/firmadyne/libnvram/"                                        
  mkdir "${IMAGE_DIR}/firmadyne/libnvram.override/"  
  
  echo "----Patching Filesystem (chroot)----"                                     
  cp $(which busybox) "${IMAGE_DIR}"                                              
  cp "${IMAGE_SCRIPTS}/fixImage.sh" "${IMAGE_DIR}"                                   
  cp "${IMAGE_SCRIPTS}/preInit.sh" "${IMAGE_DIR}/firmadyne/"                                   
  chmod a+x ${IMAGE_DIR}/firmadyne/preInit.sh
  chroot "${IMAGE_DIR}" /busybox ash /fixImage.sh                                 
  rm "${IMAGE_DIR}/fixImage.sh"                                                   
  rm "${IMAGE_DIR}/busybox"            

}

mount_image() {
  echo "----Mounting QEMU Image----"                                              
  kpartx_out="$(kpartx -a -s -v "${IMAGE}")"                                      
  echo $kpartx_out                                                                
  DEVICE="$(echo $kpartx_out | cut -d ' ' -f 3)"                                  
  export DEVICE="/dev/mapper/$DEVICE"                                                    
  sleep 1                            

  echo "----Mounting QEMU Image Partition 1----"                                  
  mount "${DEVICE}" "${IMAGE_DIR}"                                                
}


umount_image() {
  umount $1                                                         
  kpartx -d "${IMAGE}"                                                            
  #losetup -d "$1" &>/dev/null                                              
  #dmsetup remove $(basename "$1") &>/dev/null
}
