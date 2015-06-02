#!/bin/bash


__mwiki_journal_view(){
	local cur base opts
	COMPREPLY=()
	cur="${COMP_WORDS[COMP_CWORD]}"
	prev="${COMP_WORDS[COMP_CWORD-1]}"

	# this disgusting shell line
	COMPREPLY=( $(journal entries |
		# get only the next chunk of the date
		# TODO relies on file date stamp encoding
		grep -Eo "^${cur}[[:digit:]]*(-|$)" |
		# grab unique entries
		uniq ) )

	return 0
}

__mwiki_journal_config(){
	local cur base opts
	COMPREPLY=()
	cur="${COMP_WORDS[COMP_CWORD]}"
	prev="${COMP_WORDS[COMP_CWORD-1]}"

	if [ $COMP_CWORD -eq 2 ]; then
		# doing the second word
		opts="$(journal config | grep '\[' | tr -d '[]')"
		
	elif [ $COMP_CWORD -eq 3 ]; then
		# doing third thing
		opts="$(journal config | write-from-to "\\[$prev\\]" '\[' | sed 's/ =.*//' )"
	fi

	COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )

	return 0
}

__mwiki_journal(){

	local cur base opts
	COMPREPLY=()
	cur="${COMP_WORDS[COMP_CWORD]}"
	base="${COMP_WORDS[1]}"

	case ${base} in
		# things that don't complete:
		help|entries)
			opts=""
			;;
		# things that complete to build-* entries
		query)
			path="$(journal config journal location)/plugin.d/"
			opts=`find "$path" -type f | grep -E 'query$' | sed "s_${path}__" | sed 's_/query$__' `
			;;
		# settings that we use mwiki completion for
		build)
			__mwiki_build_completion
			;;
		edit|browse)
			__mwiki_completion
			;;
		config)
			__mwiki_journal_config
			;;
		view)
			__mwiki_journal_view
			;;
		*)
			if journal config &> /dev/null ; then
				# add the extensions that exist
				path="$(journal config journal location)/plugin.d/journal/extensions/"
				opts=`find "$path" -type f 2> /dev/null | sed "s_${path}__"`
				# Add the defaults
				opts="build browse config edit entries query update view help $opts"
			else
				opts="create"
			fi
			;;
	esac

	if [ -n "$COMPREPLY" ]; then
		return 0
	fi

	COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )

	return 0
}

complete -F __mwiki_journal journal
