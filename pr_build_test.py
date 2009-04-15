#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import os.path
import pr_build

# USAGE
# python pr_build_test.py -c 0,1,2 -l 0,1,2 -n 0123 -b -s -t -v -q

# remove all folders
# for p in [ 'builds', 'core', 'core_patch1', 'core_patch2', 'installer', 'levels', 'levels_patch1', 'levels_patch2' ]:
# 	os.system( 'rm -rf "%s"' % os.path.join( os.curdir, p ) )

# copy test folders
for p in os.listdir( os.path.join( os.curdir, 'test' ) ):
	os.system( 'cp -r "%s" "%s"' % ( os.path.join( os.curdir, 'test', p ), os.curdir ) )

def update_repo( path, revision ):
	
	if revision > 0:
		if path == pr_build.core_path:
			pr_build.copy( os.path.join( os.curdir, 'core_patch%s' % revision ), path )
		if path == pr_build.levels_path:
			pr_build.copy( os.path.join( os.curdir, 'levels_patch%s' % revision ), path )

def export_repo( path, destination ):
	pr_build.copy( path, destination )

def log_repo( path, start, end, destination ):
	pass

def paths_repo( source, patch ):
	
	if source == pr_build.core_log:
		if patch == 1:
			return [ 'menu/menu_client-zip/super.con', 'menu/menu_server-zip/super.tweak' ] 
		if patch == 2:
			return [ 'common_client-zip/something.con', 'objects/objects_server-zip/vehicles/vehicles.tweak', 'objects/objects_server-zip/weapons/weapons.tweak' ]
	if source == pr_build.levels_log:
		if patch == 1:
			return [ 'archer/objects_server.zip' ]
		if patch == 2:
			return [ 'archer/objects_client.zip', 'archer/objects_server.zip', 'fallujah/objects_server.zip' ]
	
	return []


pr_build.update_repo = update_repo
pr_build.export_repo = export_repo
pr_build.log_repo    = log_repo
pr_build.paths_repo  = paths_repo

if __name__ == "__main__":
	sys.exit(pr_build.main())

