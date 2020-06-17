#!/bin/bash

## Paths
BASEDIR=~/dotfiles
SNIPPETPATH=${BASEDIR}/my-snippets
SNIPPETTARGETPATH=~/.vim/bundle/vim-snippets/UltiSnips

## Symlinks
# Vim
ln -sT ${BASEDIR}/vimrc ~/.vimrc
ln -sT ${BASEDIR}/vim/ ~/.vim

## Plugin installation for vim
vim +PluginInstall +qall &>/dev/null

## Move my-snippets to correct place
cp ${SNIPPETPATH}/* ${SNIPPETTARGETPATH}/
