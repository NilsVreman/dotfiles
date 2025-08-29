-- https://github.com/LazyVim/LazyVim/pull/6354#issuecomment-3202799735
return {
  "akinsho/bufferline.nvim",
  init = function()
    local bufline = require("catppuccin.groups.integrations.bufferline")
    function bufline.get()
      return bufline.get_theme()
    end
  end,
}
