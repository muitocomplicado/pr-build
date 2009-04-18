#!/usr/bin/env python
# encoding: utf-8

import sys
import getopt
import os
import time
import datetime
import tempfile
import re

import pr_svn

help_message = '''
Project Reality Mod Changelog Generator

Usage:

	python pr_changelog.py [args] [path|url]

Main options:
	
	-r --revision    revision range
	-t --today       current day of changes
	-y --yesterday   previous day of changes
	-w --week        last week of changes (but not today)

Examples:

	python pr_changelog.py -r 2334:2356
	python pr_changelog.py ./core --revision 2334:HEAD
	python pr_changelog.py --today
	python pr_changelog.py --yesterday
	python pr_changelog.py --revision {2008-04-25}:{2008-06-23}

Other options:
	
	-c --category    group by category
	-a --author      group by author
	
	-o --output      set the output format (default text)
	                 other: bbcode, rss, test
	
	-d --default     set the default category (GENERAL)
	
	-m --multi       group multiline entries
	-x --xxx         hide all comments with xxxx
	-f --fun         hide all comments except first and last letter of each word
	
	-v --verbose     run it verbosely
	-q --quiet       run it quietly
'''

options = {
	'path': '',
	'revision': None,
	'output': 'text',
	
	'category': False,
	'author': False,
	'default': 'GENERAL',
	
	'multi': None,
	'hide': None,
	
	'verbose': '',
	'quiet': ''
}

today = datetime.date.today()
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
				"hr:tywcao:d:mxfvq", 
				[ "help", "revision=", "today", "yesterday", "week", "category", "author",
					"output=", "default=", "multi", "xxx", "fun", "verbose", "quiet" ])
		except getopt.error, msg:
			raise Usage(msg)
		
		try:
			options['path'] = args[0]
		except:
			raise Usage('Missing PATH or URL argument.')
		
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
			
			if option in ("-c", "--category"):
				options['category'] = True
			if option in ("-a", "--author"):
				options['author'] = True
			
			if option in ("-o", "--output"):
				options['output'] = value
			
			if option in ("-d", "--default"):
				options['default'] = value
			
			if option in ("-m", "--multi"):
				options['multi'] = True
			if option in ("-x", "--xxx"):
				options['hide'] = True
			if option in ("-f", "--fun"):
				options['hide'] = False
			
			if option in ("-v", "--verbose"):
				options['verbose'] = '-v'
			if option in ("-q", "--quiet"):
				options['quiet'] = '-q'
		
		if options['output'] not in ['text', 'bbcode', 'rss', 'test']:
			raise Usage( 'Incorrect output format (text, bbcode, rss, test)' )
			
		logs = pr_svn.log( options['path'], options['revision'], options['multi'], options['default'] )
		
		if options['hide'] in [ True, False ]:
			logs = hide( logs, options['hide'] )
		
		header( options['path'], options['revision'], options['output'] )
		
		if options['category']:
			by_category( logs, options['output'] )
		elif options['author']:
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
		print '<title>Project Reality Mod Changelog</title>'
		print '<link>http://realitymod.com</link>'
		print '<description>Latest changelog information.</description>'
		print '<language>en-us</language>'
	
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

def by_category( logs, output='text' ):
	
	for g,logs in grouped( logs, 'category' ).iteritems():
		msg = category( g.upper(), output )
		
		entries = ''
		for entry in logs:
			entries += message( entry, output )
		
		print msg % entries

def by_date( logs, output='text' ):
	
	logs_date = grouped( logs, 'date' )
	
	groups = logs_date.keys()
	groups.sort(compare)
	groups.reverse()
	groups.pop()
	
	for g in groups:
		
		date = datetime.date( int( g[0:4] ), int( g[5:7] ), int( g[8:10] ) )
		msg = category( date.strftime('%a, %d %B %Y'), output )
		
		entries = ''
		for entry in logs_date[g]:
			entries += message( entry, output )
		
		print msg % entries

def by_author( logs, output='text' ):
	
	for g,logs in grouped( logs, 'author' ).iteritems():
		msg = category( g.upper(), output )
		
		entries = ''
		for entry in logs:
			entries += message( entry, output )
		
		print msg % entries

def message( entry, output='text' ):
	
	if output == 'test':
		txt = '[QUOTE]Test: %s[/QUOTE]\n\n' % entry['message']
	
	if output in ['text','bbcode','rss']:
		txt = '%s: %s (%s) %s\n' % ( entry['category'], entry['message'], entry['author'], entry['revision'] )
	
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
		txt += '<title>Changelog - %s</title>\n' % msg
		txt += '<description><![CDATA[%s]]></description>\n'
		txt += '<guid isPermalink="false">%s</guid>\n' % msg
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
