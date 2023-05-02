#!/bin/bash

echo "Initializing parameters and updating submodules..."

## Paths
BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

## Update submodules
git submodule update --init --recursive

## Symlinks
echo "Generating symbolic links..."

# Bash
ln -sT ${BASEDIR}/bashrc ~/.bashrc
ln -sT ${BASEDIR}/bash_profile ~/.bash_profile
source ~/.bashrc

# Vim
ln -sT ${BASEDIR}/nvim/ ~/.config/nvim

# Tmux
ln -sT ${BASEDIR}/tmux/ ~/.tmux
tmux source ~/.tmux/tmux.conf
#ln -sT ${BASEDIR}/tmux.conf ~/.tmux.conf

# Julia
mkdir -p ~/.julia/config/
ln -sT ${BASEDIR}/startup.jl ~/.julia/config/startup.jl

# Git
ln -sT ${BASEDIR}/gitconfig ~/.gitconfig

# SSH
mkdir -p ~/.ssh
ln -sT ${BASEDIR}/sshconfig ~/.ssh/config

echo "Done!"
