source ~/.bashrc

# Path extentions

# added by Anaconda3 4.4.0 installer
#export PATH="/home/nils/anaconda3/bin:$PATH"

# added by Anaconda3 installer
#export PATH="/local/home/nilsv/anaconda3/bin:$PATH"

# Add sml path
export PATH="$HOME/SML-NJ/bin:$PATH"

# Add racket path
export PATH="$HOME/racket/bin:$PATH"

# Add mosek path
export PATH="$HOME/PhD/toolboxes/mosek/9.2/tools/platform/linux64x86/bin:$PATH"

# opam configuration
test -r /local/home/nilsv/.opam/opam-init/init.sh && . /local/home/nilsv/.opam/opam-init/init.sh > /dev/null 2> /dev/null || true
