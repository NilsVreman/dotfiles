return {
  "ahmedkhalf/project.nvim",
  opts = {
    manual_mode = false,
  },
  keys = {
    { "<leader>pa", "<Cmd>AddProject<CR>", desc = "Add current dir to Projects" },
    { "<leader>pr", "<Cmd>ProjectRoot<CR>", desc = "Change Project root to the current buffers" },
  },
}
