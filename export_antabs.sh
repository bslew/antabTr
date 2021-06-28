#!/bin/bash

mkdir to_ftp
for p in `cat projects`; do
    export yy=`date +%y`
    for d in `cat EVNSchedule.txt | grep -i $p| tr '[]' ' ' | head -1 | tr -s ' '|awk -F' ' '{print $29}' | tr '()/' ' ' | awk '{print $3,$6}'| tr ' ' '\n'| uniq | awk ' BEGIN { yy=ENVIRON["yy"]};  { printf("%s-%s\n",$1,yy) }'`; do
	mkdir to_ftp/$d
	cp logs/"$p"tr.antabfs to_ftp/$d
	echo
    done
done

