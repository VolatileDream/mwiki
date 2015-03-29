#!/usr/bin/env bash

# mwiki expects plugins to be added to the .mwiki.d/Tupfile, which will ensure
# that the get run and are kept up to date when files are changed.

# Here's the missing entry:

## : *.mw |> plugins/missing.sh %o |> build/~missing.html

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
	output="$1" ; shift
	( echo "<h1>Missing Pages</h1><hr>" ;
	 missing_pages |
	 sed 's_^.*$_<a href="./&.html">&</a>_' ) |
	awk '{ print $0 " <br>" }' > "$output"
}

run "$@"
