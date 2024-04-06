return {
  "williamboman/mason.nvim",
  opts = function(_, opts)
    -- formatters
    table.insert(opts.ensure_installed, "prettier")
    table.insert(opts.ensure_installed, "prettierd")

    -- linters
    table.insert(opts.ensure_installed, "eslint_d")
  end,
}
