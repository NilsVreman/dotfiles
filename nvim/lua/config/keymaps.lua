-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here
--
local Util = require("lazyvim.util")

-- Formatting
vim.keymap.set({ "n", "v" }, "==", function()
  Util.format({ force = true })
end, { desc = "Format" })

-- Terminal
vim.keymap.set("n", "<leader>tt", function()
  Util.terminal(nil, { cwd = Util.root() })
end, { desc = "Terminal (root)" })
vim.keymap.set("n", "<leader>tT", function()
  Util.terminal()
end, { desc = "Terminal (cwd)" })

-- Window splitting
vim.keymap.set("n", "<leader>sj", "<C-W>s", { desc = "Split window below", remap = true })
vim.keymap.set("n", "<leader>sl", "<C-W>v", { desc = "Split window right", remap = true })

-- deletes
vim.keymap.del("n", "<leader>ft")
