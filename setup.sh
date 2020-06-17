#!/bin/bash

## Paths
BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SNIPPETSOURCE=${BASEDIR}/my-snippets
SNIPPETTARGET=~/.vim/bundle/vim-snippets/UltiSnips

## Update submodules
git submodule update --init --recursive

## Symlinks
# Vim
ln -sT ${BASEDIR}/vimrc ~/.vimrc
ln -sT ${BASEDIR}/vim/ ~/.vim

# Bash
ln -sT ${BASEDIR}/bashrc ~/.bashrc
ln -sT ${BASEDIR}/bash_profile ~/.bash_profile

# Tmux
ln -sT ${BASEDIR}/tmux.conf ~/.tmux.conf

# Git
ln -sT ${BASEDIR}/gitconfig ~/.gitconfig

# SSH
mkdir -p ~/.ssh
ln -sT ${BASEDIR}/sshconfig ~/.ssh/config

## Plugin installation for vim
vim +PluginInstall +qall &>/dev/null

## symlink my-snippets to correct place
# Remove all symlinks in target dir
for TFILE in ${SNIPPETTARGET}/*.snippets; do
    if [[ -L ${TFILE} ]]; then
        unlink ${TFILE}
        rm -rf ${TFILE}
    fi
done
# Add new symlinks
for SFILE in ${SNIPPETSOURCE}/*.snippets; do
    ln -sT ${SFILE} "${SNIPPETTARGET}/$(basename ${SFILE} .snippets).snippets"
done
