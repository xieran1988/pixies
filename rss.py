#!/usr/bin/python

from bs4 import BeautifulSoup
import subprocess, sys, json, argparse, re, os
import urllib, time
import feedparser

def popen(args):
	p = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE)
	return p.communicate()[0]

proxy = '192.168.1.66:8888'

def curl_x(url):
	return [ '-x', proxy ] if need_proxy(url) else []

def curl(url):
	return popen(['curl', '-s', '-L'] + curl_x(url) + [url])

def curl_save(url, fname):
	return popen(['curl', '-#', '-o', fname] + curl_x(url) + [url])

def need_proxy(url):
	return 'youtube' in url;

def fetch(url):
	if url.startswith('http'):
		return curl(url)
	return open(url).read()

def parse_yt_rss(url):
	if not url.startswith('http') and not os.path.exists(url):
		url = 'http://www.youtube.com/rss/user/%s/video.rss' % url
	s = fetch(url)
	soup = BeautifulSoup(s)
#	print len(soup.select('item'))
	for i in soup.select('item'):
#		print i.guid.text
		vid = re.findall(r'video:(\S+)', i.guid.text)[0]
		u = "http://www.youtube.com/watch?v=" + vid
		vurl = parse_yt_page(u)
		print 'saving', vid
		curl_save(vurl, '%r.mp4' % vid)

'''
5:  { itag: 5 , quality:  1, description: getTrans("low")     , format: "FLV" , mres: { width:  400, height:  240 }, acodec: "MP3"   , vcodec: "SVQ"                          , arate: 22050, abr:  64000, vbr:  250000 },
18: { itag: 18, quality:  5, description: getTrans("high")    , format: "MP4" , mres: { width:  480, height:  360 }, acodec: "AAC"   , vcodec: "H.264" , vpro: "Baseline@L3.0", arate: 44100, abr:  96000, vbr:  500000 },
22: { itag: 22, quality:  8, description: getTrans("highdef") , format: "MP4" , mres: { width: 1280, height:  720 }, acodec: "AAC"   , vcodec: "H.264" , vpro: "High@L3.1"    , arate: 44100, abr: 152000, vbr: 2000000 },
34: { itag: 34, quality:  3, description: getTrans("lowdef")  , format: "FLV" , mres: { width:  640, height:  360 }, acodec: "AAC"   , vcodec: "H.264" , vpro: "Main@L3.0"    , arate: 44100, abr: 128000, vbr:  500000 },
35: { itag: 35, quality:  6, description: getTrans("stddef")  , format: "FLV" , mres: { width:  854, height:  480 }, acodec: "AAC"   , vcodec: "H.264" , vpro: "Main@L3.0"    , arate: 44100, abr: 128000, vbr:  800000 },
37: { itag: 37, quality:  9, description: getTrans("fhighdef"), format: "MP4" , mres: { width: 1920, height: 1080 }, acodec: "AAC"   , vcodec: "H.264" , vpro: "High@L4.0"    , arate: 44100, abr: 152000, vbr: 3500000 },
38: { itag: 38, quality: 10, description: getTrans("origdef") , format: "MP4" , mres: { width: 4096, height: 3072 }, acodec: "AAC"   , vcodec: "H.264" },
43: { itag: 43, quality:  2, description: getTrans("lowdef")  , format: "WebM", mres: { width:  640, height:  360 }, acodec: "Vorbis", vcodec: "VP8"                          , arate: 44100, abr: 128000, vbr:  500000 },
44: { itag: 44, quality:  4, description: getTrans("stddef")  , format: "WebM", mres: { width:  854, height:  480 }, acodec: "Vorbis", vcodec: "VP8"                          , arate: 44100, abr: 128000, vbr: 1000000 },
45: { itag: 45, quality:  7, description: getTrans("highdef") , format: "WebM", mres: { width: 1280, height:  720 }, acodec: "Vorbis", vcodec: "VP8"                          , arate: 44100, abr: 192000, vbr: 2000000 },
};
'''
def parse_yt_page(url):
	s = fetch(url)
	fv = re.findall(r'url_encoded_fmt_stream_map=([0-9A-Za-z\-%_\.]+)', s)[0]
	fv = urllib.unquote(fv)
	r = {}
	for v in fv.split(','):
		h = {}
		for ss in v.split('&'):
			a, b = ss.split('=')
			h[a] = b
		url = urllib.unquote(h['url'])
		r[h['itag']] = url + '&signature=' + h['sig']
	return r['34']

def parse_yk_rss(url):
#	d = feedparser.parse('yk.rss')
#	print d.entries[0].link
#	soup = BeautifulSoup(open('yk.rss').read())
	s = fetch(url)
	r = re.findall(r'id_([^_]+)', s)
	h = {}
	for i in r:
		h[i] = 1
	for i in h.keys():
		vid = parse_yk_page('http://v.youku.com/v_show/id_%s.html' % i)
		print 'saving', vid
		now = int(time.time())
		mu = 'http://v.youku.com/player/getM3U8/vid/%s/type/%s/ts/%d/v.m3u8' % (vid, 'flv', now)
		ts = filter(lambda x: x.startswith('http'), curl(mu).split('\n'))
		print 'n_ts', len(ts)
		fname = '%s.ts' % vid
		os.system(' > %s' % fname)
		for i in ts:
			print i
			os.system('curl -L "%s" -# >> %s' % (i, fname))

def parse_yk_page(url):
	#var videoId = '114934455';
	s = fetch(url)
	r = re.findall(r'videoId = \'(\d+)\'', s)[0]
	return r

url = sys.argv[1]
if 'youku' in url and 'rss' in url:
	print 'parse youku rss', url
	parse_yk_rss(url)

'''
if s == 'ytrss':
	parse_yt_rss(url)
elif s == 'ytpage':
	print parse_yt_page(url)
elif s == 'ykrss':
	parse_yk_rss(url)
elif s == 'ykpage':
	print parse_yk_page(url)
'''
