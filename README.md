Project Reality Mod Build Script
================================

[Project Reality Mod](http://realitymod.com) script for making full or patch builds.

Requirements
------------

* Python 2.3+
* Directory structure:
	- `/core` (working copy for core repo trunk folder)
	- `/levels` (working copy for maps repo levels folder)
	- `/installer`
		- `pr_core_base.iss`
		- `pr_levels_base.iss`
		- `pr_patch_base.iss`
	- `pr_build.py`

Usage
-----

The `pr_build.py` script help:

	Required arguments:

		-c --core       revisions separated by commas (no spaces)
		-l --levels     revisions separated by commas (no spaces)
		-n --number     version number (e.g. 0856)

	Build arguments:

		-b --build      make a client build
		-s --server     make a server build
		-t --test       make a test build

	Example:

		python pr_build.py --core 2334,2356 --levels 456,488 --number 0856 --build --server

	Optional arguments:

		-k --skip       skip to the last patch (must have all other builds ready)

		-y --python     do not compile python
		-i --installer  do not create installers
		-u --update     do not update the repo
		-e --export     do not export the repo

		-v --verbose    run it verbosely
		-q --quiet      run it quietly

Testing
-------

You can run a test with the dummy data in the `test` folder by running `pr_build_test.py` with the following command:

	python pr_build_test.py -c 0,1,2 -l 0,1,2 -n 0123 -b -s -t -v

The results will be in the `builds_test` folder.

