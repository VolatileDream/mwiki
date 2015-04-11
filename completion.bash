#!/bin/bash

__mwiki_build_completion(){
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

__mwiki_completion(){

	local cur base
	local opts=""
	COMPREPLY=()
	cur="${COMP_WORDS[COMP_CWORD]}"
	base="${COMP_WORDS[1]}"

	case ${base} in
		# things that don't complete:
		init|entries|generate|search)
			opts=""
			;;
		edit|browse)
			if [ $COMP_CWORD -lt 3 ]; then
				opts=`mwiki entries`
			fi
			;;
		build)
			__mwiki_build_completion
			;;
		*)
			# Add the defaults
			opts="init edit entries browse search build"
			;;
	esac

	if [ ! -z "$COMPREPLY" ]; then
		return 0
	fi
	COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )

	return 0
}

complete -F __mwiki_completion mwiki
