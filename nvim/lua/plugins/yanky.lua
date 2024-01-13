return {
  "gbprod/yanky.nvim",
  keys = {
    { "<leader>p", false },
    {
      "<leader>y",
      function()
        require("telescope").extensions.yank_history.yank_history({})
      end,
      desc = "Open Yank History",
    },
    { ">p", false },
    { "]p", false },
    { "<p", false },
    { "[p", false },
    { ">P", false },
    { "]P", false },
    { "<P", false },
    { "[P", false },
    { "=p", false },
    { "=P", false },
  },
}
