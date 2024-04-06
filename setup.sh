#!/bin/bash

echo "Initializing parameters and updating submodules..."

## Paths
BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMUXDIR="$BASEDIR/tmux"
NVIMDIR="$BASEDIR/nvim"
CONFDIR="$HOME/.config"
BAKDIR="$HOME/backups"

mkdir -p $CONFDIR
mkdir -p $BAKDIR

## Update Submodules
git submodule update --init --recursive

## Symlinks
echo "Generating symbolic links..."

# Bash
if [ -e "$HOME/.bashrc" ]; then
	cp -r $HOME/.bashrc $BAKDIR/bashrc.bak
	rm $HOME/.bashrc # Cleaning up old links
fi
ln -sT $BASEDIR/bashrc $HOME/.bashrc
source $HOME/.bashrc
if [ -e "$HOME/.bash_profile" ]; then
	cp -r $HOME/.bash_profile $BAKDIR/bash_profile.bak
	rm $HOME/.bash_profile # Cleaning up old links
fi
ln -sT $BASEDIR/bash_profile $HOME/.bash_profile

# NeoVim
if [ -d "$CONFDIR/nvim" ]; then
	cp -r $CONFDIR/nvim $BAKDIR/nvim.bak
	rm $CONFDIR/nvim # Cleaning up old links
fi
ln -sT $NVIMDIR/ $CONFDIR/nvim
echo "Don't forget to install nvim"
echo "NOTE: Mason (LSP/Linters/Formatters) need npm installed."
echo "  - Also Note that both rg (ripgrep) and fd (fd-find) needs to be installed"
echo "Open nvim and execute leader l followed by I"

# Tmux
if [ -d "$CONFDIR/tmux" ]; then
	cp -r $CONFDIR/tmux $BAKDIR/tmux.bak
	rm $CONFDIR/tmux # Cleaning up old links
fi
ln -sT $TMUXDIR $CONFDIR/tmux
tmux source $CONFDIR/tmux/tmux.conf
echo "Don't forget to install tpm by running:"
echo "  git clone https://github.com/tmux-plugins/tpm $TMUXDIR/plugins/tpm"
echo "Open a tmux session and press 'prefix + I' (capital i, as in Install) to fetch the plugins."

# Git
cp -r $HOME/.gitconfig $BAKDIR/gitconfig.bak
rm $HOME/.gitconfig
ln -sT $BASEDIR/gitconfig $HOME/.gitconfig

echo "Done!"
