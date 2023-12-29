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
if [ -e "$HOME/.bashrc" ] ; then
	rm $HOME/.bashrc		# Cleaning up old links
fi
ln -sT $BASEDIR/bashrc $HOME/.bashrc
source $HOME/.bashrc
if [ -e "$HOME/.bash_profile" ] ; then
	rm $HOME/.bash_profile		# Cleaning up old links
fi
ln -sT $BASEDIR/bash_profile $HOME/.bash_profile

# NeoVim
if [ -d "$CONFDIR/nvim" ] ; then
	rm $CONFDIR/nvim		# Cleaning up old links
fi
ln -sT $NVIMDIR/ $CONFDIR/nvim
# 1. Install nvim
# 2. Clone the repository:
#   git clone --depth 1 https://github.com/wbthomason/packer.nvim ~/.local/share/nvim/site/pack/packer/start/packer.nvim
# 3. Open nvim and execute `:PackerInstall`

# Tmux
mkdir -p $CONFDIR/tmux
if [ -e "$CONFDIR/tmux/tmux.conf" ] ; then
	rm $CONFDIR/tmux/tmux.conf	# Cleaning up old links
fi
ln -sT $TMUXDIR/tmux.conf $CONFDIR/tmux/tmux.conf
tmux source $CONFDIR/tmux/tmux.conf

# Julia
mkdir -p $HOME/.julia/config
rm $HOME/.julia/config/startup.jl
ln -sT $BASEDIR/startup.jl $HOME/.julia/config/startup.jl

# Git
rm $HOME/.gitconfig
ln -sT $BASEDIR/gitconfig $HOME/.gitconfig

# VsCode
if [ -e "$CONFDIR/Code/User/settings.json" ] ; then
	rm $CONFDIR/Code/User/settings.json	# Cleaning up old links
fi
ln -sT $CODEDIR/settings.json $CONFDIR/Code/User/settings.json
if [ -e "$CONFDIR/Code/User/keybindings.json" ] ; then
	rm $CONFDIR/Code/User/keybindings.json	# Cleaning up old links
fi
ln -sT $CODEDIR/keybindings.json $CONFDIR/Code/User/keybindings.json

echo "Done!"
