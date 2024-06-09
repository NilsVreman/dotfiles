# ~/.bashrc: executed by bash(1) for non-login shells.
# see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
# for examples

# If not running interactively, don't do anything
case $- in
*i*) ;;
*) return ;;
esac

# don't put duplicate lines or lines starting with space in the history.
# See bash(1) for more options
HISTCONTROL=ignoreboth

# append to the history file, don't overwrite it
shopt -s histappend

# for setting history length see HISTSIZE and HISTFILESIZE in bash(1)
HISTSIZE=500
HISTFILESIZE=500

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# If set, the pattern "**" used in a pathname expansion context will
# match all files and zero or more directories and subdirectories.
#shopt -s globstar

# Used to be able to pattern match when moving stuff
shopt -s extglob

# make less more friendly for non-text input files, see lesspipe(1)
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
	debian_chroot=$(cat /etc/debian_chroot)
fi

## Command Prompt setup
# Color definition
COLOR_HOST="\e[38;5;2m"
COLOR_PATH="\e[38;5;3m"
COLOR_CHANGE="\e[38;5;9m"
COLOR_RESET="\e[0m"

# Format the git information
function parse_git_branch {
	# Check if we are in a git repo
	if [ -d .git ] || git rev-parse --is-inside-work-tree &>/dev/null; then
		local git_status="$(git status --porcelain=v1 2>/dev/null)"

		function _count_git_pattern() {
			echo "$(grep "^$1" <<<$git_status | wc -l)"
		}

		local branch="$(git branch 2>/dev/null | sed -e "/^[^*]/d" -e "s/* \(.*\)/\1/")"
		local remote_branch="origin/$branch"
		local staged_modified=$(_count_git_pattern "M ")
		local unstaged_modified=$(_count_git_pattern " M")
		local both_modified=$(_count_git_pattern "MM")
		local staged_deleted=$(_count_git_pattern "D ")
		local unstaged_deleted=$(_count_git_pattern " D")
		local staged_renamed=$(_count_git_pattern "R ")
		local unstaged_renamed=$(_count_git_pattern " R")
		local added_files=$(_count_git_pattern "A ")
		local untracked_files=$(_count_git_pattern "??")
		local ahead_commits=$(git rev-list --count ${remote_branch}..${branch} 2>/dev/null)
		local behind_commits=$(git rev-list --count ${branch}..${remote_branch} 2>/dev/null)

		local git_info="[$branch"

		if [[ "$ahead_commits" -gt 0 || "$behind_commits" -gt 0 ]]; then
			git_info="${git_info} | C: \x01$COLOR_HOST\x02${ahead_commits}\x01$COLOR_PATH\x02/\x01$COLOR_CHANGE\x02${behind_commits}\x01$COLOR_PATH\x02"
		fi

		if [[ $staged_renamed -gt 0 || $unstaged_renamed -gt 0 ]]; then
			git_info="${git_info} | R: \x01$COLOR_HOST\x02${staged_renamed}\x01$COLOR_PATH\x02/\x01$COLOR_CHANGE\x02${unstaged_renamed}\x01$COLOR_PATH\x02"
		fi

		if [[ $staged_deleted -gt 0 || $unstaged_deleted -gt 0 ]]; then
			git_info="${git_info} | D: \x01$COLOR_HOST\x02${staged_deleted}\x01$COLOR_PATH\x02/\x01$COLOR_CHANGE\x02${unstaged_deleted}\x01$COLOR_PATH\x02"
		fi

		if [[ $staged_modified -gt 0 || $unstaged_modified -gt 0 || $both_modified -gt 0 ]]; then
			git_info="${git_info} | M: \x01$COLOR_HOST\x02$((staged_modified + both_modified))\x01$COLOR_PATH\x02/\x01$COLOR_CHANGE\x02$((unstaged_modified + both_modified))\x01$COLOR_PATH\x02"
		fi

		if [[ $untracked_files -gt 0 || $added_files -gt 0 ]]; then
			git_info="${git_info} | U: \x01$COLOR_HOST\x02${added_files}\x01$COLOR_PATH\x02/\x01$COLOR_CHANGE\x02${untracked_files}\x01$COLOR_PATH\x02"
		fi

		git_info="${git_info}]"

		echo -e " $git_info"
	else
		echo ""
	fi
}

# Command prompt color and look
PS1="${debian_chroot:+($debian_chroot)}\001$COLOR_HOST\002\u@\h\001$COLOR_RESET\002:\001$COLOR_PATH\002./\W\$(parse_git_branch)\001$COLOR_RESET\002\n\001$COLOR_PATH\002[\D{%b %d | %H:%M:%S}]\001$COLOR_RESET\002\$ "
# To get gruvbox terminal colours: bash -c  "$(wget -qO- https://git.io/vQgMr)"

### Aliases
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'

# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
if ! shopt -oq posix; then
	if [ -f /usr/share/bash-completion/bash_completion ]; then
		. /usr/share/bash-completion/bash_completion
	elif [ -f /etc/bash_completion ]; then
		. /etc/bash_completion
	fi
fi

# --------------------------------
# Make vim default editor
# --------------------------------

alias nvim='~/neovim/bin/nvim'
export EDITOR='nvim'
export VISUAL='nvim'

# --------------------------------
# Commands
# --------------------------------

# enable color support of ls and also add handy aliases
alias ls='ls --color=auto'

alias ll='ls -alF'
alias la='ls -A'
alias l='ls -1'

# My aliases
cdw() { cd ~/"$1" && clear; }
alias t='tree'

# Tmux
alias tmux='TERM=xterm-256color tmux'

# Bind autocompletion here to overwrite the one in /etc/inputrc
bind "set completion-ignore-case on"
bind "set show-all-if-ambiguous on"

# Rust related
. "$HOME/.cargo/env"

# Zoxide
eval "$(zoxide init --cmd cd bash)"

source $HOME/alacritty/extra/completions/alacritty.bash
