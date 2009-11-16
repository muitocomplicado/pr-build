#!/usr/bin/env python
# encoding: utf-8

import sys
import getopt
import os
import os.path
import stat
import compileall
import re

from xml.dom import minidom

from pr_utils import *
import pr_svn

help_message = '''
Project Reality Mod Build Generator

Usage:

	python pr_build.py [args]

Main options:

	-c --core         revisions separated by commas (no spaces)
	-l --levels       revisions separated by commas (no spaces)
	-n --number       version numbers separated by commas (no spaces) e.g. 0901,0902

Build options:

	-b --build        make a client build
	-s --server       make a server build
	-t --test         make a test build

Examples:

	python pr_build.py --core 2334,2356 --levels 456,488 --number 0856,0857 --build --server
	python pr_build.py -c 2334 -l 456 -n 0856 --build --test

Other options:

	-k --skip         skip to the last patch (must have all other builds ready)
	-w --wait         pauses after each major subversion command
	-z --zip          zip structure (default v2)

	-y --python       do not compile python
	-i --installer    do not create installers
	-u --update       do not update the repo
	-e --export       do not export the repo
	-a --archive      do not compile archives

	-p --paths        core and levels repo subpaths additions to defaults (comma separated)
	                  defaults: trunk, levels

	-v --verbose      run it verbosely
	-q --quiet        run it quietly
'''

root_path = os.curdir # os.path.dirname(__file__)

core_path      = os.path.join( root_path, 'core' )
levels_path    = os.path.join( root_path, 'levels' )
builds_path    = os.path.join( root_path, 'builds' )
logs_path      = os.path.join( root_path, 'logs' )

core_build     = os.path.join( builds_path, 'core' )
levels_build   = os.path.join( builds_path, 'levels' )
server_build   = os.path.join( builds_path, 'server' )
patch_build    = os.path.join( builds_path, 'patch' )

core_build_patch   = os.path.join( builds_path, 'core_patch' )
levels_build_patch = os.path.join( builds_path, 'levels_patch' )

exec_7zip  = 'C:\\repos\\core\\readme\\assets\\7za.exe'
exec_inno  = 'C:\\Program Files (x86)\\Inno Setup 5\\Compil32.exe'

installer_path        = os.path.join( core_path, 'readme', 'assets', 'builds', 'installer' )
core_installer_path   = os.path.join( installer_path, 'pr_core_base.iss' )
levels_installer_path = os.path.join( installer_path, 'pr_levels_base.iss' )
patch_installer_path  = os.path.join( installer_path, 'pr_patch_base.iss' )

filter_archives = {
	'v1': {
		'objects/objects_client': ['*.con', '*.tweak', '*.collisionmesh']
	},
	'v2': {
		'objects/common_client': ['*.con', '*.tweak', '*.collisionmesh'],
		'objects/dynamicobjects_client': ['*.con', '*.tweak', '*.collisionmesh'],
		'objects/effects_client': ['*.con', '*.tweak', '*.collisionmesh'],
		'objects/kits_client': ['*.con', '*.tweak', '*.collisionmesh'],
		'objects/miscobjects_client': ['*.con', '*.tweak', '*.collisionmesh'],
		'objects/roads_client': ['*.con', '*.tweak', '*.collisionmesh'],
		'objects/soldiers_client': ['*.con', '*.tweak', '*.collisionmesh'],
		'objects/staticobjects_client': ['*.con', '*.tweak', '*.collisionmesh'],
		'objects/vegitation_client': ['*.con', '*.tweak', '*.collisionmesh'],
		'objects/vehicles_client': ['*.con', '*.tweak', '*.collisionmesh'],
		'objects/water_client': ['*.con', '*.tweak', '*.collisionmesh'],
		'objects/weapons_client': ['*.con', '*.tweak', '*.collisionmesh']
	}
}

old_archives = {
	'v1': {
		8066: {
			'objects/objects_client': [ 
				'Vehicles/Air/ch_the_z9', 
				'Vehicles/Air/gb_the_chinook',
				'Vehicles/Land/cf_jep_nyala',
				'Vehicles/Land/ch_jeep_vn3',
				'Vehicles/Land/gb_apc_scimitar',
				'Weapons/Handheld/GBLMG_M249MINIMI'
			]
		}
	},
	'v2': {}
}

archives_con = {
	'client': 'clientarchives.con',
	'server': 'serverarchives.con'
}

core_archives = {
	'v1': {
		'client': {
			'common_client': ( 'Common', False ),
			'menu/fonts_client': ( 'Fonts', False ),
			'menu/menu_client': ( 'Menu', False ),
			'shaders_client': ( 'Shaders', False ),
			'objects/objects_client': ( 'Objects', False )
		},
		'server': { 
			'common_server': ( 'Common', False ),
			'menu/menu_server': ( 'Menu', False ), 
			'objects/objects_server': ( 'Objects', False )
		}
	},
	'v2': {
		'client': {
			'common_client': ( 'Common', False ),
			'menu/fonts_client': ( 'Fonts', False ),
			'menu/menu_client': ( 'Menu', False ),
			'shaders_client': ( 'Shaders', False ),
			'objects/common_client': ( 'Objects', True ),
			'objects/dynamicobjects_client': ( 'Objects', True ),
			'objects/effects_client': ( 'Objects', True ),
			'objects/kits_client': ( 'Objects', True ),
			'objects/miscobjects_client': ( 'Objects', True ),
			'objects/roads_client': ( 'Objects', True ),
			'objects/soldiers_client': ( 'Objects', True ),
			'objects/staticobjects_client': ( 'Objects', True ),
			'objects/vegitation_client': ( 'Objects', True ),
			'objects/vehicles_client': ( 'Objects', True ),
			'objects/water_client': ( 'Objects', True ),
			'objects/weapons_client': ( 'Objects', True )
		},
		'server': { 
			'common_server': ( 'Common', False ),
			'menu/menu_server': ( 'Menu', False ), 
			'objects/common_server': ( 'Objects', True ),
			'objects/effects_server': ( 'Objects', True ),
			'objects/kits_server': ( 'Objects', True ),
			'objects/miscobjects_server': ( 'Objects', True ),
			'objects/roads_server': ( 'Objects', True ),
			'objects/soldiers_server': ( 'Objects', True ),
			'objects/staticobjects_server': ( 'Objects', True ),
			'objects/vegitation_server': ( 'Objects', True ),
			'objects/vehicles_server': ( 'Objects', True ),
			'objects/water_server': ( 'Objects', True ),
			'objects/weapons_server': ( 'Objects', True )
		}
	}
}

options = {
	'core': None,
	'levels': None,
	'number': None,
	'patch': None, # internal
	
	'build': False,
	'server': False,
	'test': False,
	'skip': False,
	'wait': False,
	'zip': 'v2',
	'paths': [ 'trunk', 'levels' ],
	
	'python': True,
	'installer': True,
	'update': True,
	'export': True,
	'archive': True,
	'cleanup': True,
	
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
				"hc:l:n:bstkwp:z:yiueavq", 
				[ "help", "core=", "levels=", "number=", "build", "server", "test", "skip", "wait", 
					"paths=", "zip=", "python", "installer", "update", "export", "archive", "verbose", "quiet" ])
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
				options['number'] = value.split(',')
			
			if option in ("-b", "--build"):
				options['build'] = True
			if option in ("-s", "--server"):
				options['server'] = True
			if option in ("-t", "--test"):
				options['test'] = True
			if option in ("-k", "--skip"):
				options['skip'] = True
			if option in ("-w", "--wait"):
				options['wait'] = True
			if option in ("-z", "--zip") and value in core_archives:
				options['zip'] = value
			if option in ("-p", "--paths"):
				paths = value.split(',')
				for p in paths:
					options['paths'].append( p.strip('/') )
			
			if option in ("-y", "--python"):
				options['python'] = False
			if option in ("-i", "--installer"):
				options['installer'] = False
			if option in ("-u", "--update"):
				options['update'] = False
			if option in ("-e", "--export"):
				options['export'] = False
			if option in ("-a", "--archive"):
				options['archive'] = False
			
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
		if len( options['core'] ) != len( options['number'] ):
			raise Usage('Number of revisions is different than the total of version numbers.')
		
		for r in ['core','levels']:
			last_rev = 0
			for rev in options[r]:
				if last_rev > int( rev ):
					raise Usage('%s revision %s is smaller than the previous revision %s' % ( r, rev, last_rev ) )
				else:
					last_rev = int( rev )
		
		for num in options['number']:
			last_num = 0
			if last_num > int( num ):
				raise Usage('%s version number is smaller than the previous version number %s' % ( num, last_num ) )
			else:
				last_num = int( num )
		
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
				
				if len( options['core'] ) == 1:
					core_installer( options['number'][-1], options['test'] )
					levels_installer( options['number'][-1], options['test'] )
				
				else:
					
					patch_installer( options['number'][-1], options['number'][-2], options['test'] )
					
					if not options['skip']:
						core_installer( options['number'][-1], options['test'] )
						levels_installer( options['number'][-1], options['test'] )
			
			if options['server']:
				server_installer( options['number'][-1], options['test'] )
		
		verbose( 'DONE', True )
	
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
		
		delete( path=cb, verbose=options['verbose'] )
		delete( path=lb, verbose=options['verbose'] )
		
		if not patch:
			
			export_repo( core_path, cb )
			export_repo( levels_path, lb )
		
		else:
			
			core_lrevision   = int( options['core'][patch-1] )+1
			levels_lrevision = int( options['levels'][patch-1] )+1
			
			if core_lrevision <= int( core_revision ):
				core_log = log_repo( core_path, core_lrevision, core_revision )
				for path in paths_repo( core_log, patch, options['paths'] ):
					copy( os.path.join( core_path, path ), os.path.join( cb, path ), options['verbose'] )
			
			if levels_lrevision <= int( levels_revision ):
				levels_log = log_repo( levels_path, levels_lrevision, levels_revision )
				for path in paths_repo( levels_log, patch, options['paths'] ):
					copy( os.path.join( levels_path, path ), os.path.join( lb, path ), options['verbose'] )
		
	if options['cleanup']:
		verbose( 'CLEANUP %s' % patch )

		delete( path=os.path.join( cb, 'build_pr.bat' ), verbose=options['verbose'] )
		delete( path=os.path.join( cb, 'readme', 'assets' ), verbose=options['verbose'] )
		delete( path=cb, pattern='bst*.md5', verbose=options['verbose'] )
		delete( path=lb, pattern='assets', recursive=True, verbose=options['verbose'] )
		delete( path=lb, pattern='server', recursive=True, verbose=options['verbose'] )
		clean_archives( cb, core_archives[options['zip']]['server'] )
		clean_archives( cb, core_archives[options['zip']]['client'] )
		empty_archives( cb, core_revision )
		clean_atlas( cb )
	
	if options['archive']:
		verbose( 'ARCHIVE %s' % patch )
		
		build_archives( cb, core_archives[options['zip']]['server'], sufix )
		build_archives( cb, core_archives[options['zip']]['client'], sufix )
		copy( os.path.join( cb, 'shaders_client%s.zip' % sufix ), 
					os.path.join( cb, 'shaders_client_pr%s.zip' % sufix ), options['verbose'] )
		copy( os.path.join( cb, 'shaders_client%s.zip' % sufix ), 
					os.path.join( cb, 'shaders_night_client%s.zip' % sufix ), options['verbose'] )
		delete_archives( cb, core_archives[options['zip']]['server'] )
		delete_archives( cb, core_archives[options['zip']]['client'] )
		update_archives( patch )
	
	
	if patch:
		verbose( 'MERGE PATCH %s' % patch )
		
		merge( cb, core_build,   options['verbose'] )
		merge( lb, levels_build, options['verbose'] )
		
def build_python( patch ):
	
	verbose( 'PYTHON BUILD %s' % patch )
	
	delete( path=os.path.join( core_build, 'python', 'game' ), verbose=options['verbose'] )
	export_repo( os.path.join( core_path, 'python', 'game' ), os.path.join( core_build, 'python', 'game' ) )
	compile_python( os.path.join( core_build, 'python', 'game' ) )
	clean_python( os.path.join( core_build, 'python' ) )
	
	if patch:
		delete( path=os.path.join( path_core_build( patch ), 'python', 'game' ), verbose=options['verbose'] )
		copy( os.path.join( core_build, 'python', 'game' ), os.path.join( path_core_build( patch ), 'python', 'game' ), options['verbose'] )

def build_patch( patch ):
	
	verbose( 'PATCH BUILD %s' % patch )
	
	delete( path=patch_build, verbose=options['verbose'] )
	merge( path_core_build( patch ),   patch_build,                           options['verbose'] )
	merge( path_levels_build( patch ), os.path.join( patch_build, 'levels' ), options['verbose'] )

def build_server( patch ):
	
	verbose( 'SERVER BUILD %s' % patch )
	
	delete( path=server_build, verbose=options['verbose'] )
	merge( core_build,   server_build,                           options['verbose'] )
	merge( levels_build, os.path.join( server_build, 'levels' ), options['verbose'] )
	
	verbose( 'SERVER CLEANUP' )

	delete( os.path.join( server_build, 'levels' ), '*client.zip', True, [], options['verbose'] )
	delete( os.path.join( server_build, 'levels' ), '*.png',       True, [], options['verbose'] )

	for p,o in core_archives[options['zip']]['client'].iteritems():
		delete( path=os.path.join( server_build, '%s.zip' % os.path.normcase( p ) ), verbose=options['verbose'] )
		for i in range( 1, patch+1 ):
			delete( path=os.path.join( server_build, '%s_patch%s.zip' % ( os.path.normcase( p ), i ) ), verbose=options['verbose'] )
	
	delete( path=os.path.join( server_build, 'shaders_client_pr.zip' ), verbose=options['verbose'] )
	delete( path=os.path.join( server_build, 'shaders_night_client.zip' ), verbose=options['verbose'] )
	
	for i in range( 1, patch+1 ):
		delete( path=os.path.join( server_build, 'shaders_client_pr_patch%s.zip' % i ), verbose=options['verbose'] )
		delete( path=os.path.join( server_build, 'shaders_night_client_patch%s.zip' % i ), verbose=options['verbose'] )
	
	delete( path=os.path.join( server_build, archives_con['client'] ), verbose=options['verbose'] )
	delete( path=os.path.join( server_build, 'menu', 'external' ), verbose=options['verbose'] )
	delete( path=os.path.join( server_build, 'readme', 'bf2editor' ), verbose=options['verbose'] )
	delete( path=os.path.join( server_build, 'readme', 'dotnet' ), verbose=options['verbose'] )
	delete( path=os.path.join( server_build, 'readme', 'icons' ), verbose=options['verbose'] )
	delete( path=os.path.join( server_build, 'readme' ), pattern='*.pdf', verbose=options['verbose'] )
	delete( path=os.path.join( server_build, 'movies' ), verbose=options['verbose'] )
	delete( path=os.path.join( server_build, '00000000.256' ), verbose=options['verbose'] )
	delete( path=os.path.join( server_build, 'pr.exe' ), verbose=options['verbose'] )
	delete( os.path.join( server_build, 'readme' ), '*.txt', False, ['license.txt'], options['verbose'] )
	
	# rename( os.path.join( server_build, 'settings', 'prserverusersettings.con' ), os.path.join( server_build, 'settings', 'usersettings.con' ), options['verbose'] )
	# os.chmod( os.path.join( server_build, 'settings', 'usersettings.con' ), stat.S_IREAD )
	
def server_installer( current, test ):
	
	verbose( 'SERVER INSTALLER %s TEST %s' % ( current, test ) )
	
	if test:
		server_build_renamed = os.path.join( builds_path, 'pr_test' )
	else:
		server_build_renamed = os.path.join( builds_path, 'pr' )
	
	filename = os.path.join( builds_path, 'pr_%s_server.zip' % current )
	
	delete( path=server_build_renamed, verbose=options['verbose'] )
	
	rename( server_build, server_build_renamed, options['verbose'] )
	delete( path=filename, verbose=options['verbose'] )
	zip( server_build_renamed, filename, True )
	rename( server_build_renamed, server_build, options['verbose'] )

def core_installer( current, test ):
	
	verbose( 'CORE INSTALLER %s TEST %s' % ( current, test ) )
	client_installer( 'core', core_installer_path, current, None, test )
	
def levels_installer( current, test ):
	
	verbose( 'LEVELS INSTALLER %s TEST %s' % ( current, test ) )
	client_installer( 'levels', levels_installer_path, current, None, test )

def patch_installer( current, previous, test ):
	
	verbose( 'PATCH INSTALLER %s - %s TEST %s' % ( previous, current, test ) )
	client_installer( 'patch', patch_installer_path, current, previous, test )

def client_installer( type, script, current, previous=None, test=False):
	
	verbose( 'Running %s installer %s' % ( type, script ), False )
	
	final = script.replace( '_base', '' )
	
	b = open( script, 'r' )
	f = open( final,  'w' )
	
	for line in b:
		
		if previous:
			line = line.replace( 'old_version_number', previous )
		
		if not test:
			line = line.replace( '_version_number', '' )
		else:
			line = line.replace( '_version_number', '_test' )
		
		line = line.replace( 'version_number', current )
		
		f.write( line )
	
	b.close()
	f.close()
	
	if os.path.exists( exec_inno ):
		os.spawnl(os.P_WAIT, exec_inno, os.path.basename( exec_inno ), '/cc', final)
		
		output   = os.path.join( installer_path, 'Output', 'setup.exe' )
		
		if previous:
			filename = os.path.join( builds_path, 'pr_%s_to_%s_%s_setup.exe' % ( previous, current, type ) )
		else:
			filename = os.path.join( builds_path, 'pr_%s_%s_setup.exe' % ( current, type ) )
		
		delete( path=filename, verbose=options['verbose'] )
		copy( output, filename, options['verbose'] )
		delete( path=output, verbose=options['verbose'] )

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
	wait()

def export_repo( path, destination ):
	
	verbose( 'Exporting %s to %s' % ( path, destination ), False )
	pr_svn.export( path, destination, options['quiet'] )

def log_repo( path, start, end ):
	
	if start:
		revision = '%s:%s' % ( start, end )
	else:
		revision = end
	
	verbose( 'Log %s revision %s' % ( path, revision ), False )
	
	logs = pr_svn.log( path, revision, True, True )
	wait()
	
	return logs

def paths_repo( log, patch, remove=['trunk'] ):
	return pr_svn.get_paths( log, remove )

def empty_archives( path, revision ):
	
	for rev,paths in old_archives[options['zip']].iteritems():
		if revision > rev:
			continue
		for p,dirs in paths.iteritems():
			dir = os.path.join( path, os.path.normcase( p ) + '-zip' )
			if not os.path.exists( dir ):
				continue
			for d in dirs:
				os.makedirs( os.path.join( dir, os.path.normcase( d ) ) )

def clean_archives( path, archives ):

	for p,o in archives.iteritems():
		
		dir  = os.path.join( path, '%s-zip'   % ( os.path.normcase( p ) ) )
		
		if not os.path.exists( dir ):
			continue
		
		verbose( 'Cleaning %s' % ( dir ), False )
		
		delete( path=dir, pattern='assets',      recursive=True, verbose=options['verbose'] )
		delete( path=dir, pattern='*.db',        recursive=True, verbose=options['verbose'] )
		delete( path=dir, pattern='*.samp*',     recursive=True, verbose=options['verbose'] ) 
		delete( path=dir, pattern='*.max',       recursive=True, verbose=options['verbose'] )
		delete( path=dir, pattern='*.3ds',       recursive=True, verbose=options['verbose'] )
		delete( path=dir, pattern='*.psd',       recursive=True, verbose=options['verbose'] )
		delete( path=dir, pattern='samples.tga', recursive=True, verbose=options['verbose'] )
		delete( path=dir, pattern='uvs.tga',     recursive=True, verbose=options['verbose'] )
		
		if p in filter_archives[options['zip']]:
			for f in filter_archives[options['zip']][p]:
				delete( path=dir, pattern=f, recursive=True, verbose=options['verbose'] )
		
		verbose( 'Deleting empty folders from %s' % ( dir ), False )
		
		for root, dirs, files in os.walk( dir, topdown=False ):
			for name in dirs:
				if len( os.listdir(os.path.join(root, name)) ) == 0:
					os.rmdir(os.path.join(root, name))

def build_archives( path, archives, sufix='' ):
	
	for p,o in archives.iteritems():
		
		dir  = os.path.join( path, '%s-zip'   % ( os.path.normcase( p ) ) )
		file = os.path.join( path, '%s%s.zip' % ( os.path.normcase( p ), sufix ) )
		
		if not os.path.exists( dir ):
			continue
		
		if o[1]:
			ren = dir.replace( '_client-zip', '' )
			ren = ren.replace( '_server-zip', '' )
			folder = True
		else:
			ren = dir
			folder = False
		
		if o[1]:
			rename( dir, ren, options['verbose'] )
		
		verbose( 'Building archive %s from %s' % ( file, ren ), False )
		
		if os.path.exists( file ):
			delete( path=file, verbose=options['verbose'] )
		
		zip( ren, file, folder )
		
		if o[1]:
			rename( ren, dir, options['verbose'] )

def compile_python( path ):
	
	verbose( 'Compiling python', False )
	compileall.compile_dir( path, 1, quiet=options['quiet'] )

def clean_python( path ):
	
	verbose( 'Cleaning python %s' % path, False )
	
	delete( path=path, pattern='assets',   recursive=True, verbose=options['verbose'] )
	delete( path=path, pattern='compiled', recursive=True, verbose=options['verbose'] )
	delete( path=path, pattern='debug',    recursive=True, verbose=options['verbose'] )
	
	game = os.path.join( path, 'game' )
	delete( game, '*.py', True, [ '__init__.py', 'gpm_*.py', 'realityconfig_common.py', 'realityconfig_local.py', 'realityconfig_private.py', 'realityconfig_coop.py' ], options['verbose'] )
	delete( game, 'gpm_*.pyc', True, [], options['verbose'] )
	delete( game, 'realityconfig_*.pyc', True, [ 'realityconfig_public.pyc' ], options['verbose'] )
	delete( game, '__init__.pyc', True, [], options['verbose'] )

def clean_atlas( path ):

	verbose( 'Cleaning atlas files %s' % path, False )
	
	r = re.compile('^Menu\\\(\S+)\s+?.*$')
	
	menu_server = os.path.join( path, 'menu', 'menu_server-zip' )
	menu_client = os.path.join( path, 'menu', 'menu_client-zip' )
	
	if not os.path.exists(menu_client) or not os.path.exists(menu_server):
		return
	
	tac = os.path.join( menu_server, 'Atlas', 'PR_MemeAtlas.tac' )
	
	if not os.path.exists(tac):
		return
	
	for line in open(tac):
		
		match = r.search(line)
		if not match:
			continue

		filename = os.path.join( menu_client, os.path.normcase( match.group(1) ) )

		if not os.path.exists( filename ):
			continue
		
		# print filename
		delete( filename )

def delete_archives( path, archives ):
	
	for p,o in archives.iteritems():
		dir = os.path.join( path, '%s-zip' % os.path.normcase( p ) )
		
		if not os.path.exists( dir ):
			continue
		
		verbose( 'Deleting archive folder %s' % dir, False )
		delete( path=dir, verbose=options['verbose'] )

def update_archives( patch ):
	
	for type,filecon in archives_con.iteritems():
		
		repo_filecon  = os.path.join( core_path, filecon )
		build_filecon = os.path.join( core_build, filecon )
		patch_filecon = os.path.join( path_core_build( patch ), filecon )
		
		copy( repo_filecon, patch_filecon, options['verbose'] )
		
		if not patch:
			continue
		
		archive_content = ''
		patch_replacer  = 'rem patch'
		
		f = open( repo_filecon, 'r' )
		for line in f:
			archive_content += line
		f.close()
		
		for i in range( 1, patch+1 ):
			if archive_content.find( '_patch%s' % i ) != -1:
				continue
			
			patch_content = ''
			for p,o in core_archives[options['zip']][type].iteritems():
				
				ps = os.path.join( path_core_build( i ), os.path.normcase( p ) )
				
				if os.path.exists( '%s_patch%s.zip' % ( ps, i ) ):
					verbose( 'Updating %s to mount %s_patch%s.zip' % ( filecon, p, i ), False )
					patch_content += 'fileManager.mountArchive %s_patch%s.zip %s\n' % ( p, i, o[0] )
			
			if archive_content.find( patch_replacer ) != -1:
				archive_content = archive_content.replace( patch_replacer, patch_replacer + '\n' + patch_content )
			else:
				archive_content = patch_content + archive_content
		
		g = open( patch_filecon, 'w' )
		g.write( archive_content )
		g.close()
	
		copy( patch_filecon, build_filecon, options['verbose'] )

def verbose( text, prefix=True ):
	if options['verbose']:
		if prefix:
			print '--- ' + text
		else:
			print text

def zip( source, destination, folder=False, filters='' ):
	
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
		os.system( '"%s" a -tzip %s %s %s -xr!.svn\\ -xr!Assets\\ -xr!assets\\' % ( exec_7zip, d, s, filters ) )
	
	os.chdir( root )

def wait():
	if options['wait']:
		os.system('pause')

if __name__ == "__main__":
	sys.exit(main())
