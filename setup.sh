#!/bin/bash

echo "Initializing parameters and updating submodules..."

## Paths
BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SNIPPETSOURCE=${BASEDIR}/my-snippets
SNIPPETTARGET=~/.vim/bundle/vim-snippets/UltiSnips

## Update submodules
git submodule update --init --recursive

echo "Generating symbolic links..."

## Symlinks
# Vim
ln -sT ${BASEDIR}/vimrc ~/.vimrc
ln -sT ${BASEDIR}/vim/ ~/.vim

# Bash
ln -sT ${BASEDIR}/bashrc ~/.bashrc
ln -sT ${BASEDIR}/bash_profile ~/.bash_profile

# Tmux
ln -sT ${BASEDIR}/tmux.conf ~/.tmux.conf

# Julia
mkdir -p ~/.julia/config/
ln -sT ${BASEDIR}/startup.jl ~/.julia/config/startup.jl

# Git
ln -sT ${BASEDIR}/gitconfig ~/.gitconfig

# SSH
mkdir -p ~/.ssh
ln -sT ${BASEDIR}/sshconfig ~/.ssh/config

echo "Installing vim plugins..."

## Plugin installation for vim
vim +PluginInstall +qall &>/dev/null

echo "Adding snippet links to correct path..."

## symlink my-snippets to correct place
# Remove all symlinks in target dir
for TFILE in ${SNIPPETTARGET}/*.snippets; do
    if [[ -L ${TFILE} ]]; then
        unlink ${TFILE}
    fi
done
# Add new symlinks
for SFILE in ${SNIPPETSOURCE}/*.snippets; do
    TARGETPATH="${SNIPPETTARGET}/$(basename ${SFILE} .snippets).snippets"
    rm -rf ${TARGETPATH}
    ln -sT ${SFILE} ${TARGETPATH}
done

echo "Done!"
