#!/bin/bash
fname=$1
f=`basename $fname`
ext="${fname##*.}"
name="${f%.*}"

echo ${name%.*}

if [ ! -f $name.antabfs ]; then
    antabTr.py $fname --clean rlm $2
else
    echo $name.antabfs already exists, skipping
fi
