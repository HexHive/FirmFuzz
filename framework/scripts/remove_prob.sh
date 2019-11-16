#!/bin/bash
for file in $1*
do
  mv -v -- "$file" $PROB_IMAGE
  break
done

