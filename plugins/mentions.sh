#!/usr/bin/env bash

# mwiki expects plugins to be added to the .mwiki.d/Tupfile, which will ensure
# that the get run and are kept up to date when files are changed.

# Here is the mentions entry:

## !mentions = | *.mw |> plugins/mentions.sh %B %o |>

# Note that it must get added to the pipeline of regular page generation.
# Because of the way Tup treats macro expansion, the macros that would generate
# the build/%B.html file must all be expanded by hand.

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
