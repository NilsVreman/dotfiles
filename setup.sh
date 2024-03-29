#!/bin/bash

echo "Initializing parameters and updating submodules..."

## Paths
BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMUXDIR="$BASEDIR/tmux"
NVIMDIR="$BASEDIR/nvim"
CODEDIR="$BASEDIR/vscode"
CONFDIR="$HOME/.config"

## Update Submodules
git submodule update --init --recursive

## Symlinks
echo "Generating symbolic links..."

# Bash
if [ -e "$HOME/.bashrc" ]; then
	rm $HOME/.bashrc # Cleaning up old links
fi
ln -sT $BASEDIR/bashrc $HOME/.bashrc
source $HOME/.bashrc
if [ -e "$HOME/.bash_profile" ]; then
	rm $HOME/.bash_profile # Cleaning up old links
fi
ln -sT $BASEDIR/bash_profile $HOME/.bash_profile

# NeoVim
if [ -d "$CONFDIR/nvim" ]; then
	rm $CONFDIR/nvim # Cleaning up old links
fi
ln -sT $NVIMDIR/ $CONFDIR/nvim
# 1. Install nvim
# 3. Open nvim and execute `<leader>l` followed by `I`
# Note: if the fons aren't loading properly check this reddit thread:
# https://www.reddit.com/r/Fedora/comments/u2fmwm/font_rendering_isnt_good_as_win_11/

# Tmux
if [ -d "$CONFDIR/tmux" ]; then
	rm $CONFDIR/tmux # Cleaning up old links
fi
ln -sT $TMUXDIR $CONFDIR/tmux
tmux source $CONFDIR/tmux/tmux.conf
# 1. Install tpm by running:
#   git clone https://github.com/tmux-plugins/tpm $TMUXDIR/plugins/tpm
# 2. Open a tmux session and press `prefix + I` (capital i, as in Install) to fetch the plugins.

# Julia
mkdir -p $HOME/.julia/config
rm $HOME/.julia/config/startup.jl
ln -sT $BASEDIR/startup.jl $HOME/.julia/config/startup.jl

# Git
rm $HOME/.gitconfig
ln -sT $BASEDIR/gitconfig $HOME/.gitconfig

# VsCode
if [ -e "$CONFDIR/Code/User/settings.json" ]; then
	rm $CONFDIR/Code/User/settings.json # Cleaning up old links
fi
ln -sT $CODEDIR/settings.json $CONFDIR/Code/User/settings.json
if [ -e "$CONFDIR/Code/User/keybindings.json" ]; then
	rm $CONFDIR/Code/User/keybindings.json # Cleaning up old links
fi
ln -sT $CODEDIR/keybindings.json $CONFDIR/Code/User/keybindings.json

echo "Done!"
