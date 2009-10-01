# Project Reality Mod scripts

Some utility scripts used for creating [Project Reality Mod](http://realitymod.com) builds, changelogs, test lists, RSS feeds, etc.

* `pr_build.py` is a build creator for full and patch builds.
* `pr_changelog.py` is a changelog creator for parsing repo logs.
* `pr_svn.py` utility functions for dealing with svn.

Requires Python 2.3+


## pr_build.py

### Usage:

	python pr_build.py [args]

	Main options:

		-c --core         revisions separated by commas (no spaces)
		-l --levels       revisions separated by commas (no spaces)
		-n --number       version number (e.g. 0856)

	Build options:

		-b --build        make a client build
		-s --server       make a server build
		-t --test         make a test build

	Examples:

		python pr_build.py --core 2334,2356 --levels 456,488 --number 0856 --build --server
		python pr_build.py -c 2334 -l 456 -n 0856 --build --test

	Other options:

		-k --skip         skip to the last patch (must have all other builds ready)
		-w --wait         pauses after each major subversion command
		-z --zip          zip structure (default v1)

		-y --python       do not compile python
		-i --installer    do not create installers
		-u --update       do not update the repo
		-e --export       do not export the repo
		-a --archive      do not compile archives

		-p --paths        core and levels repo subpaths additions to defaults (comma separated)
		                  defaults: trunk, levels

		-v --verbose      run it verbosely
		-q --quiet        run it quietly

### Directory structure:

	/core (working copy for core repo trunk folder)
	/levels (working copy for maps repo levels folder)
	/builds
	pr_build.py

### Testing

You can run a test with the dummy data in the `test` folder by running `pr_build_test.py` with the following command:

	python pr_build_test.py -c 0,1,2 -l 0,1,2 -n 0123 -b -s -t -v -z v2

The results will be in the `test_builds` folder.


## pr_changelog.py

### Usage:

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
	
		-v --verbose     run it verbosely
		-q --quiet       run it quietly


