set nocompatible              " be iMproved, required
filetype off                  " required

" set the runtime path to include Vundle and initialize
set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()
    " alternatively, pass a path where Vundle should install plugins
    "call vundle#begin('~/some/path/here')
    
    " let Vundle manage Vundle, required
    Plugin 'VundleVim/Vundle.vim'
    " NERDTree
    Plugin 'scrooloose/nerdtree'
    " Delimiter Mate
    Plugin 'delimitMate.vim'
    " Track the engine.
    Plugin 'SirVer/ultisnips'
    " Snippets are separated from the engine. Add this if you want them:
    Plugin 'honza/vim-snippets'
    " Colorschemes to try out
    Plugin 'morhetz/gruvbox'
    " Plugin 'arcticicestudio/nord-vim'
    " Plugin 'mhartington/oceanic-next'
    " Plugin 'altercation/vim-colors-solarized'
    " Plugin 'tomasiser/vim-code-dark'

" All of your Plugins must be added before the following line
call vundle#end()            " required
filetype plugin indent on    " required

" To ignore plugin indent changes, instead use:
"filetype plugin on
"
" Brief help
" :PluginList       - lists configured plugins
" :PluginInstall    - installs plugins; append `!` to update or just :PluginUpdate
" :PluginSearch foo - searches for foo; append `!` to refresh local cache
" :PluginClean      - confirms removal of unused plugins; append `!` to auto-approve removal
"
" see :h vundle for more details or wiki for FAQ
" Put your non-Plugin stuff after this line
"
" UltiSnips
" Trigger configuration. Do not use <tab> if you use https://github.com/Valloric/YouCompleteMe.
let g:UltiSnipsExpandTrigger="<tab>"
let g:UltiSnipsJumpForwardTrigger="<c-j>"
let g:UltiSnipsJumpBackwardTrigger="<c-k>"
let g:UltiSnipsSnippetsDir="~/.vim/snippets/UltiSnips"
let g:ultisnips_python_style = "google"
" To be able to run snippets to newly created vim files
let g:tex_flavor="latex" 
"let g:UltiSnipsSnippetDirectories = ['snippets/UltiSnips']
" Adds my snippets to runtimepath
set runtimepath+=~/.vim/snippets/UltiSnips
" If you want :UltiSnipsEdit to split your window.
let g:UltiSnipsEditSplit="vertical"

" Has to do with delimitMate
" -------------------------------------------
let delimitMate_expand_cr = 1

" Has to do with NERDTree
" -------------------------------------------
autocmd VimEnter * NERDTree
autocmd VimEnter * wincmd p

" Allows nerdtree to open mirrors in new tabs
autocmd BufWinEnter * NERDTreeMirror
"
" Close NERDTree if it is the last open buffer
autocmd WinEnter * call s:CloseIfOnlyNerdTreeLeft()

" Close all open buffers on entering a window if the only
" buffer that's left is the NERDTree buffer
function! s:CloseIfOnlyNerdTreeLeft()
    if exists("t:NERDTreeBufName")
        if bufwinnr(t:NERDTreeBufName) != -1
            if winnr("$") == 1
                q
            endif
        endif
    endif
endfunction

" -------------------------------------------
"  Colorscheme
set termguicolors                     " For full support of colours, uncomment this line and comment next
" set t_Co=256
set background=dark
let g:gruvbox_contrast_dark='hard' | colorscheme gruvbox
" colorscheme nord
" colorscheme OceanicNext
" colorscheme solarized
" colorscheme codedark
syntax on

" -------------------------------------------
"  Tabs
set tabstop=4
set shiftwidth=4
set expandtab
set autoindent

" -------------------------------------------
"  Line break
set wrap
set linebreak
set breakindent

" -------------------------------------------
"  Line numbering
set relativenumber
"  Lines above and below line
set scrolloff=3 

" -------------------------------------------
"  Smart Searches
set ignorecase
set smartcase
set incsearch

" -------------------------------------------
"  Commandline completion
set wildmode=longest,list,full

" -------------------------------------------
"  Has to do with line highlighting
"hi CursorLine guifg=NONE guibg=#2d3c45 ctermbg=237 gui=NONE term=NONE cterm=NONE
set cursorline

" -------------------------------------------
" KEY MAPPINGS
"
" Remap Leader to space
let mapleader = "\<Space>"

" Execute python code
autocmd! FileType python nnoremap <leader>p :exec '!python3.6' shellescape(@%, 1)<cr>

" Execute Julia code
autocmd! FileType julia nnoremap <leader>j :exec '!julia-1.1' shellescape(@%, 1)<cr>

" Run Makefile in folder
nnoremap <Leader>m :!make<CR>

" Has to do with line highlighting
nnoremap <Leader>c :set cursorline!<CR>

" Join two lines
nnoremap <Leader>j J

" de-tab and tab remap
" for command mode
nnoremap <S-Tab> <<
nnoremap <Tab> >>
" for visual mode
vnoremap <Tab> >gv
vnoremap <S-tab> <gv

" New line from marker NOT INSERTING
nmap <CR> i<CR><Esc>l
" New line above or below line
nmap <leader>o o<Esc>k
nmap <leader>O O<Esc>j

" Move to beginning and end of line
noremap H ^
noremap L g$
noremap K 10k
noremap J 10j

" remove arrowmovement
nnoremap <up> <nop>
nnoremap <down> <nop>
nnoremap <left> <nop>
nnoremap <right> <nop>
vnoremap <left> h
vnoremap <right> l
vnoremap <up> k
vnoremap <down> j

" Remove highlighting when pressing space+n after search
nnoremap <leader>n :noh<CR>

" Add spell check for certain files
" Spell check is currently positioned in ~/.vim/after/ftplugin/type.vim
