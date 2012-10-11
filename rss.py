#!/usr/bin/python

from bs4 import BeautifulSoup
import subprocess, sys, json, argparse, re, os
import urllib, time, hashlib
import feedparser

def popen(args):
	p = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE)
	return p.communicate()[0]

shortsha = lambda x: hashlib.sha1(x).hexdigest()[:7]

proxy = '192.168.1.66:8888'

def curl_x(url):
	return [ '-x', proxy ] if need_proxy(url) else []

def curl(url):
	return popen(['curl', '-s', '-L'] + curl_x(url) + [url])

def curl_save(url, fname):
	return popen(['curl', '-#', '-o', fname] + curl_x(url) + [url])

def need_proxy(url):
	return 'youtube' in url or 'vimeo' in url;

def fetch(url):
	if url.startswith('http'):
		return curl(url)
	return open(url).read()

import marshal

def L(sha):
	return marshal.load(open('pool/%s.m'%sha))

def S(sha, r):
	marshal.dump(r, open('pool/%s.m'%sha, 'wb+'))

import glob

def LS():
	items = {}
	rss = {}
	for i in glob.glob('pool/*.m'):
		sha = re.findall(r'/(\w+).m', i)[0]
		m = L(sha)
		m['img'] = i[:-2] + '.jpg'
		if not os.path.exists(m['img']):
			del m['img']
		items[sha] = m
		if m['rss'] not in rss:
			rss[m['rss']] = []
		rss[m['rss']].append(sha)
	return [items, rss, marshal.load(open('rssinfo.m'))]

def fetch_video_start(sha, rssurl, fname, title):
	if os.path.exists(fname):
		return False
	S(sha, {'title':title, 'rss':shortsha(rssurl), 'fname':fname, 'stat':'start'})
	return True

def fetch_video_end(sha):
	r = L(sha)
	r['stat'] = 'done'
	os.system('av/avin -p %s pool/%s.jpg' % (r['fname'], sha))
	S(sha, r)

def parse_youtube_rss(url):
	if not url.startswith('http') and not os.path.exists(url):
		url = 'http://www.youtube.com/rss/user/%s/video.rss' % url
	s = fetch(url)
	soup = BeautifulSoup(s)
#	print len(soup.select('item'))
	for i in soup.select('item'):
#		print i.guid.text
		vid = re.findall(r'video:(\S+)', i.guid.text)[0]
		u = "http://www.youtube.com/watch?v=" + vid
		vurl, title = parse_youtube_page(u)
		print 'saving', vid
		sha = shortsha(vid)
		fname = 'pool/%s.mp4' % sha
		if fetch_video_start(sha, url, fname, fname):
			curl_save(vurl, fname)
			fetch_video_end(sha)

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
def parse_youtube_page(url):
	s = fetch(url)
	open('yt.page', 'w+').write(s)
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
	title = meta_og_title(s)
	return r['34'], title

def grab_m3u8_ts(rssurl, url, vid, title):
	ts = filter(lambda x: x.startswith('http'), curl(url).split('\n'))
	print 'n_ts', len(ts)
	sha = shortsha(vid)
	fname = 'pool/%s.ts' % sha
	if fetch_video_start(sha, rssurl, fname, title):
		os.system(' > %s' % fname)
		for i in ts:
			if os.system('wget "%s" -O - >> %s' % (i, fname)) != 0:
				return 
		fetch_video_end(sha)

def parse_youku_rss(url):
#	d = feedparser.parse('youku.rss')
#	print d.entries[0].link
#	soup = BeautifulSoup(open('youku.rss').read())
	s = fetch(url)
	d = feedparser.parse(s)
	update_rss_info(url, d)
	r = re.findall(r'id_([^_]+)', s)
	h = {}
	for i in r:
		h[i] = 1
	for i in h.keys():
		u = 'http://v.youku.com/v_show/id_%s.html' % i
		print u
		vid, title = parse_youku_page(u)
#		print 'saving', vid
		now = int(time.time())
		mu = 'http://v.youku.com/player/getM3U8/vid/%s/type/%s/ts/%d/v.m3u8' % (vid, 'flv', now)
		grab_m3u8_ts(url, mu, vid, title)

def parse_youku_page(url):
	#var videoId = '114934455';
	s = fetch(url)
	open('yk.page', 'w+').write(s)
	title = meta_title(s)
	r = re.findall(r'videoId = \'(\d+)\'', s)[0]
	return r, title

def vimeo_page_url(vid):
	return 'http://vimeo.com/%s' % vid

def meta_title(s):
	soup = BeautifulSoup(s)
	t = soup.find(attrs={"name":"title"})
	return t['content']

def meta_og_title(s):
	soup = BeautifulSoup(s)
	t = soup.find(attrs={"property":"og:title"})
	return t['content']

def vimeo_video_title(url):
	s = fetch(url)
	return meta_og_title(s)

def fetch_vimeo_video(url, vid):
	sha = shortsha(vid)
	fname = 'pool/%s.mp4' % sha
	title = vimeo_video_title(vimeo_page_url(vid))
	if fetch_video_start(sha, url, fname, title):
		os.system('wget 106.187.99.71:8080/getvideo.pl?%s -O %s' % (vid, fname))
		fetch_video_end(sha)
	'''
	url = vimeo_page_url(vid)
	print url
	s = fetch(url)
#	open('v', 'w+').write(s)
	sig = re.findall(r'"signature":"(\w+)"', s)[0]
	ts = re.findall(r'"timestamp":(\d+)', s)[0]
	u = 'http://player.vimeo.com/play_redirect?quality=sd&codecs=h264&clip_id=%s&time=%s&sig=%s&type=html5_desktop_embed' \
				% (vid, ts, sig)
	print u
	curl_save(u, 'pool/%s.mp4' % vid)
	'''

def parse_vimeo_rss(url):
	s = fetch(url)
	open('vo.rss', 'w+').write(s)
	d = feedparser.parse(s)
	update_rss_info(url, d)
	for l in [re.findall('(\d+)$', e.link)[0] for e in d.entries]:
		print 'saving', l
		fetch_vimeo_video(url, l)

def update_rss_info(url, d):
	if not os.path.exists('rssinfo.m'):
		m = {}
	else:
		m = marshal.load(open('rssinfo.m'))
	if url in m:
		return 
	sha = shortsha(url)
	print 'update rss info', url, sha
	m[sha] = {'title':d.feed.title}
	marshal.dump(m, open('rssinfo.m', 'wb+'))

def call_cgi(args):
	if args[0] == 'ls':
		return LS()

if __name__ == '__main__':

	url = sys.argv[1]

	if url == 'genallpreview':
		r = LS()
		for k in r:
			v = r[k]
			os.system('av/avin -p %s %s' % (v['fname'], v['img']))

	if url == 'vimeo':
		fetch_vimeo_video('cmdline', sys.argv[2])

	if 'vimeo' in url and 'rss' not in url:
		print 'parse vimeo page'
		vimeo_video_title(url)

	if 'youtube' in url and 'rss' not in url:
		print 'parse youtube page'
		parse_youtube_page(url)

	if 'youku' in url and 'rss' in url:
		print 'parse youku rss', url
		parse_youku_rss(url)

	if 'youku' in url and 'rss' not in url:
		print 'parse youku page'
		parse_youku_page(url)

	if 'youtube' in url and 'rss' in url:
		print 'parse youtube rss', url
		parse_youtube_rss(url)

	if 'vimeo' in url and 'rss' in url:
		print 'parse vimeo rss', url
		parse_vimeo_rss(url)

	'''
	if s == 'youtuberss':
		parse_youtube_rss(url)
	elif s == 'youtubepage':
		print parse_youtube_page(url)
	elif s == 'youkurss':
		parse_youku_rss(url)
	elif s == 'youkupage':
		print parse_youku_page(url)
	'''
