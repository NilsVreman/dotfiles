return {
  "rcarriga/nvim-notify",
  opts = {
    timeout = 2000,
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
