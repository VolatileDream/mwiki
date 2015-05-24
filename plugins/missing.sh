#!/usr/bin/env bash

# mwiki runs plugins inside it's .mwkik.d/ directory.
MWIKI_DIR="."

pages_linked_to(){

	mwiki entries |
	while read entry ; do
		cat "$MWIKI_DIR/$entry.mw" |
		grep -o '[#@]\([a-zA-Z_0-9]\+\)' |
		tr -d '#@'
	done |
	sort -u
}

pages(){
	mwiki entries |
	sort -u
}

missing_pages(){
	( pages_linked_to ; pages ) |
	# join the two lists
	sort |
	# show only unique entries, which gives us the pages that are missing
	uniq -u
}

run(){
	( echo "<h1>Missing Pages</h1><hr>" ;
	 missing_pages |
	 sed 's_^.*$_<a href="./&.html">&</a>_' ) |
	awk '{ print $0 " <br>" }'
}


run "$@"