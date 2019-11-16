#!/bin/bash
FILES=$1*
RAW_IMAGE_DIR=$1
mkdir -p ./prob/scratch_prob
mkdir -p ./scratch_unk
for f in $FILES
do
  #Checking if the directory is empty now
  num=$(ls $RAW_IMAGE_DIR | wc -l)
  if [ "$num" -eq 0 ]; then
    exit 1
  fi

  source makeImage_batch_fs.sh $f
  echo "REMOVING $f"
  rm $f
  ./cleanup_fs.sh $ARCH

done
