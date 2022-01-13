#!/bin/bash

if [ $# -eq 0 ]; then
	echo share_wisdom.sh [wisDir]
	exit 0
fi

wisDir=$1
dst=deepsky.astro.umk.pl
#rsync -au wisdom/*.awpkl $dst
echo "put $wisDir/*.awpkl wisdom/data/" |sftp vlbeer@deepsky.astro.umk.pl

