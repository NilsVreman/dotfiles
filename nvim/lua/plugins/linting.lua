return {
  "mfussenegger/nvim-lint",
  opts = {
    linters_by_ft = {
      javascript = { "eslint_d" },
      typescript = { "eslint_d" },
      vue = { "eslint_d" },
      javascriptreact = { "eslint_d" },
      typescriptreact = { "eslint_d" },
      python = { "mypy", "pylint", "flake8" },
    },
  },
}
