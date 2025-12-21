return {
  "mikesmithgh/kitty-scrollback.nvim",
  enabled = true,
  lazy = true,
  cmd = { "KittyScrollbackGenerateKittens", "KittyScrollbackCheckHealth", "KittyScrollbackGenerateCommandLineEditing" },
  event = { "User KittyScrollbackLaunch" },
  config = function()
    require("kitty-scrollback").setup()
  end,
  keys = {
    { "<C-CR>", false }, -- Disable execute in all modes
    { "<S-CR>", false }, -- Disable paste to terminal in all modes
    -- keybindings are added as autocmds in nvim/lua/config/autocmds.lua
  },
}
