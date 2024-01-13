return {
  "rcarriga/nvim-notify",
  opts = {
    timeout = 1000, -- NOTE: don't know why this doesn't work
  },
  keys = {
    { "<leader>un", false },
    {
      "<leader>n",
      function()
        require("notify").dismiss({ silent = true, pending = true })
      end,
      mode = { "n", "v" },
      desc = "Dismiss all Notifications",
    },
  },
}
