local lsp = require('lsp-zero').preset({})
---- To add when snippets are reintroduced
--local cmp_action = require('lsp-zero').cmp_action()
--['<C-n>'] = cmp_action.luasnip_jump_forward(),          -- jump in snippet back and forward
--['<C-p>'] = cmp_action.luasnip_jump_backward(),

lsp.ensure_installed({
	'tsserver',
	'eslint',
	'rust_analyzer',
	'julials',
	'pyright',
	'lua_ls',
})

local cmp = require('cmp')
local cmp_select = { behavior = cmp.SelectBehavior.Select }
local cmp_mappings = lsp.defaults.cmp_mappings({
	['<C-k>'] = cmp.mapping.select_prev_item(cmp_select),   -- iterate up and down in lsp list
	['<C-j>'] = cmp.mapping.select_next_item(cmp_select),
	['<CR>'] = cmp.mapping.confirm({ select = false }),     -- select=false to confirm if selected
	['<C-Space>'] = cmp.mapping.complete(),
})

cmp_mappings['<Tab>'] = nil
cmp_mappings['<S-Tab>'] = nil

lsp.set_preferences({
	sign_icons = { }
})

lsp.setup_nvim_cmp({
	mapping = cmp_mappings
})

lsp.on_attach(function(_, bufnr)
    local opts = { buffer = bufnr, remap = false }

    vim.keymap.set("n", "gd", function() vim.lsp.buf.definition() end, opts)
    vim.keymap.set("n", "K", function() vim.lsp.buf.hover() end, opts)
    vim.keymap.set("n", "<leader>j", function() vim.diagnostic.goto_next() end, opts) -- next err
    vim.keymap.set("n", "<leader>k", function() vim.diagnostic.goto_prev() end, opts) -- prev err
    vim.keymap.set("n", "<leader>vc", function() vim.lsp.buf.code_action() end, opts) -- codeaction
    vim.keymap.set("n", "<leader>vr", function() vim.lsp.buf.references() end, opts)  -- ref to thi
    vim.keymap.set("n", "<leader>vn", function() vim.lsp.buf.rename() end, opts)      -- rename ref
end)

-- (Optional) Configure lua language server for neovim
require('lspconfig').lua_ls.setup(lsp.nvim_lua_ls())

lsp.setup()
