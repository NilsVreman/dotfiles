local builtin = require('telescope.builtin')
vim.keymap.set('n', '<leader>pf', builtin.find_files, {})   -- Find PROJECT FILES (PF)
vim.keymap.set('n', '<leader>pg', builtin.git_files, {})    -- Find PROJECT GIT FILES (PG)
vim.keymap.set('n', '<leader>ps', function()                -- Find PROJECT STRING (PS)
	builtin.grep_string({ search = vim.fn.input("Grep > ") }); -- NOTE: This requires ripgrep
end)
vim.keymap.set('n', 'gl', builtin.buffers, {})              -- Open buffer list

local actions = require("telescope.actions")
require("telescope").setup{
    defaults = {
        mappings = {
            i = {
                ["<Esc>"] = actions.close
            },
        },
    }
}
