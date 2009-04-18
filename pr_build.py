#!/usr/bin/env python
# encoding: utf-8

import sys
import getopt
import os
import os.path
import stat
import fnmatch
import compileall

from xml.dom import minidom

import pr_svn

help_message = '''
Project Reality Mod Build Generator

Usage:

	python pr_build.py [args]

Main options:

	-c --core       revisions separated by commas (no spaces)
	-l --levels     revisions separated by commas (no spaces)
	-n --number     version number (e.g. 0856)

Build options:

	-b --build      make a client build
	-s --server     make a server build
	-t --test       make a test build

Examples:

	python pr_build.py --core 2334,2356 --levels 456,488 --number 0856 --build --server
	python pr_build.py -c 2334 -l 456 -n 0856 --build --test

Other options:

	-k --skip       skip to the last patch (must have all other builds ready)

	-y --python     do not compile python
	-i --installer  do not create installers
	-u --update     do not update the repo
	-e --export     do not export the repo

	-v --verbose    run it verbosely
	-q --quiet      run it quietly
'''

core_path      = os.path.join( os.curdir, 'core' )
levels_path    = os.path.join( os.curdir, 'levels' )
installer_path = os.path.join( os.curdir, 'installer' )
builds_path    = os.path.join( os.curdir, 'builds' )
logs_path      = os.path.join( os.curdir, 'logs' )

core_build     = os.path.join( builds_path, 'core' )
levels_build   = os.path.join( builds_path, 'levels' )
server_build   = os.path.join( builds_path, 'server' )
patch_build    = os.path.join( builds_path, 'patch' )

core_build_patch   = os.path.join( builds_path, 'core_patch' )
levels_build_patch = os.path.join( builds_path, 'levels_patch' )

exec_7zip  = os.path.abspath( os.path.join( core_path, 'readme', 'assets', '7za.exe' ) )
exec_inno  = 'C:\\Program Files (x86)\\Inno Setup 5\\Compil32.exe'

core_installer_path   = os.path.join( installer_path, 'pr_core_base.iss' )
levels_installer_path = os.path.join( installer_path, 'pr_levels_base.iss' )
patch_installer_path  = os.path.join( installer_path, 'pr_patch_base.iss' )

filter_archives = {
	'objects/objects_client': '-xr!*.con -xr!*.tweak -xr!*.collisionmesh'
}

archives_con = {
	'client': 'clientarchives.con',
	'server': 'serverarchives.con'
}

core_archives = {
	'client': {
		'common_client': 'Common', 
		'menu/fonts_client': 'Menu', 
		'menu/menu_client': 'Menu',
		'objects/objects_client': 'Objects',
		'shaders_client': 'Shaders'
	},
	'server': { 
		'common_server': 'Common',
		'menu/menu_server': 'Menu', 
		'objects/objects_server': 'Objects',
	}
}

options = {
	'core': None,
	'levels': None,
	'number': '',
	'patch': None, # internal
	
	'build': False,
	'server': False,
	'test': False,
	'skip': False,
	
	'python': True,
	'installer': True,
	'update': True,
	'export': True,
	
	'verbose': '',
	'quiet': ''
}


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
				"hc:l:n:bstkyiuevq", 
				[ "help", "core=", "levels=", "number=", "build", "server", "test", "skip", 
					"python", "installer", "update", "export", "verbose", "quiet" ])
		except getopt.error, msg:
			raise Usage(msg)
		
		for option, value in opts:
			
			if option in ("-h", "--help"):
				raise Usage(help_message)
			
			if option in ("-c", "--core"):
				options['core'] = value.split(',')
			if option in ("-l", "--levels"):
				options['levels'] = value.split(',')
			if option in ("-n", "--number"):
				options['number'] = value
			
			if option in ("-b", "--build"):
				options['build'] = True
			if option in ("-s", "--server"):
				options['server'] = True
			if option in ("-t", "--test"):
				options['test'] = True
			if option in ("-k", "--skip"):
				options['skip'] = True
			
			if option in ("-y", "--python"):
				options['python'] = False
			if option in ("-i", "--installer"):
				options['installer'] = False
			if option in ("-u", "--update"):
				options['update'] = False
			if option in ("-e", "--export"):
				options['export'] = False
			
			if option in ("-v", "--verbose"):
				options['verbose'] = '-v'
			if option in ("-q", "--quiet"):
				options['quiet'] = '-q'
		
		if not options['verbose']:
			options['quiet'] = '-q'
		
		if not options['core'] or not options['levels'] or not options['number']:
			raise Usage('Missing required arguments')
		
		if len( options['core'] ) != len( options['levels'] ):
			raise Usage('Number of revisions is different between core and levels')
		
		for r in ['core','levels']:
			last_rev = 0
			for rev in options[r]:
				if last_rev >= rev:
					raise Usage('%s revision %s is smaller than the previous revision %s' % ( r, rev, last_rev ) )
		
		if options['build']:
			
			if options['skip']:
				
				verbose( 'SKIP BUILD' )
				
				patch = len( options['core'] )-1
				
				for p in range( 0, patch ):
					if not os.path.exists( path_core_build( p ) ):
						raise Usage('Missing core build %s' % path_core_build( p ) )
					if not os.path.exists( path_levels_build( p ) ):
						raise Usage('Missing levels build %s' % path_levels_build( p ) )
				
				options['patch'] = patch
				build_client( patch )
				
			else:
				
				verbose( 'FULL BUILD' )
				for patch in range( 0, len( options['core'] ) ):
					options['patch'] = patch
					build_client( patch )
			
			if options['python']:
				build_python( options['patch'] )
		
			if options['patch']:
				build_patch( options['patch'] )
		
		if options['server']:
			build_server( options['patch'] )
		
		if options['installer']:
			if options['build']:
				patch_installer( options['number'], options['test'] )
				if not options['skip']:
					core_installer( options['number'], options['test'] )
					levels_installer( options['number'], options['test'] )
			if options['server']:
				server_installer( options['number'], options['test'] )
	
	except Usage, err:
		print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
		# print >> sys.stderr, "\t for help use --help"
		return 2


def build_client( patch ):
	
	verbose( 'CLIENT BUILD %s' % patch )
	
	core_revision   = options['core'][patch]
	levels_revision = options['levels'][patch]
	
	cb = path_core_build( patch )
	lb = path_levels_build( patch )
	
	if not patch:
		sufix = ''
	else:
		sufix = '_patch%s' % patch
	
	if options['update']:
		verbose( 'REPO UPDATE %s' % patch )
		
		update_repo( core_path, core_revision )
		update_repo( levels_path, levels_revision )
	
	if options['export']:
		verbose( 'REPO EXPORT %s' % patch )
		
		delete( cb )
		delete( lb )
		
		if not patch:
			
			export_repo( core_path, cb )
			export_repo( levels_path, lb )
		
		else:
			
			core_lrevision   = int( options['core'][patch-1] )+1
			levels_lrevision = int( options['levels'][patch-1] )+1
			
			core_log   = log_repo( core_path,   core_lrevision,   core_revision )
			levels_log = log_repo( levels_path, levels_lrevision, levels_revision )
			
			for path in paths_repo( core_log, patch, '/trunk/' ):
				copy( os.path.join( core_path, path ), os.path.join( cb, path ) )
			
			for path in paths_repo( levels_log, patch, '/levels/' ):
				copy( os.path.join( levels_path, path), os.path.join( lb, path ) )
			
			update_archives( patch )
	
	verbose( 'ARCHIVE %s' % patch )
	
	build_archives( cb, core_archives['server'], sufix )
	build_archives( cb, core_archives['client'], sufix )
	copy( os.path.join( cb, 'shaders_client%s.zip' % sufix ), 
				os.path.join( cb, 'shaders_client_pr%s.zip' % sufix ) )
	copy( os.path.join( cb, 'shaders_client%s.zip' % sufix ), 
				os.path.join( cb, 'shaders_night_client_%s.zip' % sufix ) )
	
	verbose( 'CLEANUP %s' % patch )
	
	clean_archives( cb, core_archives['server'] )
	clean_archives( cb, core_archives['client'] )
	delete( os.path.join( cb, 'build_pr_new.bat' ) )
	delete( os.path.join( cb, 'readme', 'assets' ) )
	delete( cb, 'bst*.md5' )
	delete( lb, 'assets', True )
	delete( lb, 'server', True )
	
	# rename( os.path.join( cb, 'settings', 'usersettings.con' ), os.path.join( cb, 'settings', 'prserverusersettings.con' ) )
	
	if patch:
		verbose( 'MERGE PATCH %s' % patch )
		
		merge( cb, core_build )
		merge( lb, levels_build )

def build_python( patch ):
	
	verbose( 'PYTHON BUILD %s' % patch )
	
	delete( os.path.join( core_build, 'python', 'game' ) )
	export_repo( os.path.join( core_path, 'python', 'game' ), os.path.join( core_build, 'python', 'game' ) )
	compile_python( os.path.join( core_build, 'python', 'game' ) )
	clean_python( os.path.join( core_build, 'python' ) )
	
	if patch:
		delete( os.path.join( path_core_build( patch ), 'python', 'game' ) )
		copy( os.path.join( core_build, 'python', 'game' ), os.path.join( path_core_build( patch ), 'python', 'game' ) )

def build_patch( patch ):
	
	verbose( 'PATCH BUILD %s' % patch )
	
	delete( patch_build )
	merge( path_core_build( patch ),   patch_build )
	merge( path_levels_build( patch ), os.path.join( patch_build, 'levels' ) )

def build_server( patch ):
	
	verbose( 'SERVER BUILD %s' % patch )
	
	delete( server_build )
	merge( core_build, server_build )
	merge( levels_build, os.path.join( server_build, 'levels' ) )
	
	verbose( 'SERVER CLEANUP' )

	delete( os.path.join( server_build, 'levels' ), '*client.zip', True )
	delete( os.path.join( server_build, 'levels' ), '*.png', True )

	for p,o in core_archives['client'].iteritems():
		delete( os.path.join( server_build, '%s.zip' % p.replace('/',os.sep) ) )
		for i in range( 1, patch+1 ):
			delete( os.path.join( server_build, '%s_patch%s.zip' % ( p.replace('/',os.sep), i ) ) )
	
	delete( os.path.join( server_build, 'shaders_client_pr.zip' ) )
	delete( os.path.join( server_build, 'shaders_night_client.zip' ) )
	
	for i in range( 1, patch+1 ):
		delete( os.path.join( server_build, 'shaders_client_pr_patch%s.zip' % i ) )
		delete( os.path.join( server_build, 'shaders_night_client_patch%s.zip' % i ) )
	
	delete( os.path.join( server_build, archives_con['client'] ) )
	delete( os.path.join( server_build, 'menu', 'external' ) )
	delete( os.path.join( server_build, 'readme', 'bf2editor' ) )
	delete( os.path.join( server_build, 'readme' ), '*.txt', False, ['license.txt'] )
	delete( os.path.join( server_build, 'readme' ), '*.pdf' )
	delete( os.path.join( server_build, 'movies' ) )
	
	# rename( os.path.join( server_build, 'settings', 'prserverusersettings.con' ), os.path.join( server_build, 'settings', 'usersettings.con' ) )
	# os.chmod( os.path.join( server_build, 'settings', 'usersettings.con' ), stat.S_IREAD )
	
def server_installer( number, test ):
	
	verbose( 'SERVER INSTALLER %s TEST %s' % ( number, test ) )
	
	if test:
		server_build_renamed = os.path.join( builds_path, 'pr_%s' % number )
	else:
		server_build_renamed = os.path.join( builds_path, 'pr' )
	
	filename = os.path.join( builds_path, 'pr_%s_server.zip' % number )
	
	rename( server_build, server_build_renamed )
	delete( filename )
	zip( server_build_renamed, filename, '', True )
	rename( server_build_renamed, server_build )

def core_installer( number, test ):
	
	verbose( 'CORE INSTALLER %s TEST %s' % ( number, test ) )
	client_installer( 'core', core_installer_path, number, test )
	
def levels_installer( number, test ):
	
	verbose( 'LEVELS INSTALLER %s TEST %s' % ( number, test ) )
	client_installer( 'levels', levels_installer_path, number, test )

def patch_installer( number, test ):
	
	verbose( 'PATCH INSTALLER %s TEST %s' % ( number, test ) )
	client_installer( 'patch', patch_installer_path, number, test )

def client_installer( type, script, number, test ):
	
	verbose( 'Running %s installer %s' % ( type, script ), False )
	
	final = script.replace( '_base', '' )
	
	b = open( script, 'r' )
	f = open( final,  'w' )
	
	for line in b:
		
		if not test:
			line = line.replace( '_version_number', '' )
		line = line.replace( 'version_number', number )
		
		f.write( line )
	
	b.close()
	f.close()
	
	if os.path.exists( exec_inno ):
		os.spawnl(os.P_WAIT, exec_inno, os.path.basename( exec_inno ), '/cc', final)
		
		output   = os.path.join( installer_path, 'Output', 'setup.exe' )
		filename = os.path.join( builds_path, 'pr_%s_%s_setup.exe' % ( number, type ) )
		
		delete( filename )
		copy( output, filename )
		delete( output )

def path_core_build( patch ):
	if patch:
		return core_build_patch + '%s' % patch
	else:
		return core_build

def path_levels_build( patch ):
	if patch:
		return levels_build_patch + '%s' % patch
	else:
		return levels_build

def update_repo( path, revision ):
	
	verbose( 'Updating %s to revision %s' % ( path, revision ), False )
	pr_svn.update( path, revision, options['quiet'] )

def export_repo( path, destination ):
	
	verbose( 'Exporting %s to %s' % ( path, destination ), False )
	pr_svn.export( path, destination, options['quiet'] )

def log_repo( path, start, end ):
	
	if start:
		revision = '%s:%s' % ( start, end )
	else:
		revision = end
	
	verbose( 'Log %s revision %s' % ( path, revision ), False )
	
	return pr_svn.log( path, revision, True )

def paths_repo( log, patch, remove='/trunk/' ):
	return pr_svn.get_paths( log, remove )

def build_archives( path, archives, sufix='' ):
	
	for p,o in archives.iteritems():
		
		dir  = os.path.join( path, '%s-zip'   % ( p.replace('/',os.sep) ) )
		file = os.path.join( path, '%s%s.zip' % ( p.replace('/',os.sep), sufix ) )
		
		verbose( 'Building archive %s from %s' % ( file, dir ), False )
		
		if os.path.exists( file ):
			delete( file )
		
		if p not in filter_archives:
			zip( dir, file )
		else:
			zip( dir, file, filter_archives[p] )

def compile_python( path ):
	
	verbose( 'Compiling python', False )
	compileall.compile_dir( path, 1, quiet=options['quiet'] )

def clean_python( path ):
	
	verbose( 'Cleaning python %s' % path, False )
	
	delete( path, 'assets', True )
	delete( path, 'compiled', True )
	delete( path, 'debug', True )
	
	game = os.path.join( path, 'game' )
	delete( game, '*.py', True, [ '__init__.py', 'gpm_*.py', 'realityconfig_common.py', 'realityconfig_local.py', 'realityconfig_private.py' ] )
	delete( game, 'gpm_*.pyc', True )
	delete( game, 'realityconfig_*.pyc', True, [ 'realityconfig_public.pyc' ] )
	delete( game, '__init__.pyc', True )

def clean_archives( path, archives ):
	
	for p,o in archives.iteritems():
		dir = os.path.join( path, '%s-zip' % p.replace('/',os.sep) )
		
		verbose( 'Cleaning archive folder %s' % dir, False )
		delete( dir )

def update_archives( patch ):
	
	for type,filecon in archives_con.iteritems():
		
		filename = os.path.join( path_core_build( patch ), filecon )
		
		if not os.path.exists( filename ):
			copy( os.path.join( core_path, filecon ), filename )
		
		archive_content = ''
		patch_replacer  = 'rem patch'
		
		f = open( os.path.join( core_build, filecon ), 'r' )
		for line in f:
			archive_content += line
		f.close()
		
		for i in range( 1, patch+1 ):
			if archive_content.find( '_patch%s' % i ) != -1:
				continue
			
			patch_content = ''
			for p,o in core_archives[type].iteritems():
				ps = os.path.join( path_core_build( i ), p.replace('/',os.sep) )
				
				if os.path.exists( '%s-zip' % ps ) or os.path.exists( '%s_patch%s.zip' % ( ps, i ) ):
					verbose( 'Updating %s to mount %s_patch%s.zip' % ( filecon, p, i ), False )
					patch_content += 'fileManager.mountArchive %s_patch%s.zip %s\n' % ( p, i, o )
			
			if archive_content.find( patch_replacer ) != -1:
				archive_content = archive_content.replace( patch_replacer, patch_replacer + '\n' + patch_content )
			else:
				archive_content = patch_content + archive_content
		
		g = open( filename, 'w' )
		g.write( archive_content )
		g.close()

def verbose( text, prefix=True ):
	if options['verbose']:
		if prefix:
			print '--- ' + text
		else:
			print text

def rename( source, destination ):
	
	if not os.path.exists( source ):
		return
		
	verbose( 'Renaming %s to %s' % ( source, destination ), False )
	os.rename( source, destination )
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
			
		for f in filter( files, pattern, exclude ):
			list.append( os.path.join( root, f ) )
			
		for f in filter( dirs, pattern, exclude ):
			list.append( os.path.join( root, f ) )
			
		if not recursive:
			break

	list.sort()
	return list

def filter( list, pattern, exclude ):
	
	items = fnmatch.filter( list, pattern )
	
	remove = []
	for e in exclude:
		remove.extend( fnmatch.filter( items, e ) )
	for r in remove:
		items.remove( r )
	
	return items

def delete( path, pattern=None, recursive=False, exclude=[] ):
	
	if not os.path.exists( path ):
		return
	
	if pattern:
		
		verbose( 'Deleting %s pattern %s recursive %s exclude %s' % ( path, pattern, recursive, exclude ), False )
		
		for p in paths( path, pattern, recursive, exclude ):
			delete( p )
		
	else: 
		
		verbose( 'Deleting %s' % path, False )
		
		if os.path.isdir( path ):
			for root, dirs, files in os.walk(path, topdown=False):
				for name in files:
					os.remove(os.path.join(root, name))
				for name in dirs:
					os.rmdir(os.path.join(root, name))
			os.rmdir( path )
			# os.system( 'rd /S %s %s' % ( q, path ) )
		else:
			os.remove( path )
			# os.system( 'del /F %s %s %s' % ( q, r, path ) )
		
def zip( source, destination, filters='', folder=False ):
	
	if not os.path.exists( source ):
		return
	
	verbose( 'Archiving %s to %s' % ( source, destination ), False )
	
	root = os.getcwd()
	
	if folder:
		os.chdir( os.path.join( source, '..' + os.sep ) )
		d = os.path.basename( destination )
		s = os.path.basename( source )
	else:
		os.chdir( os.path.join( source ) )
		d = os.path.join( '..', os.path.basename( destination ) )
		s = '*'
	
	if os.name in ['posix','mac']:
		os.system( 'zip -r %s %s %s -x \*/assets/\* -x \*/.*' % ( options['quiet'], d, s ) ) 
	else:
		os.system( '"%s" a -tzip %s %s %s -xr!.svn\\ -xr!Assets\\ -xr!assets\\ -xr!*.db -xr!*.samp* -xr!*.max -xr!*.3ds -xr!*.psd -xr!samples.tga -xr!uvs.tga' % ( exec_7zip, d, s, filters ) )
	
	os.chdir( root )

def copy( source, destination ):

	if not os.path.exists( source ):
		return
	
	if not os.path.exists( os.path.dirname( destination ) ):
		os.makedirs( os.path.dirname( destination ) )
	
	if not os.path.isdir( source ):
		verbose( 'Copying %s to %s' % ( source, destination ), False )
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
			copy( os.path.join( s, name ), os.path.join( d, name ) )
		
		for name in dirs:
			if not os.path.exists( os.path.join( d, name ) ):
				verbose( 'Creating dir %s' % os.path.join( d, name ), False )
				os.makedirs( os.path.join( d, name ) )

def merge( source, destination ):
	
	if not os.path.exists( source ):
		return
	
	verbose( 'Merging %s to %s' % ( source, destination ), False )
	
	if os.name in ['posix','mac']:
		copy( source, destination )
	else:
		os.system( 'xcopy "%s" "%s" /E /Q /I /Y' % ( source, destination ) )


if __name__ == "__main__":
	sys.exit(main())
