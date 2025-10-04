return {
  "mason-org/mason.nvim",
  opts_extend = { "ensure_installed" },
  opts = {
    ensure_installed = {
      -- formatters
      "prettierd",
      "ruff",
      -- linters
      "eslint_d",
      "mypy",
    },
  },
}
