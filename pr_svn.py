#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import os.path
import tempfile

from xml.dom import minidom

def log( path, revision=None, multi=False, default='GENERAL' ):
	
	cmd = 'svn log %s -v --xml' % path
	
	if revision:
		cmd += ' -r %s' % revision
	
	temp = tempfile.NamedTemporaryFile()
	
	os.system( '%s > %s' % ( cmd, temp.name ) )
	
	return get_log( temp, multi, default )

def update( path, revision=None, quiet=True ):
	
	if not os.path.exists( path ):
		return False
	
	cmd = 'svn update %s' % path
	
	if revision:
		cmd += ' -r %s' % revision
	
	if quiet:
		cmd += ' -q'
	
	return os.system( cmd )

def export( path, destination, quiet=True ):
	
	if not os.path.exists( path ):
		return False
	
	if not os.path.exists( destination ):
		os.makedirs( destination )
	
	cmd = 'svn export %s %s --force' % ( path, destination )
	
	if quiet:
		cmd += ' -q'
	
	return os.system( cmd )

def get_paths( logs, remove='/trunk/' ):
	
	paths = []
	
	for entry in logs.values():
		for p in entry['paths']:
			
			action = p[0]
			path   = p[1]
			
			if remove:
				path = path.replace( remove, '' )
			
			if os.sep != '/':
				path = path.replace( '/',os.sep )
			
			if action == 'D':
				if path in paths:
					paths.remove( path )
			else:
				if path not in paths:
					paths.append( path )
	
	paths.sort()
	return paths

def get_log( file, multi=False, default='GENERAL' ):
	
	logs = []
	
	xmldoc = minidom.parse( file )

	for log in xmldoc.getElementsByTagName('logentry'):
		
		r = str( log.getAttribute('revision') )
		
		try:
			m = str( log.getElementsByTagName('msg')[0].firstChild.nodeValue )
		except: continue
		
		d = str( log.getElementsByTagName('date')[0].firstChild.nodeValue )
		d = d[0:10]
	
		a = str( log.getElementsByTagName('author')[0].firstChild.nodeValue )
		
		p = []
		for path in log.getElementsByTagName('path'):
			p.append( ( str( path.getAttribute('action') ), str( path.firstChild.nodeValue ) ) )
		
		c = default.upper()
		
		if not multi:
			mm = m.split('\n')
		else:
			mm = [ m ]
		
		for ml in mm:
			
			mp = ml.strip().split(':',1)
			if len( mp ) >= 2 and mp[0].upper() == mp[0]:
				c = mp[0]
			
			ml = ml.replace( c + ':', '' ).strip()
			c  = c.strip()
			
			logs.append( { 'revision': r, 'category': c, 'message': ml, 'date': d, 'author': a, 'paths': p } )
	
	return logs
