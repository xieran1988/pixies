#!/bin/bash

while true; do
	avconv -loglevel verbose -re -i $1 -c:a copy -c:v copy -f flv rtmp://localhost/myapp/$2
	[ $? -ne 0 ] && exit
done
