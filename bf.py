#!/usr/bin/python

from bs4 import BeautifulSoup
import subprocess, sys, json, argparse, re
import urllib

convert_href = 0

def D(**kw):
	h = {}
	for k in kw: 
		if type(kw[k]) == unicode:
			v = kw[k]
			v = strip(v)
			if k == 'href' and convert_href:
				v = '?'+v[1:].replace('/', ',')
			if k == 'title':
				lim = 30
				if len(v) > lim:
					v = v[:lim] + ' ..'
			h[k] = v
		elif kw[k] and len(kw[k]) > 0:
			v = kw[k]
			h[k] = v
	return h

def U(**kw):
	return '?'+'&'.join([ '%s=%s'%(k,kw[k]) for k in kw ])

def js(h):
	return json.dumps(h)

def strip(s):
	return s.strip('\t\r\n ')

dbg = 0

def popen(cmd, args):
	p = subprocess.Popen([cmd, args], 
					shell=False, stdout=subprocess.PIPE)
	return p.communicate()[0]

def curl(s):
	if dbg == 1:
		print 'curl', s
	return popen('./curl-proxy', s)

def _get_title(soup):
	return D(title=soup.title.text[:-8])

def get_main_categories(soup):
	l = soup.select("#categories li a")
	r = []
	for a in l:
		h = a['href']
		r.append(D(href=h, title=a.text))
	return D(cat=r)

def get_categories_info(soup):
	if soup.select('a[name=videos]'):
		r = []
		for l in soup.select('section.block'):
			a = l.select('h2 var a')
			if a:
				a = a[0]
				title = a.parent.parent.text
				if not title.startswith('People'):
					b = l.select('ul#browse_list')[0]
					r.append(D(title=title, href=a['href'], box=ol_browse_list(b)))
		return D(catinfo=r)

def get_categories_right_bar(soup):
	b = []
	p = soup.find('ul', {'class':'pivots'})
	h4 = strip(p.parent.h4.text)
	if h4 != 'Browse this Category':
		return
	#.startswith('^Browe'):
	#	return 
	l = p.findAll('li')
	for i in l:
		h = i.a['href']
		b.append(D(href=h, title=i.a.strong.string))
	return D(catright=b)

def get_sort_bar(soup):
	l = soup.select('div#sort a')
	return D(sortbar=[ D(text=a.text, href=a['href']) \
					for a in l ])

def get_box12(soup):
	l = soup.select('div#browse_content')
	if l:
		return D(box12=ol_browse_list(l[0]))

def get_chan_tabs(soup):
	l = soup.select('div#tabs a')
	return D(chantabs=[ D(text=a['title'], href=a['href']) for a in l ])

def get_chan_clips(soup):
	l = soup.find('ol', {'id':'clips'})
	if l is None:
		return 
	l = l.findAll('li')
	r = []
	for i in l:
		img = i.find('div', {'data-thumb':True})['data-thumb']
		vid = i['id'][4:]
		plays = i.find('span', {'class':'plays'})
		likes = i.find('span', {'class':'likes'})
		comms = i.find('span', {'class':'comments'})
		meta = '%s %s %s' % (plays, likes, comms)
		r.append(D(href=vid, img=img, meta=meta))
	return D(chanclips=r)

def get_page_info(soup):
	p = page(soup)
	return D(page=p)

def get_header_title(soup):
	l = soup.select('header#page_header a')
	if l:
		return D(header=[ D(href=a['href'], text=a.text) for a in l ])

def _get_one(url):
	h = {}
	s = BeautifulSoup(curl(url))
	for f in globals():
		if f.startswith('get'):
			r = globals()[f](s)
			if r:
				h.update(r)
	return h

def _get_all():
	for url in testurls:
		print url
		print _get_one(url).keys()

def print_testurls():
	for f in globals():
		if f.startswith('curl_'):
			c = globals()[f]
			print "'%s'," % c.__doc__.split('\n')[1].strip()


def test_sub_func(func, url):
	print globals()[func](BeautifulSoup(curl(url)))

def curl_cat1():
	'''
	http://vimeo.com/categories/
	list:[href=xxxx|title=, ..]
	navbar:xxx / xx
	'''
	return cat1(curl('http://vimeo.com/categories/'))
def cat1(s):
	soup = BeautifulSoup(s)
	l = soup.select(".col_large li h2")
	a = []
	for i in l:
		if i.parent.name == 'a':
			h = i.parent['href']
			a.append(D(href=h, title=i.string))
	return {'list':a, 'navbar':cat_title(soup)}

def curl_cat2(t=('animation')):
	'''
  http://vimeo.com/categories/animation
	http://vimeo.com/categories/%s
	title:
	chan,video,group:{info{href,title},box:[{href,title,meta,img},..]}
	right:[{href,title}...]
	'''
	return cat2(curl('http://vimeo.com/categories/%s' % t))
def cat2(s):
	soup = BeautifulSoup(s)
	l = soup.select("h2 var a")
	a = []
	for i in l:
		a.append(D(href=i['href'], title=i.string))
	c = []
	l = soup.findAll('ul', {'id':'browse_list'})[:3]
	for i in l:
		c.append(ol_browse_list(i))
	return {
			'navbar':cat_title(soup),
			'video':{'info':a[0], 'box':c[0]}, 
			'chan':{'info':a[1], 'box':c[1]}, 
			'group':{'info':a[2], 'box':c[2]}, 
			'right':cat_right(soup),
			}

def curl_cat3(t=('animation', '3d')):
	'''
  http://vimeo.com/categories/animation/3d
	http://vimeo.com/categories/%s/%s
	title:
	chan,video,group:{info{href,title},box:[{href,title,meta,img},..]}
	cat:[{href,title}...]
	'''
	return cat2(curl('http://vimeo.com/categories/%s/%s' % t))

def page(soup):
	'''
	{r=pref,next,dots p=pageno}
	'''
	l = soup.find('div', {'class':'pagination'})
	if l is None:
		return
	l = l.findAll('li')
	p = []
	for li in l:
		if not li.a:
			p.append(D(type='dots'))
		else:
			a = li.a
			p.append(D(href=a['href'], text=a.text))
	return p

def parse_yt_rss():
	soup = BeautifulSoup(open('a.rss').read())
	print len(soup.select('item'))
	f = open('yt.vid', 'w+')
	for i in soup.select('item'):
		print i.guid.text
		vid = re.findall(r'video:(\S+)', i.guid.text)[0]
		f.write(vid + '\n')
	f.close()

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
def parse_yt_page():
	s = open('yt.page').read()
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
	print r['34']
	open('yt.url', 'w+').write(r['34'])

def curl_chans(t=('3', 'date')):
	'''
  http://vimeo.com/channels/page:3/sort:subscribers
	http://vimeo.com/channels/page:%s/sort:%s
  sort:date,videos,subscribers
	chans:[href|img|title|meta, ..]
	page:
	'''
	return chans(curl('http://vimeo.com/channels/page:%s/sort:%s' % t))
def chans(s):
	soup = BeautifulSoup(s)
	l = soup.findAll('div', {'class':'boxed'})
	a = []
	for i in l:
		href = i.find('a')['href']
		img = i.find('img')['src']
		title = i.select('.title')[0].string
		meta = i.select('.meta')[0].string
		a.append(D(href=href, img=img, title=title, meta=meta))
	return {'page':page(soup), 'chans':a}

def ol_browse_list(l):
	r = []
	l = l.select('li a')
	for a in l:
#		print '===='
#		print a
		m = a.select('p.meta')
		if m:
			meta = m[0].text 
			title = a['title'] if 'title' in a else \
					a.select('p.title')[0].text
			img = a.select('img')[0]['src']
			r.append(D(href=a['href'], title=title, meta=meta, img=img))
	return r

def box12(s):
	soup = BeautifulSoup(s)
	l = soup.find('ol', {'id':'browse_list'})
	return {'page':page(soup), 'box':ol_browse_list(l)}

def curl_chansdir(t=('4', 'date')):
	'''
  http://vimeo.com/channels/directory/page:4/sort:subscribers
	http://vimeo.com/channels/directory/page:%s/sort:%s
  sort:date,videos,subscribers
	box:[href|title|meta, ..]
	page:
	'''
	return chansdir(curl(
		'http://vimeo.com/channels/directory/page:%s/sort:%s' % t))
def chansdir(s):
	return box12(s)

def curl_chan(t=('channels/vimeohq', '5')):
	'''
  http://vimeo.com/channels/vimeohq/page:5
	http://vimeo.com/%s/page:%s
	chan:[{href|img|meta}, ..]
	page:
	'''
	return chan(curl('http://vimeo.com/%s/page:%s' % t))
def chan(s):
	soup = BeautifulSoup(s)
	l = soup.find('ol', {'id':'clips'})
	l = l.findAll('li')
	r = []
	for i in l:
		img = i.find('div', {'data-thumb':True})['data-thumb']
		vid = i['id'][4:]
		plays = i.find('span', {'class':'plays'})
		likes = i.find('span', {'class':'likes'})
		comms = i.find('span', {'class':'comments'})
		meta = '%s %s %s' % (plays, likes, comms)
		r.append(D(href=vid, img=img, meta=meta))
	return {'page':page(soup), 'chan':r}

def curl_catvideos(t=('categories/sports/videos', '7', 'relevant')):
	'''
  http://vimeo.com/categories/sports/videos/page:7/sort:relevant
	http://vimeo.com/%s/page:%s/sort:%s
  sort:relevant,date,plays,likes,comments,duration
	box:[{href|title|meta}, ..]
	cat:[{href|title}, ..]
	'''
	return box12(curl('http://vimeo.com/%s/page:%s/sort:%s' % t))

def curl_catchans(t=('categories/sports/channels', '6', 'subscribers')):
	'''
  http://vimeo.com/categories/sports/channels/page:6/sort:subscribers
	http://vimeo.com/%s/page:%s/sort:%s
  sort:date,videos,subscribers
	c=box|href|title|meta
	'''
	return box12(curl('http://vimeo.com/%s/page:%s/sort:%s' % t))

def curl_chanvideos(t=('channels/ski', '4', 'preset')):
	'''
  http://vimeo.com/channels/ski/videos/page:4/sort:preset
	http://vimeo.com/%s/videos/page:%s/sort:%s
  sort:preset,date,plays,likes,comments,duration
	c=box|href|title|meta
	'''
	return box12(curl('http://vimeo.com/%s/videos/page:%s/sort:%s' % t))

def curl_catgroups(t=('categories/technology/groups', '5', 'members')):
	'''
  http://vimeo.com/categories/technology/groups/page:5/sort:members
	http://vimeo.com/%s/page:%s/sort:%s
  sort:date,videos,members
	c=box|href|title|meta
	'''
	return box12(curl('http://vimeo.com/%s/page:%s/sort:%s' % t))

def curl_groupvideos(t=('groups/mwc', '6', 'plays')):
	'''
  http://vimeo.com/groups/mwc/page:6/sort:plays
	http://vimeo.com/%s/page:%s/sort:%s
  sort:relevant,date,plays,likes,comments,duration
	c=box|href|title|meta
	'''
	return box12(curl('http://vimeo.com/%s/page:%s/sort:%s' % t))

c = {
	'cat1':curl_cat1,
	'cat2':curl_cat2,
	'cat3':curl_cat3,
	'chans':curl_chans, # page sort
	'chansdir':curl_chansdir,
	'chan':curl_chan,
	'catvideos':curl_catvideos,
	'catchans':curl_catchans,
	'chanvideos':curl_chanvideos,
	'catgroups':curl_catgroups,
	'groupvideos':curl_groupvideos,
	}

testurls = [
'http://vimeo.com/categories/sports/channels/page:6/sort:subscribers',
'http://vimeo.com/categories/sports/videos/page:7/sort:relevant',
'http://vimeo.com/groups/mwc/page:6/sort:plays',
'http://vimeo.com/channels/ski/videos/page:4/sort:preset',
'http://vimeo.com/categories/',
'http://vimeo.com/categories/animation',
'http://vimeo.com/categories/animation/3d',
'http://vimeo.com/channels/vimeohq/page:5',
'http://vimeo.com/channels/directory/page:4/sort:subscribers',
'http://vimeo.com/categories/technology/groups/page:5/sort:members',
'http://vimeo.com/channels/page:3/sort:subscribers',
]



#dbg = 1
if len(sys.argv) == 1:
	for k in c:
		print k
else:
	s = sys.argv[1]
	if s == 'ytrss':
		parse_yt_rss()
	elif s == 'ytpage':
		parse_yt_page()
	elif s == 'mylike':
		for i in range(1, 9):
			box = box12(popen('./mylike', '%d'%i))
			for b in box['box']:
				print b['href'][1:], b['title']
				open('mylike.txt', 'a').write('%s %s')
	elif s == 'loc':
		box = box12(open(sys.argv[2]).read())
		for b in box['box']:
			print b['href'][1:], b['title']
	elif s == 'testurls':
		print_testurls()
	elif s == 'testurlsphp':
		for i in testurls:
			print i.replace('/', ',')
	elif s == 'getone':
		print js(_get_one(sys.argv[2]))
	elif s == 'php':
		url = sys.argv[2]
		convert_href = 1
		url = url.replace(',', '/')
		print js(_get_one('http://vimeo.com/' + url))
	elif s == 'sub':
		test_sub_func(sys.argv[2], sys.argv[3])
	elif s == 'getall':
		_get_all()
	elif s == 'all':
		for s in c:
			print s
			r = js(c[s]())
			print r
			open('%s.j'%s, 'w+').write(r)
	elif s in c:
		if len(sys.argv) == 2:
			r = js(c[s]())
			print r
			open('%s.j'%s, 'w+').write(r)
		elif sys.argv[2] == '-h':
			print c[s].__doc__
		else:
			dump(c[s](tuple(sys.argv[2:])))



