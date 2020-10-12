# Autoloading packages
try
    @eval using Revise
    # Turn on Revise's automatic-evaluation behavior
    Revise.async_steal_repl_backend()
    
catch err
    @warn "Could not load startup packages."
end

# Environments
ENV["EDITOR"] = "vim"
ENV["JULIA_NUM_THREADS"] = 6
