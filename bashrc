# ~/.bashrc: executed by bash(1) for non-login shells.
# see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
# for examples

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
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

# make less more friendly for non-text input files, see lesspipe(1)
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

### Command Prompt setup
# Color definition
COLOR_HOST="\033[38;5;202m"
COLOR_PATH="\033[38;5;184m"
COLOR_GITCHANGED="\033[38;5;160m"
COLOR_GITUNTRACKED="\033[38;5;160m"
COLOR_GITADD="\033[38;5;172m"
COLOR_GITCOMMIT="\033[38;5;182m"
COLOR_GITCLEAN="\033[38;5;73m"
COLOR_GITOTHER="\033[38;5;128m"
COLOR_RESET="\033[0m"

# Pick correct color based on if we have changes or not
function parse_git_color {
    local git_status="$(git status 2> /dev/null)"

    if [[ $git_status =~ "Changes not staged for commit" || $git_status =~ "Untracked files" ]]; then
        echo -e $COLOR_GITCHANGED
    elif [[ $git_status =~ "Changes to be committed" ]]; then
        echo -e $COLOR_GITADD
    elif [[ $git_status =~ "Your branch is ahead of" ]]; then
        echo -e $COLOR_GITCOMMIT
    elif [[ $git_status =~ "nothing to commit" ]]; then
        echo -e $COLOR_GITCLEAN
    else
        echo -e $COLOR_GITOTHER
    fi
}

# Pick the branch we are on
function parse_git_branch {
  local git_status="$(git status 2> /dev/null)"
  local on_branch="On branch ([^${IFS}]*)"

  if [[ $git_status =~ $on_branch ]]; then
    local branch=${BASH_REMATCH[1]}
    echo " [$branch]"
  fi
}

# To get gruvbox terminal colours: bash -c  "$(wget -qO- https://git.io/vQgMr)"

# Command prompt color and look
PS1="${debian_chroot:+($debian_chroot)}\[$COLOR_HOST\]\u@\h\[$COLOR_RESET\]:\[$COLOR_PATH\]./\W\[\$(parse_git_color)\]\$(parse_git_branch)\[$COLOR_RESET\]\$ "

### Aliases
# enable color support of ls and also add handy aliases
alias ls='ls --color=auto'
#alias dir='dir --color=auto'
#alias vdir='vdir --color=auto'

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

# Added julia thread count
export JULIA_NUM_THREADS=4

# --------------------------------
# Commands
# --------------------------------
# Language aliases
alias python='python3'
alias julia11='/opt/julia/julia-v1.1.0/bin/julia'
alias julia='julia11'
alias matlab16='VERSION=R2016a matlab &'
alias matlab19='VERSION=R2019b matlab &'

# some more ls aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -1'

# My aliases
cdw() { cd ~/"$1" && clear; }
alias t='tree'
alias zotero='~/Downloads/Zotero-5.0.60_linux-x86_64/Zotero_linux-x86_64/zotero'

# XClip aliases
alias c='xclip'
alias v='xclip -o'

# Bind autocompletion here to overwrite the one in /etc/inputrc
bind "set completion-ignore-case on"
bind "set show-all-if-ambiguous on"
