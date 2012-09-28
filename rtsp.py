#!/usr/bin/python

import socket, re
from gevent import *

HOST, PORT = "192.168.1.66", 554
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen(5)
ss, addr = s.accept()
print addr
#f = ss.makefile()
#l = f.readline()
buf = ss.recv(4096)
print buf
for l in buf.split('\n'):
	if l.startswith('CSeq'):
		r = re.match(r'^CSeq: (\d+)', l)
		cseq = r.groups(0)[0]
print cseq
ss.close()
s.shutdown(socket.SHUT_RDWR)
s.close()

