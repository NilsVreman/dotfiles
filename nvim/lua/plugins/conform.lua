return {
  "stevearc/conform.nvim",
  opts = {
    formatters_by_ft = {
      javascript = { "prettierd" },
      typescript = { "prettierd" },
      vue = { "prettierd" },
      javascriptreact = { "prettierd" },
      typescriptreact = { "prettierd" },
      markdown = { "prettierd" },
      json = { "prettierd" },
      yaml = { "prettierd" },
      css = { "prettierd" },
      html = { "prettierd" },
      graphql = { "prettierd" },
      lua = { "stylua" },
      python = { "ruff_format", "ruff_organize_imports", lsp_format = "first" },
    },
  },
}
