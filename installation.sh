# Variables
SPATH=~/dotfiles/my-snippets
STPATH=~/.vim/bundle/vim-snippets/UltiSnips

# Symlinks

# Plugin installation for vim
vim +PluginInstall +qall &>/dev/null

# Move my-snippets to correct place
cp ${SPATH}/* ${STPATH}/
