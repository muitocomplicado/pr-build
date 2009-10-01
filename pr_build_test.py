#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import os.path
import pr_build

from time import sleep

# Replacing some repo commands to load dummy test data

def update_repo( path, revision ):
	
	if revision > 0:
		if path == pr_build.core_path:
			pr_build.copy( os.path.join( pr_build.root_path, 'test', pr_build.options['zip'], 'core_patch%s' % revision ), path )
		if path == pr_build.levels_path:
			pr_build.copy( os.path.join( pr_build.root_path, 'test', pr_build.options['zip'], 'levels_patch%s' % revision ), path )

def export_repo( path, destination ):
	pr_build.copy( path, destination )

def log_repo( path, start, end ):
	pass

def paths_repo( log, patch, remove=['trunk'] ):
	
	if remove == ['trunk']:
		if patch == 1:
			return [ 
				'menu/menu_client-zip/super.con',
				'menu/menu_server-zip/super.tweak'
			] 
		
		if patch == 2:
			if pr_build.options['zip'] == 'v1':
				return [ 
					'common_client-zip/something.con',
					'objects/objects_server-zip/vehicles/vehicles.tweak',
					'objects/objects_server-zip/weapons/weapons.tweak'
				]
			else:
				return [ 
					'common_client-zip/something.con',
					'objects/vehicles_server-zip/vehicles.tweak',
					'objects/weapons_server-zip/weapons.tweak'
				]
	
	if remove == ['levels']:
		if patch == 1:
			return [ 
				'archer/objects_server.zip'
			]
		if patch == 2:
			return [ 
				'archer/objects_client.zip',
				'archer/objects_server.zip',
				'fallujah/objects_server.zip'
			]
	
	return []

def delay():
	sleep(3)

# Updating paths to use test data

pr_build.update_repo = update_repo
pr_build.export_repo = export_repo
pr_build.log_repo    = log_repo
pr_build.paths_repo  = paths_repo
pr_build.delay       = delay

if __name__ == "__main__":
	
	if 'v2' in sys.argv:
		pr_build.options['zip'] = 'v2'
	
	pr_build.root_path = os.path.dirname(__file__)

	pr_build.core_path      = os.path.join( pr_build.root_path, 'test', pr_build.options['zip'], 'core' )
	pr_build.levels_path    = os.path.join( pr_build.root_path, 'test', pr_build.options['zip'], 'levels' )
	pr_build.installer_path = os.path.join( pr_build.root_path, 'test', pr_build.options['zip'], 'installer' )
	pr_build.builds_path    = os.path.join( pr_build.root_path, 'builds_test' )

	pr_build.core_build     = os.path.join( pr_build.builds_path, 'core' )
	pr_build.levels_build   = os.path.join( pr_build.builds_path, 'levels' )
	pr_build.server_build   = os.path.join( pr_build.builds_path, 'server' )
	pr_build.patch_build    = os.path.join( pr_build.builds_path, 'patch' )

	pr_build.core_build_patch   = os.path.join( pr_build.builds_path, 'core_patch' )
	pr_build.levels_build_patch = os.path.join( pr_build.builds_path, 'levels_patch' )

	pr_build.core_installer_path   = os.path.join( pr_build.installer_path, 'pr_core_base.iss' )
	pr_build.levels_installer_path = os.path.join( pr_build.installer_path, 'pr_levels_base.iss' )
	pr_build.patch_installer_path  = os.path.join( pr_build.installer_path, 'pr_patch_base.iss' )

	sys.exit(pr_build.main())

