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
    Plugin 'JuliaEditorSupport/julia-vim'

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

" -------------------------------------------
" DelimitMate
let delimitMate_expand_cr = 1

" -------------------------------------------
"  Julia-Vim

" Blockwise movement = false
let g:julia_blocks = 0

" Spellchecking
let g:julia_spellcheck_docstrings = 0
let g:julia_spellcheck_comments = 0

" unicode tabbing
let g:latex_to_unicode_suggestions = 0
let g:latex_to_unicode_tab = 0

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
"  Highlighting
" Highlight misspelled words
hi SpellBad guibg=#afaf00 guifg=black

" Highlight currently marked item
" NOTE: IncSearch sets reverse automatically -> bg colours are fg and other way around!
hi IncSearch guifg=#ff0000 guibg=black

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
set textwidth=80

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
set wildignorecase

" -------------------------------------------
"  Highlighting
set cursorline

" -------------------------------------------
"  Statusline
let g:currentmode = { 'n': 'NORMAL', 'v': 'VISUAL', 'V': 'V.LINE', "\<C-V>": 'V.BLOCK', 's': 'SELECT', 'S': 'S.LINE', "\<C-S>": 'S.BLOCK', 'i': 'INSERT', 'R': 'REPLACE', 'c': 'COMMAND', 'r': 'PROMPT', 'r?': 'CONFIRM'}
let g:modegroups = { 'n': 'NRM', 'v': 'VIS', 'V': 'VIS', "\<C-V>": 'VIS', 's': 'OTH', 'S': 'OTH', "\<C-S>": 'OTH', 'i': 'INS', 'R': 'REP', 'c': 'CMD', 'r': 'OTH', 'r?': 'OTH'}

function! Modetheme(group)
    if g:modegroups[mode()]==a:group
        let g:colthm = g:currentmode[mode()]
        let g:lineModes = g:colthm
        return " <".g:lineModes."> "
    else
        return ''
    endif
endfunction

set statusline=                             " Init
set statusline+=[%{expand('%:p:h:t')}/%t]%* " finds parent directory and the current file name
set statusline+=\ >\ %*                     " Arrow
set statusline+=[%Y]\ >\ %*                 " File type 
set statusline+=%n%*                        " Buffer Number
set statusline+=\ %7*%m%*                   " Modified file flag"
set statusline+=%=                          " Switch to right
set statusline+=[%l/%L]\ (%v)\ %*           " Current Line / Total # lines + (virtual column number)
set statusline+=%1*%{(Modetheme('INS'))}%*  " Color 'USER1"
set statusline+=%2*%{(Modetheme('NRM'))}%*  " Color 'USER2"
set statusline+=%3*%{(Modetheme('CMD'))}%*  " Color 'USER3"
set statusline+=%4*%{(Modetheme('REP'))}%*  " Color 'USER4"
set statusline+=%5*%{(Modetheme('VIS'))}%*  " Color 'USER5"
set statusline+=%6*%{(Modetheme('OTH'))}%*  " Color 'USER6"

"  Colours: Insert, Normal, Command, Replace, Visual, Other
" aquaish: 108
hi User1 guifg=Black guibg=#8ec07c
" yellowish: 214
hi User2 guifg=Black guibg=#fabd2f
" purple: 175
hi User3 guifg=Black guibg=LightCoral
" purple: 175
hi User4 guifg=Black guibg=#d3869b
" blueish: 109
hi User5 guifg=Black guibg=#83a598
"fg dark khaki colour: 250
hi User6 guifg=Black guibg=#d5c4a1
"fg light khaki colour: 223
hi User7 guifg=#ebdbb2 guibg=#504945

" Make permanently visible
set laststatus=2

" -------------------------------------------
"  Window split order
set splitright

" -------------------------------------------
" KEY MAPPINGS
"
" Remap Leader to space
let mapleader = "\<Space>"

" TOGGLES -----------------------------------

" Execute python code
autocmd! FileType python nnoremap <leader>p :exec '!python3.6' shellescape(@%, 1)<cr>

" Run Makefile in folder
nnoremap <Leader>m :!make<CR>

" Has to do with line highlighting
nnoremap <Leader>c :set cursorline!<CR>

" Remove highlighting when pressing space+n after search
nnoremap <leader>n :noh<CR>

" Add spell check
map <Leader>s :setlocal spell! spelllang=en_gb<CR>

" Toggle line wrapping
nnoremap <Leader>w :execute "set textwidth=" . (&textwidth == "0" ? "80" : "0")<CR>

" MOVEMENT ----------------------------------
"
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

" Remap increase number and decrease number
noremap <C-j> <C-x>
noremap <C-k> <C-a>

" Remap Match nearest [], (), {} on this line to its nearest counterpart
noremap M %

" -------------------------------------------
" BUFFER KEYMAPPINGS

" Move to the previous buffer with "gp"
nnoremap gp :bp<CR>

" Move to the next buffer with "gn"
nnoremap gn :bn<CR>

" List all possible buffers with "gl"
nnoremap gl :ls<CR>

" List all possible buffers with "gb" and accept a new buffer argument [1]
nnoremap gb :ls<CR>:b

" Close current buffer and open next in buffer list. 
nnoremap gd :bp<bar>sp<bar>bn<bar>bd<CR>

" -------------------------------------------
" WINDOW KEYMAPPINGS

" Vertical split
nnoremap gv :vsp 

" Horizontal split
nnoremap gh :sp 

" Moving around windows: C-w + {h, j, k, l}
