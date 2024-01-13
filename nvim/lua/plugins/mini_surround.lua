return {
  "echasnovski/mini.surround",
  opts = {
    highlight_duration = 1000,
    mappings = {
      add = "msa", -- Add surrounding in Normal and Visual modes
      delete = "msd", -- new_text surrounding
      find = "msf", -- Find surrounding (to the right)
      find_left = "msF", -- Find surrounding (to the left)
      highlight = "msh", -- Highlight surrounding
      replace = "msr", -- Replace surrounding
      update_n_lines = "msn", -- Update `n_lines`
    },
  },
}
