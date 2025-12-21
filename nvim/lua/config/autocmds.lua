-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
-- Add any additional autocmds here

vim.api.nvim_create_autocmd("FileType", {
  pattern = "*",
  callback = function()
    local tabstop = vim.opt.tabstop:get()
    vim.opt_local.breakindentopt = "shift:" .. tabstop
  end,
})

vim.api.nvim_create_autocmd("FileType", {
  pattern = { "kitty-scrollback" },
  callback = function(ev)
    vim.keymap.set("v", "<leader><CR>", "<Plug>(KsbExecuteVisualCmd)", { buffer = ev.buf, silent = true })
    vim.keymap.set({ "n", "i" }, "<leader><CR>", "<Plug>(KsbExecuteCmd)", { buffer = ev.buf, silent = true })
    vim.keymap.set("v", "<leader>p", "<Plug>(KsbPasteVisualCmd)", { buffer = ev.buf, silent = true })
    vim.keymap.set({ "n", "i" }, "<leader>p", "<Plug>(KsbPasteCmd)", { buffer = ev.buf, silent = true })
  end,
})
