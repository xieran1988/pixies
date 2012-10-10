#!/bin/bash

((j=0))
 > $2
for i in `wget "$1" -O - | grep http`; do
#	echo $j
#	echo $i
	wget "$i" -O - >> $2
	((j++))
done
