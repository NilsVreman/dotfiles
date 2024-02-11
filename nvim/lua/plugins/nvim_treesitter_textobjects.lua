return {
  "nvim-treesitter/nvim-treesitter-textobjects",
  opts = {
    textobjects = {
      select = {
        enable = true,
        lookahead = true,
        keymaps = {
          ["af"] = { query = "@function.outer", desc = "Select outer part of a function/method definition" },
          ["if"] = { query = "@function.inner", desc = "Select inner part of a function/method definition" },
          ["ac"] = { query = "@class.outer", desc = "Select outer part of a class" },
          ["ic"] = { query = "@class.inner", desc = "Select inner part of a class" },
          -- loop, block, etc, are mapped to ["io"] and ["ao"] by default
        },
      },
      swap = {
        enable = true,
        swap_next = {
          ["<leader>sna"] = "@parameter.inner",
          ["<leader>snf"] = "@function.outer",
        },
        swap_previous = {
          ["<leader>spa"] = "@parameter.inner",
          ["<leader>spf"] = "@function.outer",
        },
      },
    },
  },
}
