#!/bin/bash

SCHED=$1
echo "exporting antabs"
echo "SCHED="$SCHED

mkdir to_ftp
for p in `cat logs/projects`; do
    echo "Processing project "$p
    export yy=`date +%y`
#    for d in `cat $SCHED | grep -i $p| tr '[]' ' ' | head -1 | tr -s ' '|sed 's/--(Km)--/-- Km --/g'|awk -F' ' '{print $29}' | tr '()/' ' ' | awk '{print $3,$6}'| tr ' ' '\n'| uniq | awk ' BEGIN { yy=ENVIRON["yy"]};  { printf("%s-%s\n",$1,yy) }'`; do
    for d in `cat $SCHED | grep -i $p| sed 's/.*(\([[:digit:]][[:digit:]]\)\/\([[:digit:]][[:digit:]]\)).*/\1 \2/g'| uniq| head -1 | awk ' function get_mon(m) { if (m==1) {return "jan"}; if (m==2) {return "feb"}; if (m==3) {return "mar"}; if (m==4) {return "apr"}; if (m==5) {return "may"}; if (m==6) {return "jun"}; if (m==7) {return "jul"}; if (m==8) {return "aug"};  if (m==9) {return "sep"}; if (m==10) {return "oct"}; if (m == 11) {return "nov"}; if (m==12) {return "dec"}; return "dupa"; } BEGIN { yy=ENVIRON["yy"]};  { printf("%s%s\n",get_mon(int($2)),yy) }'`; do
	mkdir to_ftp/$d
#	echo mkdir to_ftp/$d
	cp logs/"$p"tr.antabfs to_ftp/$d
	echo cp logs/"$p"tr.antabfs to_ftp/$d
	echo
    done
done 2> missing.antabs.raw > exported.antabs.raw

echo "Exported antabs" > summary.log
cat exported.antabs.raw | grep "^cp " | awk '{print $2}' >> summary.log
echo "" >> summary.log
echo "Missing antabs" >> summary.log
cat missing.antabs.raw | grep 'No such file or directory' | awk '{print $4}'| tr -d "':" >> summary.log
echo "" >> summary.log

cat summary.log
echo "summary file in "`pwd`"/summary.log"

