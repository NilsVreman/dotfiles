#!/bin/bash

# Set some colors
CNT="[\e[1;36mNOTE\e[0m]"
COK="[\e[1;32mOK\e[0m]"
CAT="[\e[1;37mATTENTION\e[0m]"
CWR="[\e[1;35mWARNING\e[0m]"

# Paths
BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMUXDIR="$BASEDIR/tmux"
NVIMDIR="$BASEDIR/nvim"
CONFDIR="$HOME/.config"
OMPDIR="$CONFDIR/ohmyposh"
ALADIR="$CONFDIR/alacritty"
BAKDIR="$HOME/backups"

# Initialize directories
init_dirs() {
  echo -e "$CNT - Initializing directories..."
  mkdir -p $CONFDIR
  mkdir -p $BAKDIR
  mkdir -p $OMPDIR
  mkdir -p $ALADIR
}

# Backup and create symlink
backup_and_link() {
  local source_path=$1
  local target_path=$2
  local backup_name=$3

  if [ -e "$target_path" ]; then
    TIMESTAMP=$(date +%Y%m%d%H%M)
    echo -e "$CWR - Backup and remove existing $backup_name..."
    cp -rL "$target_path" "$BAKDIR/$backup_name.bak.$TIMESTAMP"
    rm -rf "$target_path"
  fi

  echo -e "$CNT - Creating symlink from $source_path to $target_path..."
  ln -sT "$source_path" "$target_path"
}

# Update Git submodules
update_submodules() {
  echo -e "$CNT - Updating submodules..."
  git submodule update --init --recursive
}

# Install Oh-my-posh configuration
install_omp() {
  read -rep $'[\e[1;33mACTION\e[0m] - Do you want to install Oh-my-posh configuration? (y/n) ' -n 1 CONTINST
  if [[ $CONTINST =~ ^[Yy]$ ]]; then
    backup_and_link "$BASEDIR/ohmyposh.toml" "$OMPDIR/ohmyposh.toml" "ohmyposh.toml"
    echo -e "$CAT - Don't forget to install oh-my-posh. Run: 'curl -s https://ohmyposh.dev/install.sh | sudo bash -s'"
    echo -e "$CAT - ."
  fi
}

# Install Aliases
install_aliases() {
  read -rep $'[\e[1;33mACTION\e[0m] - Do you want to install Aliases? (y/n) ' -n 1 CONTINST
  if [[ $CONTINST =~ ^[Yy]$ ]]; then
    backup_and_link "$BASEDIR/aliases" "$HOME/.aliases" "aliases"
  fi
}

# Install Bash configuration
install_bash() {
  read -rep $'[\e[1;33mACTION\e[0m] - Do you want to install Bash configuration? (y/n) ' -n 1 CONTINST
  if [[ $CONTINST =~ ^[Yy]$ ]]; then
    backup_and_link "$BASEDIR/bashrc" "$HOME/.bashrc" "bashrc"
    backup_and_link "$BASEDIR/bash_profile" "$HOME/.bash_profile" "bash_profile"
    source $HOME/.bashrc
  fi
}

# Install Zsh configuration
install_zsh() {
  read -rep $'[\e[1;33mACTION\e[0m] - Do you want to install Zsh configuration? (y/n) ' -n 1 CONTINST
  if [[ $CONTINST =~ ^[Yy]$ ]]; then
    backup_and_link "$BASEDIR/zshrc" "$HOME/.zshrc" "zshrc"
  fi
}

# Install NeoVim configuration
install_nvim() {
  read -rep $'[\e[1;33mACTION\e[0m] - Do you want to install NeoVim configuration? (y/n) ' -n 1 CONTINST
  if [[ $CONTINST =~ ^[Yy]$ ]]; then
    backup_and_link "$NVIMDIR" "$CONFDIR/nvim" "nvim"
    echo -e "$CAT - Don't forget to install nvim."
    echo -e "$CAT - Mason (LSP/Linters/Formatters) need npm installed."
    echo -e "$CAT - Also, install rg (ripgrep) and fd (fd-find)."
    echo -e "$CAT - Open nvim and execute leader l followed by I."
  fi
}

# Install Tmux configuration
install_tmux() {
  read -rep $'[\e[1;33mACTION\e[0m] - Do you want to install Tmux configuration? (y/n) ' -n 1 CONTINST
  if [[ $CONTINST =~ ^[Yy]$ ]]; then
    backup_and_link "$TMUXDIR" "$CONFDIR/tmux" "tmux"
    tmux source "$CONFDIR/tmux/tmux.conf"
    echo -e "$CAT - Don't forget to install tpm by running:"
    echo -e "$CAT - git clone https://github.com/tmux-plugins/tpm $TMUXDIR/plugins/tpm"
    echo -e "$CAT - Open a tmux session and press 'prefix + I' to fetch the plugins."
  fi
}

# Install Alacritty configuration
install_alacritty() {
  read -rep $'[\e[1;33mACTION\e[0m] - Do you want to install Alacritty configuration? (y/n) ' -n 1 CONTINST
  if [[ $CONTINST =~ ^[Yy]$ ]]; then
    backup_and_link "$BASEDIR/alacritty" "$CONFDIR/alacritty" "alacritty"
  fi
}

# Install Git configuration
install_git() {
  read -rep $'[\e[1;33mACTION\e[0m] - Do you want to install Git configuration? (y/n) ' -n 1 CONTINST
  if [[ $CONTINST =~ ^[Yy]$ ]]; then
    backup_and_link "$BASEDIR/gitconfig" "$HOME/.gitconfig" "gitconfig"
  fi
}

# Main script execution
echo -e "$CNT - Initializing parameters and updating submodules..."
init_dirs
update_submodules

install_omp
install_aliases
install_bash
install_zsh
install_nvim
install_tmux
install_alacritty
install_git

echo -e "$COK - Done!"

read -rep $'[\e[1;33mACTION\e[0m] - Would you like some additional reminders? (y/n) ' -n 1 CONTINST
if [[ $CONTINST =~ ^[yY]$ ]]; then
  echo -e "$CAT - Install a Nerd Font"
  echo -e "$CAT - Install fzf, ripgrep, fd-find, and npm"
  echo -e "$CAT - Install oh-my-posh"
  echo -e "$CAT - For Hyprland: Run 'install-hyprland.sh' in $BASEDIR/hyprland/"
fi
