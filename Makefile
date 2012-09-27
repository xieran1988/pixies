
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

get-youku-m3u8:
	wget v.youku.com/player/getM3U8/vid/113618328/type/$p/ts/1348582854/v.m3u8

youku-hd2:
	make get-youku-m3u8 p=hd2
	make get-first-ts 

youku-mp4:
	make get-youku-m3u8 p=mp4
	make get-first-ts 

youku-flv:
	make get-youku-m3u8 p=flv
	make get-first-ts 

get-first-ts:
	wget -O a.ts "`cat v.m3u8 | grep http | head -1`"
	ffprobe a.ts

avpipe:
	$(CC) -o $@ avpipe.c


