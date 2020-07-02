set nocompatible              " be iMproved, required
filetype off                  " required

" set the runtime path to include Vundle and initialize
set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()
    " alternatively, pass a path where Vundle should install plugins
    "call vundle#begin('~/some/path/here')
    
    " let Vundle manage Vundle, required
    Plugin 'VundleVim/Vundle.vim'
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
" -------------------------------------------
" UltiSnips
" Trigger configuration. Do not use <tab> if you use https://github.com/Valloric/YouCompleteMe.
let g:UltiSnipsExpandTrigger="<tab>"
let g:UltiSnipsJumpForwardTrigger="<c-j>"
let g:UltiSnipsJumpBackwardTrigger="<c-k>"
let g:ultisnips_python_style = "google"

" To be able to run snippets to newly created vim files
let g:tex_flavor="latex" 

" If you want :UltiSnipsEdit to split your window.
let g:UltiSnipsEditSplit="vertical"

" Has to do with delimitMate
" -------------------------------------------
let delimitMate_expand_cr = 1

" -------------------------------------------
" Netrw

" Control left/right split
let g:netrw_altv = 1

" absolute width of netrw window
let g:netrw_winsize = 10

" do not display info on the top of window
let g:netrw_banner = 0

" tree-view
let g:netrw_liststyle = 3

" sort is affecting only: directories on the top, files below
let g:netrw_sort_sequence = '[\/]$,*'

" use the previous window to open file
let g:netrw_browse_split = 4

" Remove hidden buffers
autocmd FileType netrw setl bufhidden=wipe

" Toggle Lexplore with Leader-E
let g:NetrwIsOpen=0
function! ToggleNetrw()
    if g:NetrwIsOpen
        let i = bufnr("$")
        while (i >= 1)
            if (getbufvar(i, "&filetype") == "netrw")
                silent exe "bwipeout " . i
            endif
            let i-=1
        endwhile
        let g:NetrwIsOpen=0
    else
        let g:NetrwIsOpen=1
        silent Lexplore
    endif
endfunction
" Keymapping set further down !!!!

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
set scrolloff=5 

" -------------------------------------------
"  Smart Searches
set ignorecase
set smartcase
set incsearch

" -------------------------------------------
"  Commandline completion
set wildmode=longest,list,full

" -------------------------------------------
"  Highlighting
set cursorline

" -------------------------------------------
"  Statusline
set statusline+=%F
set laststatus=2

" -------------------------------------------
" KEY MAPPINGS
"
" Remap Leader to space
let mapleader = "\<Space>"

" Toggle netrw menu
noremap <silent> <Leader>e :call ToggleNetrw()<CR>

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

" BUFFER KEYMAPPINGS
" Move to the previous buffer with "gp"
nnoremap gp :bp<CR>

" Move to the next buffer with "gn"
nnoremap gn :bn<CR>

" List all possible buffers with "gl"
nnoremap gl :ls<CR>

" List all possible buffers with "gb" and accept a new buffer argument [1]
nnoremap gb :ls<CR>:b
