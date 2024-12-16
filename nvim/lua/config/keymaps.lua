-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here

local Util = require("lazyvim.util")

-- Deletes
vim.keymap.del("n", "<leader>ft")

-- Formatting
vim.keymap.set({ "n", "v" }, "==", function()
  Util.format({ force = true })
end, { desc = "Format" })

-- Terminal
vim.keymap.set("n", "<leader>tt", function()
  Snacks.terminal(nil, { cwd = Util.root() })
end, { desc = "Terminal (root)" })
vim.keymap.set("n", "<leader>tT", function()
  Snacks.terminal()
end, { desc = "Terminal (cwd)" })

-- Window splitting
vim.keymap.set("n", "<leader>sj", "<C-W>s", { desc = "Split window below", remap = true })
vim.keymap.set("n", "<leader>sl", "<C-W>v", { desc = "Split window right", remap = true })
vim.keymap.set("n", "<leader>wj", "<C-W>s", { desc = "Split window below", remap = true })
vim.keymap.set("n", "<leader>wl", "<C-W>v", { desc = "Split window right", remap = true })

-- Vertical movement
vim.keymap.set({ "n", "v" }, "<C-d>", "<C-d>zz", { desc = "Scroll down 1/2 page", remap = true })
vim.keymap.set({ "n", "v" }, "<C-u>", "<C-u>zz", { desc = "Scroll up 1/2 page", remap = true })
vim.keymap.set("n", "<leader>o", "m`o<Esc>``")
vim.keymap.set("n", "<leader>O", "m`O<Esc>``")
