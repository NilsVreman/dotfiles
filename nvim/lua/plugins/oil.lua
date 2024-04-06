return {
  "stevearc/oil.nvim",
  opts = {
    default_file_explorer = false,
    columns = {
      "icon",
    },
    -- Buffer-local options
    buf_options = {
      buflisted = false,
      bufhidden = "hide",
    },
    -- Window-local options
    win_options = {
      wrap = false,
      signcolumn = "no",
      cursorcolumn = false,
      foldcolumn = "0",
      spell = false,
      list = false,
      conceallevel = 3,
      concealcursor = "nvic",
    },
    view_options = {
      -- Show files and directories that start with "."
      show_hidden = true,
    },
  },
  keys = {
    {
      "<leader>j",
      "<cmd>Oil<CR>",
      mode = { "n", "v" },
      desc = "Oil Explorer",
    },
  },
}
