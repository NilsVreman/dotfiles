-- MOST USEFUL COMMANDS:
--  - <leader>/:  grep in files
--  - <leader>fr: find recent files
--  - <leader>ff: find files
--  - <leader>sd: search diagnostics in current buffer
--  - <leader>sD: search diagnostics in workspace
--  - <leader>sh: search neovim help pages
--
-- USEFUL COMMANDS:
--  - <leader>sM: search man pages
--  - <leader>sm: search marks
--  - <leader>sk: search for keybinding
--  - <leader>ss: search for symbols in current buffer
--  - <leader>sS: search for symbols in workspace

return {
  "nvim-telescope/telescope.nvim",
  keys = {
    -- deletes
    { "<leader><space>", false },
    { "<leader>fg", false },
    { "<leader>fr", false },
    -- find
    { "<leader>fg", "<cmd>Telescope live_grep<cr>", desc = "Grep (cwd)" },
    { "<leader>:", "<cmd>Telescope command_history<cr>", desc = "Command History" },
    {
      "<leader>fr",
      function()
        require("telescope.builtin").oldfiles({
          cwd = vim.loop.cwd(),
        })
      end,
      desc = "Recent (cwd)",
    },
    -- git
    { "<leader>gc", "<cmd>Telescope git_commits<CR>", desc = "git commits" },
    { "<leader>gs", "<cmd>Telescope git_status<CR>", desc = "git status" },
  },
}
