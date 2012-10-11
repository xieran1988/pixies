#!/usr/bin/python
# coding=utf-8

import cgi, sys, os
import cgitb, json
cgitb.enable(display=0, logdir="/tmp")

sys.path.append('.')
import rss

#print 'Content-type: text/json'
#print
r = rss.call_cgi(os.environ['QUERY_STRING'].split(','))
print json.dumps(r)

