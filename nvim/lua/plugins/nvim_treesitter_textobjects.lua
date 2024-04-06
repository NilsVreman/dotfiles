return {
  "nvim-treesitter/nvim-treesitter-textobjects",
  opts = {
    textobjects = {
      select = {
        enable = true,
        lookahead = true,
        keymaps = {
          -- functions
          ["af"] = { query = "@function.outer", desc = "Select outer part of a function/method definition" },
          ["if"] = { query = "@function.inner", desc = "Select inner part of a function/method definition" },

          -- classes
          ["ac"] = { query = "@class.outer", desc = "Select outer part of a class" },
          ["ic"] = { query = "@class.inner", desc = "Select inner part of a class" },

          -- loop, block, etc, are mapped to ["io"] and ["ao"] by default
        },
      },
    },
  },
}
