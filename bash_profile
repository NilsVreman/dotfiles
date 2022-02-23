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

# Add ARM path
export PATH="$HOME/PhD/projects/rtos-course/toolchain/ARM/bin:$PATH"

# opam configuration
test -r /local/home/nilsv/.opam/opam-init/init.sh && . /local/home/nilsv/.opam/opam-init/init.sh > /dev/null 2> /dev/null || true
