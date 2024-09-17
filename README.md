# Dotfiles

This repo holds my dotfiles. They are specific to my needs but if you are a:

- Rust,
- Python,
- Lua, or
- Bash programmer

or if you're just interested in a simple Linux-setup, you might find something useful here.

## Installation

```bash
 > sh setup-dotfiles.sh
```

This starts an interactive setup script for

1. backing up existing files/folders to `$HOME/backups/`,
2. symlinks the dotfiles, folders, and files into your home and config folder, and
3. Sources the correct files

**NOTE**: If you're also interested in setting up [`Hyprland`](https://hyprland.org/), go to the `hyprland` folder and run

```bash
 > sh install-hyprland.sh
```

## Dependencies

- `git`
- `zsh` (optional, because a similar bash-setup is also provided)
- `neovim`
- `tmux`
- `ripgrep`
- `zoxide`
- `fd-find`
- `oh-my-posh`
- `npm`

## Good to know

- For future reference: If your formatters/linters/lsps aren't automatically activating; don't forget to update `nvim/plugin/{formatting,nvim_lspconfig,linting}.lua`
