#!/bin/bash

for f in `find sessions/ -name "*.wispkl*"`; do
    dst=`echo $f | tr '/' '-' | sed -e 's/logs//g' -e 's/sessions-//g' -e 's/-BLwisdom-//g' -e 's/.log//g' -e 's/wispkl_//g'`
    rsync -au $f ../antabML/data/train/$USER-$dst.awpkl
done
