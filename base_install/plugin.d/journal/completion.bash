#!/bin/bash

__mwiki_journal_build_completion(){
	local cur base
	local opts=""
	COMPREPLY=()
	cur="${COMP_WORDS[COMP_CWORD]}"

	if [ $COMP_CWORD -le 2 ]; then
		opts="--daemon"
	elif [ $COMP_CWORD -le 3 ]; then
		opts="--auto"
	fi

	COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
}

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
    if [ ${#COMPREPLY[@]} -ne 1 -o "${cur}" != "${COMPREPLY[0]}" ]; then
        compopt -o nospace
    fi
	return 0
}

__mwiki_journal_since(){
	local cur base opts
	if [ ${COMP_CWORD} -eq 2 -o ${COMP_CWORD} -eq 4 ]; then
		__mwiki_journal_view
	elif [ ${COMP_CWORD} -eq 3 ]; then
		COMPREPLY=(until)
	fi
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

	local journal_loc=`journal config journal location`
	local has_journal=$?

	case ${base} in
		# things that don't complete:
		help|entries)
			opts=""
			;;
		# things that complete to build-* entries
		query)
			if [ $COMP_CWORD -lt 3 ]; then
				path="$(journal config journal location)/plugin.d/"
				opts=`find "$path" -type f | grep -E 'query$' | sed "s_${path}__" | sed 's_/query$__' `
			fi
			;;
		# settings that we use mwiki completion for
		build)
			__mwiki_journal_build_completion
			;;
		edit|browse)
			if [ $COMP_CWORD -lt 3 ]; then
				export MWIKI_PATH="$journal_loc"
				opts=`journal entries`
				unset MWIKI_PATH
			fi
			;;
		config|view|since)
			__mwiki_journal_$base
			;;
		*)
			if [ -n "$journal_loc" ] ; then
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
