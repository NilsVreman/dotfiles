-- For views, notifications, popups, etc.
return {
  "folke/noice.nvim",
  opts = {
    presets = {
      lsp_doc_border = true,
    },
    routes = {
      {
        filter = { -- Used to ignore "No information available" messages on multiple LSPs attached to same buffer
          event = "notify",
          find = "No information available",
        },
        opts = { skip = true },
      },
    },
    views = {
      hover = {
        border = { style = "rounded" },
        win_options = {
          winhighlight = "Normal:Normal,FloatBorder:FloatBorder",
        },
      },
      signature = {
        border = { style = "rounded" },
        win_options = {
          winhighlight = "Normal:Normal,FloatBorder:FloatBorder",
        },
      },
    },
  },
}
