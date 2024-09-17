return {
  "stevearc/conform.nvim",
  opts = {
    formatters_by_ft = {
      javascript = { "prettier" },
      typescript = { "prettier" },
      vue = { "prettier" },
      javascriptreact = { "prettier" },
      typescriptreact = { "prettier" },
      markdown = { "prettier" },
      json = { "prettier" },
      yaml = { "prettier" },
      css = { "prettier" },
      html = { "prettier" },
      graphql = { "prettier" },
      lua = { "stylua" },
      python = { "black", "isort" },
    },
  },
}
