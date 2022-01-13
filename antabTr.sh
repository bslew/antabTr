#!/bin/bash
fname=$1
f=`basename $fname`
ext="${fname##*.}"
name="${f%.*}"

echo ${name%.*}

if [ ! -f $name.antabfs ]; then
    python ../../../antabfs_tassili.py $fname
else
    echo $name.antabfs already exists, skipping
fi
