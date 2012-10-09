#!/bin/bash

((j=0))
((lim=10))
for i in `find /root/vid -name '*.mp4'`; do
	echo $i $j
	nohup ./ffstream.sh $i $j &
	((j++))
	[ $j -eq $lim ] && break
done

