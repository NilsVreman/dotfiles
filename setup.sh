#!/bin/bash

echo "Initializing parameters and updating submodules..."

## Paths
BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMUXDIR="${BASEDIR}/tmux"
NVIMDIR="${BASEDIR}/nvim"

## Update submodules
git submodule update --init --recursive

## Symlinks
echo "Generating symbolic links..."

# Bash
ln -sT ${BASEDIR}/bashrc ~/.bashrc
ln -sT ${BASEDIR}/bash_profile ~/.bash_profile
source ~/.bashrc

# NeoVim
ln -sT ${NVIMDIR}/ ~/.config/nvim

# Tmux
mkdir -p ~/.tmux/plugins/
ln -sT ${TMUXDIR}/tpm ~/.tmux/plugins/tpm
ln -sT ${TMUXDIR}/tmux.conf ~/.tmux.conf
tmux source ~/.tmux.conf

# Julia
mkdir -p ~/.julia/config/
ln -sT ${BASEDIR}/startup.jl ~/.julia/config/startup.jl

# Git
ln -sT ${BASEDIR}/gitconfig ~/.gitconfig

# SSH
mkdir -p ~/.ssh
ln -sT ${BASEDIR}/sshconfig ~/.ssh/config

echo "Done!"
