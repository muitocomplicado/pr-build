#!/usr/bin/env python
# encoding: utf-8

import sys
import getopt
import os
import time
import datetime
import tempfile
import re
from xml.sax import saxutils

import pr_svn

help_message = '''
Project Reality Mod Changelog Generator

Usage:

	python pr_changelog.py [args] [path|url]

Main options:
	
	-r --revision    revision range
	-t --today       current day of changes
	-y --yesterday   previous day of changes
	-w --week        last week of changes (doesn't include current day)

Examples:

	python pr_changelog.py -r 2334:2356
	python pr_changelog.py ./core --revision 2334:HEAD
	python pr_changelog.py --today
	python pr_changelog.py --yesterday
	python pr_changelog.py --revision {2008-04-25}:{2008-06-23}

Other options:
	
	-g --group       set the entries grouping (default date)
	                 other: category, author, none
	
	-o --output      set the output format (default text)
	                 other: bbcode, rss, test
	
	-n --name        name of changelog (default empty)
	-d --default     set the default category (GENERAL)
	-m --multi       group multiline entries
	-x --xxx         hide all comments with xxxx
	-f --fun         hide all comments except first and last letter of each word
	-p --paths       show modified paths (includes empty log messages)
	
	-v --verbose     run it verbosely
	-q --quiet       run it quietly
'''

options = {
	'path': '',
	'revision': None,
	'output': 'text',
	
	'group': 'date',
	'default': 'GENERAL',
	'name': '',
	
	'multi': None,
	'hide': None,
	'paths': None,
	
	'verbose': '',
	'quiet': ''
}

today = datetime.date.today()
today_rfc = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
yesterday = datetime.date.fromtimestamp(time.time()-60*60*24)
lastweek = datetime.date.fromtimestamp(time.time()-60*60*24*7)

class Usage(Exception):
	def __init__(self, msg):
		self.msg = msg

def main(argv=None):
	global options
	
	if argv is None:
		argv = sys.argv
	try:
		try:
			opts, args = getopt.getopt(argv[1:], 
				"hr:tywg:o:n:d:mxfpvq", 
				[ "help", "revision=", "today", "yesterday", "week", "group=",
					"output=", "name=", "default=", "multi", "xxx", "fun", "paths", "verbose", "quiet" ])
		except getopt.error, msg:
			raise Usage(msg)
		
		options['revision'] = '{"' + lastweek.isoformat() + 'T00:00Z"}:HEAD'
		
		for option, value in opts:
			
			if option in ("-h", "--help"):
				raise Usage(help_message)
			
			if option in ("-r", "--revision"):
				options['revision'] = value
			if option in ("-t", "--today"):
				options['revision'] = '{"' + today.isoformat() + 'T00:00Z"}:{"' + today.isoformat() + 'T23:59Z"}'
			if option in ("-y", "--yesterday"):
				options['revision'] = '{"' + yesterday.isoformat() + 'T00:00Z"}:{"' + yesterday.isoformat() + 'T23:59Z"}'
			if option in ("-w", "--week"):
				options['revision'] = '{"' + lastweek.isoformat() + 'T00:00Z"}:{"' + yesterday.isoformat() + 'T23:59Z"}'
			
			if option in ("-g", "--group") and value in ['date','category','author','none']:
				options['group'] = value
			
			if option in ("-o", "--output"):
				options['output'] = value
			
			if option in ("-n", "--name"):
				options['name'] = ' - %s' % value
			if option in ("-d", "--default"):
				options['default'] = value
			
			if option in ("-m", "--multi"):
				options['multi'] = True
			if option in ("-x", "--xxx"):
				options['hide'] = True
			if option in ("-f", "--fun"):
				options['hide'] = False
			if option in ("-p", "--paths"):
				options['paths'] = True
			
			if option in ("-v", "--verbose"):
				options['verbose'] = '-v'
			if option in ("-q", "--quiet"):
				options['quiet'] = '-q'
		
		try:
			options['path'] = args[0]
		except:
			raise Usage('Missing PATH or URL argument.')
		
		if options['output'] not in ['text', 'bbcode', 'rss', 'test']:
			raise Usage( 'Incorrect output format (text, bbcode, rss, test)' )
			
		logs = pr_svn.log( options['path'], options['revision'], options['paths'], options['multi'], options['default'] )
		
		if options['hide'] in [ True, False ]:
			logs = hide( logs, options['hide'] )
		
		header( options['path'], options['revision'], options['output'] )
		
		if options['group'] == 'none':
			by_none( logs, options['output'] )
		elif options['group'] == 'category':
			by_category( logs, options['output'] )
		elif options['group'] == 'author':
			by_author( logs, options['output'] )
		else:
			by_date( logs, options['output'] )
		
		footer( options['path'], options['revision'], options['output'] )
		
	except Usage, err:
		print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
		# print >> sys.stderr, "\t for help use --help"
		return 2


def header( path, revision, output='text' ):
	
	if output == 'rss':
		print '<?xml version="1.0"?>'
		print '<rss version="2.0">'
		print '<channel>'
		print '<title>Project Reality Mod Changelog%s</title>' % saxutils.escape(options['name'])
		print '<link>http://realitymod.com</link>'
		print '<description>Latest changelog information.</description>'
		print '<language>en-us</language>'
		print '<pubDate>%s</pubDate>' % today_rfc
		print '<lastBuildDate>%s</lastBuildDate>' % today_rfc
	
	if output == 'test':
		print '[QUOTE][B]How To Use This Test List:[/B]'
		print '[LIST]'
		print '[*] Please color code the results of the test according to the legend below'
		print '[*] Each item should be worked on individually, then once completed, moved to the appropriate section (GOOD TO GO or PROBLEMS).'
		print '[*] If a test item has any problems at all, it should stay in problems.'
		print '[*] If a test item still needs further testing it should stay in need to test.'
		print '[/LIST]\n'
		print '[B]Test Results Text Legend:[/B]'
		print '[COLOR=Green]Working Good[/COLOR]'
		print '[COLOR=Red]Problem[/COLOR]'
		print '[COLOR="RoyalBlue"]Fixed for next build[/COLOR][/QUOTE]\n'
		print '[SIZE=9]NEED TO TEST:[/SIZE]\n'
	
	if output == 'bbcode':
		print '[SIZE="6"]%s[/SIZE]\n' % revision
	
	if output == 'text':
		print '============================================================='
		print str( revision )
		print '=============================================================\n'

def footer( path, revision, output='text' ):
	
	if output == 'rss':
		print '</channel>'
		print '</rss>'
	if output in ['text','bbcode']:
		print '\n%s UTC\n' % datetime.datetime.utcnow()

def compare(a,b):
	return cmp( a, b )

def hide( logs, hide=None ):
	
	pn = re.compile('\d')
	if hide:
		p = re.compile('\S', re.MULTILINE)
	else:
		p = re.compile('\B.\B', re.MULTILINE)
	
	for key,entry in enumerate( logs ):
		entry['message'] = pn.sub( 'x', entry['message'] )
		entry['message'] = p.sub(  'x', entry['message'] )
		logs[key] = entry
	
	return logs

def by_none( logs, output='text' ):
	
	logs.reverse()
	
	entries = ''
	for entry in logs:
		
		if output == 'rss':
			txt  = '<item>\n'
			txt += '<title>%s</title>\n' % ( saxutils.escape(message( entry, output ).replace( '<br />\n', '' )) )
			txt += '<description></description>\n'
			txt += '<pubDate>%s</pubDate>\n' % ( entry['datetime'].strftime('%a, %d %b %Y %T') )
			txt += '<guid isPermalink="false">%s</guid>\n' % ( entry['revision'] )
			txt += '</item>\n'
		else:
			txt = message( entry, output )
			
		entries += txt
	
	print entries

def by_category( logs, output='text' ):
	
	logs_grouped = grouped( logs, 'category' )
	groups = logs_grouped.keys()
	groups.sort(compare)
	
	if len( groups ) == 0:
		return
	
	for g in groups:
	
		msg = category( g.upper(), output )
	
		entries = ''
		for entry in logs_grouped[g]:
			entries += message( entry, output )
	
		print msg % entries

def by_date( logs, output='text' ):
	
	logs_grouped = grouped( logs, 'date' )
	groups = logs_grouped.keys()
	groups.sort(compare)
	groups.reverse()
	
	if len( groups ) == 0:
		return
	
	groups.pop()
	
	for g in groups:
		
		date = datetime.date( int( g[0:4] ), int( g[5:7] ), int( g[8:10] ) )
		msg = category( date.strftime('%a, %d %b %Y'), output )
		
		entries = ''
		for entry in logs_grouped[g]:
			entries += message( entry, output )
		
		print msg % entries

def by_author( logs, output='text' ):
	
	logs_grouped = grouped( logs, 'author' )
	groups = logs_grouped.keys()
	groups.sort(compare)
	
	if len( groups ) == 0:
		return
	
	for g in groups:
		
		msg = category( g.upper(), output )
		
		entries = ''
		for entry in logs_grouped[g]:
			entries += message( entry, output )
		
		print msg % entries

def message( entry, output='text' ):
	
	if output == 'test' and entry['message']:
		txt = '[QUOTE]Test: %s (%s) %s[/QUOTE]\n\n' % ( entry['message'], entry['author'], entry['revision'] )
	
	if output in ['text','bbcode','rss']:
		if entry['message']:
			txt = '%s: %s (%s) %s\n' % ( entry['category'], entry['message'], entry['author'], entry['revision'] )
		else:
			txt = '---- (%s) %s\n' % ( entry['author'], entry['revision'] )
		
		if options['paths']:
			
			for path in entry['paths']:
				a,p = path
				if output == 'rss':
					prefix = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
				else:
					prefix = '     '
				txt += '%s%s %s\n' % ( prefix, a, p )
			txt += '\n'
	
	if output == 'rss':
		txt = txt.replace( '\n', '<br />\n' )
	
	return txt

def category( msg, output='text' ):
	
	if output == 'text':
	
		txt  = '\n-------------------------------------------------------------\n'
		txt += msg
		txt += '\n-------------------------------------------------------------\n\n'
		txt += '%s'
	
	if output in ['bbcode','test']:
		
		txt  = '\n[SIZE="4"]%s[/SIZE]\n\n' % msg
		txt += '%s'
	
	if output == 'rss':
		
		txt  = '<item>\n'
		txt += '<title>Changelog - %s%s</title>\n' % ( saxutils.escape(msg), saxutils.escape(options['name']) )
		txt += '<description><![CDATA[%s]]></description>\n'
		txt += '<pubDate>%s %s</pubDate>\n' % ( saxutils.escape(msg), '23:59:59 GMT' )
		txt += '<guid isPermalink="false">%s - %s</guid>\n' % ( saxutils.escape(options['path']), saxutils.escape(msg) )
		txt += '</item>\n'
	
	return txt

def grouped( logs, key='date' ):
	
	groups = {}
	for entry in logs:
		
		g = entry[key]
		if g not in groups:
			groups[g] = []
		
		groups[g].append( entry )
	
	return groups

if __name__ == "__main__":
	sys.exit(main())
