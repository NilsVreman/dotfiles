return {
  {
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
  },
  {
    "echasnovski/mini.files",
    opts = {
      windows = {
        width_focus = 50,
        width_preview = 50,
        width_nofocus = 25,
      },
    },
    keys = {
      { "<leader>fm", false },
      { "<leader>fM", false },
      {
        "<leader>j",
        function()
          require("mini.files").open(vim.api.nvim_buf_get_name(0), true)
        end,
        desc = "Open mini.files (Directory of Current File)",
      },
      {
        "<leader>J",
        function()
          require("mini.files").open(vim.uv.cwd(), true)
        end,
        desc = "Open mini.files (cwd)",
      },
    },
  },
}
