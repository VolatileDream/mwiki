#!/usr/bin/env bash

# mwiki (through TUP) runs plugins inside it's mwiki directory.
MWIKI_DIR="."

page_mentions(){
	local page="$1" ; shift
	grep --files-with-match --ignore-case "[#@]$page" "$MWIKI_DIR/"*.mw |
	 sed "s_^$MWIKI_DIR/__" | sed 's_.mw$__'
	 sort -u
}

run(){
	local page="$1" ; shift
	( echo "<h2>Mentions</h2><hr>" ;
	  page_mentions "$page" |
	   sed 's_^.*$_<a href="./&.html">&</a>_' ) |
	awk '{ print $0 " <br>" }'
}

run "$@"
