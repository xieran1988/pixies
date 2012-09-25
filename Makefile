
# 9.25: http realtime upload monitor
# 			using http://github.com/valums/file-uploader.git for client
# 			modifying connections.c in lighttpd to implement monitor

lt := /root/xcache/lighttpd-1.4.31

all:
	make install -C ${lt}
	rm -rf /l/le
	/etc/init.d/lighttpd restart

taillog:
	tail /l/le

ls-cache:
	ls -l /var/cache/lighttpd/uploads/

sum-up:
	cat /l/le | grep -o "haha \([0-9]\+\)" | awk '{a+=$$2} END{print a}' 

