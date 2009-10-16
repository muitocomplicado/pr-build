#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import os.path
import stat
import fnmatch

from time import sleep

def rename( source, destination, verbose=False ):
	
	if not os.path.exists( source ):
		return
	
	if verbose:
		print 'Renaming %s to %s' % ( source, destination )
	
	os.rename( source, destination )
	delay()
	# os.system( 'ren %s %s' % ( source, destination ) )

def paths( path, pattern='*', recursive=False, exclude=[] ):
	
	if not os.path.isdir( path ):
		return []
	
	# if '.*' not in exclude:
	# 	exclude.append( '.*' )

	list = []
	for root, dirs, files in os.walk( path ):
		
		if '.svn' in dirs:
			dirs.remove( '.svn' )
			
		for f in filtering( files, pattern, exclude ):
			list.append( os.path.join( root, f ) )
			
		for f in filtering( dirs, pattern, exclude ):
			list.append( os.path.join( root, f ) )
			
		if not recursive:
			break

	list.sort()
	return list

def filtering( list, pattern, exclude ):
	
	items = fnmatch.filter( list, pattern )
	
	remove = []
	for e in exclude:
		remove.extend( fnmatch.filter( items, e ) )
	for r in remove:
		items.remove( r )
	
	return items

def delete( path, pattern=None, recursive=False, exclude=[], verbose=False ):
	
	if not os.path.exists( path ):
		return
	
	if pattern:
		
		if verbose:
			print 'Deleting %s pattern %s recursive %s exclude %s' % ( path, pattern, recursive, exclude )
		
		for p in paths( path, pattern, recursive, exclude ):
			
			r = os.path.dirname( p )
			delete( p )
			
			if not os.path.exists( r ) or not recursive:
				continue
			
			if len( os.listdir( r ) ) == 0:
				os.rmdir( r )
		
	else: 
		
		if verbose:
			print 'Deleting %s' % path
		
		if os.path.isdir( path ):
			for root, dirs, files in os.walk(path, topdown=False):
				for name in files:
					os.chmod(os.path.join(root, name), stat.S_IWRITE)
					os.remove(os.path.join(root, name))
				for name in dirs:
					os.rmdir(os.path.join(root, name))
			os.rmdir(path)
			# os.system( 'rd /S %s %s' % ( q, path ) )
		else:
			os.chmod(path, stat.S_IWRITE)
			os.remove(path)
			# os.system( 'del /F %s %s %s' % ( q, r, path ) )
		
def copy( source, destination, verbose=False ):

	if not os.path.exists( source ):
		return
	
	if not os.path.exists( os.path.dirname( destination ) ):
		os.makedirs( os.path.dirname( destination ) )
	
	if not os.path.isdir( source ):
		
		if verbose:
			print 'Copying %s to %s' % ( source, destination )
		
		if os.name in ['posix','mac']:
			os.system( 'cp -f "%s" "%s"' % ( source, destination ) )
		else:
			os.system( 'copy "%s" "%s" /Y' % ( source, destination ) )
		return
	
	for root, dirs, files in os.walk( source ):
		
		if '.svn' in dirs:
			dirs.remove( '.svn' )
		
		pref = os.path.commonprefix( ( source, root ) )
		s = os.path.join( root )
		d = os.path.join( destination, root.replace( pref, '' ).strip(os.sep) )
		
		for name in files:
			copy( os.path.join( s, name ), os.path.join( d, name ), verbose )
		
		for name in dirs:
			if not os.path.exists( os.path.join( d, name ) ):
				
				if verbose:
					print 'Creating dir %s' % os.path.join( d, name )
				os.makedirs( os.path.join( d, name ) )

def merge( source, destination, verbose=False ):
	
	if not os.path.exists( source ):
		return
	
	if verbose:
		print 'Merging %s to %s' % ( source, destination )
	
	if os.name in ['posix','mac']:
		copy( source, destination, verbose )
	else:
		os.system( 'xcopy "%s" "%s" /E /Q /I /Y' % ( source, destination ) )

def delay():
	sleep(10)
