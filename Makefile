#
# 9.25: http realtime upload monitor
# 			using http://github.com/valums/file-uploader.git for client
# 			modifying connections.c in lighttpd to implement monitor
# 9.26: get m3u8 and ts file from youku, tudou
# 			https://github.com/zythum/youkuhtml5playerbookmark/
# 9.27: open .ts file demux and mux to .ts file
# 10.8: can create and live rmtp stream
# 10.10: 
# 		DONE: Get preview image from a file. list all I-frame in HTML and let somebody pick one
# 		DONE: Get preview image from a rtmp stream per n second.
# 		DONE: RSS parsing, using lib http://code.google.com/p/feedparser/downloads/detail?name=feedparser-5.1.2.tar.bz2&can=2&q=
# 		DONE: fetch RSS feed from youtube, youku
#
# 10.11:
# 		DONE: get preview images for each rss channel
#
# 		TODO: Live youtube/youku/vimeo/tudou channel
# 			DONE: youtube
#
# 		TODO: MYTV: 
# 			Video queues, each video assign with rss_id
# 			Realtime update css
# 			Collect user preference and push him good video
#
# 		TODO: Fix the rtmp BUG: push some frames before first I-frame to client flash player
# 		TODO: Fix the rtmp BUG: push some frames before first I-frame to client flash player
# 		TODO: Setup the env: Cairo mix with SDL with libav
# 		TODO: Make UT382 work in linux
# 		Use libav

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
	wget v.youku.com/player/getM3U8/vid/113618328/type/$p/ts/1348582854/v.m3u8 -O yk.m3u8
	
get-m3u8-save-ts:
	make get-youku-m3u8 p=flv
	./grab-m3u8.sh yk.m3u8 yk.ts

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
	wget -O a.ts "`cat yk.m3u8 | grep http | head -1`"
	ffprobe a.ts

avpipe:
	$(CC) -o $@ avpipe.c

vimeo-rss:
	./rss.py http://vimeo.com/channels/everythinganimated/videos/rss

vimeo-page:
	./rss.py vimeo 37929905

youtube-rss:
	curl -s -L -x 192.168.1.66:8888 "http://www.youtube.com/rss/user/ligue1fr/video.rss" > yt.rss

youtube-page:
	./rss.py http://www.youtube.com/watch?v=FNKD6UopafA

youku-rss:
	./rss.py http://www.youku.com/index/rss_hot_day_videos/duration/1

youku-page:
	./rss.py http://v.youku.com/v_show/id_XNDU5NzM3ODIw.html

parse-youku-page:
	./bf.py ykpage

get-youku-m3u8-byid:
	$c http://v.youku.com/player/getM3U8/vid/${id}/type/${type}/ts/$(shell date +%s)/v.m3u8 $p

youku-m3u8:
	make get-youku-m3u8-byid id=`./bf.py ykpage` type=hd2 c=wget p="-O yk.m3u8"

