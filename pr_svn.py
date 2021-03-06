#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import os.path
import tempfile
import datetime

from xml.dom import minidom

def log( path, revision=None, empty=True, multi=False, default='GENERAL' ):
	
	cmd = 'svn log %s -v --xml' % path
	
	if revision:
		cmd += ' -r %s' % revision
	
	temp, abspath = tempfile.mkstemp()
	file = os.fdopen( temp )
	file.close()
	
	os.system( '%s > %s' % ( cmd, abspath ) )
	
	return get_log( abspath, empty, multi, default )

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

def get_paths( logs, remove=['trunk'] ):
	
	added = []
	modified = []
	deleted = []
	
	for entry in logs:
		for p in entry['paths']:
			
			action = p[0]
			path   = p[1].strip('/')
			
			if remove:
				for r in remove:
					r = r.strip('/')
					if path.startswith( r ):
						path = path.replace( r, '' )
			
			path = path.strip('/')
			
			if path == '' or path == '/':
				continue
			
			if os.sep != '/':
				path = path.replace( '/',os.sep )
			
			if action == 'D':
				if path in added:
					added.remove( path )
				if path in modified:
					modified.remove( path )
				if path not in deleted:
					deleted.append( path )
			
			elif action == 'M':
				if path in deleted:
					deleted.remove( path )
				if path not in modified and path not in added:
					modified.append( path )
			
			elif action == 'A':
				if path in deleted:
					deleted.remove( path )
				if path not in added and path not in modified:
					added.append( path )
	
	added.sort()
	modified.sort()
	deleted.sort()
	
	return added, modified, deleted

def get_log( file, empty=True, multi=False, default='GENERAL' ):
	
	logs = []
	
	xmldoc = minidom.parse(file)
	data = xmldoc.toxml( 'utf-8' )
	xmldoc = minidom.parseString( data )
	
	for log in xmldoc.getElementsByTagName('logentry'):
		
		r = log.getAttribute('revision').encode('utf-8')
		m = ''
		
		try:
			m = log.getElementsByTagName('msg')[0].firstChild.nodeValue.encode('utf-8')
		except: pass
		
		m = m.strip()
		
		if not empty and len( m ) == 0:
			continue
		
		d = log.getElementsByTagName('date')[0].firstChild.nodeValue.encode('utf-8')
		d = d[0:10]
		
		dt = log.getElementsByTagName('date')[0].firstChild.nodeValue.encode('utf-8')
		dt = datetime.datetime( int(dt[0:4]), int(dt[5:7]), int(dt[8:10]), int(dt[11:13]), int(dt[14:16]), int(dt[17:19]) )
	
		a = log.getElementsByTagName('author')[0].firstChild.nodeValue.encode('utf-8')
		
		p = []
		for path in log.getElementsByTagName('path'):
			p.append( ( path.getAttribute('action').encode('utf-8'), path.firstChild.nodeValue.encode('utf-8') ) )
		
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
			
			logs.append( { 'revision': r, 'category': c, 'message': ml, 'date': d, 'datetime': dt, 'author': a, 'paths': p } )
	
	return logs
