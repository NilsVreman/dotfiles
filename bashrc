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

# Used to be able to pattern match when moving stuff
shopt -s extglob

# make less more friendly for non-text input files, see lesspipe(1)
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

### Command Prompt setup
# Color definition
COLOR_HOST="\e[38;5;2m"
COLOR_PATH="\e[38;5;3m"
COLOR_GIT="\e[38;5;11m"
COLOR_CHANGE="\e[38;5;9m"
COLOR_RESET="\e[0m"

# Pick the branch we are on
function parse_git_branch {
    local git_status="$(git status 2> /dev/null)"
    local on_branch="On branch ([^${IFS}]*)"

    if [[ $git_status =~ $on_branch ]]; then
        local branch=${BASH_REMATCH[1]}

        if [[ $git_status =~ "Your branch is up to date with" && $git_status =~ "nothing to commit" ]]; then
            echo -e " \x01$COLOR_GIT\x02[$branch]"
        else
            echo -e " \x01$COLOR_GIT\x02[$branch\x01$COLOR_CHANGE\x02*\x01$COLOR_GIT\x02]"
        fi
    fi
}

# To get gruvbox terminal colours: bash -c  "$(wget -qO- https://git.io/vQgMr)"

# Command prompt color and look
PS1="${debian_chroot:+($debian_chroot)}\001$COLOR_HOST\002\u@\h\001$COLOR_RESET\002:\001$COLOR_PATH\002./\W\$(parse_git_branch)\001$COLOR_RESET\002\$ "

### Aliases
# enable color support of ls and also add handy aliases
alias ls='ls --color=auto'

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
# Link java
# --------------------------------

export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-11.0.9.11-0.fc33.x86_64/

# --------------------------------
# Make vim default editor
# --------------------------------

export EDITOR='vim'
export VISUAL='vim'

# --------------------------------
# Commands
# --------------------------------
# Language aliases
alias python='python3'
alias matlab16='VERSION=R2016a matlab &'
alias matlab20='VERSION=R2020b matlab &'
alias julia15='~/.julia/v1.5.4/bin/julia'
alias julia17='~/.julia/v1.7.0/bin/julia'

# some more ls aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -1'

# Git Aliases
alias glog='git log --graph --oneline -n30'
alias gd='git diff'
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git pull'

# My aliases
cdw() { cd ~/"$1" && clear; }
alias t='tree'

# XClip aliases
alias c='xclip'
alias v='xclip -o'

# Bind autocompletion here to overwrite the one in /etc/inputrc
bind "set completion-ignore-case on"
bind "set show-all-if-ambiguous on"

# Rust related
. "$HOME/.cargo/env"
