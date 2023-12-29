local lsp_zero = require('lsp-zero')

lsp_zero.on_attach(function(_, bufnr)
    local opts = { buffer = bufnr, remap = false }

    vim.keymap.set("n", "gd", function() vim.lsp.buf.definition() end, opts)
    vim.keymap.set("n", "K", function() vim.lsp.buf.hover() end, opts)
    vim.keymap.set("n", "<leader>j", function() vim.diagnostic.goto_next() end, opts) -- next err
    vim.keymap.set("n", "<leader>k", function() vim.diagnostic.goto_prev() end, opts) -- prev err
    vim.keymap.set("n", "<leader>ha", function() vim.lsp.buf.code_action() end, opts) -- codeaction
    vim.keymap.set("n", "<leader>gr", function() vim.lsp.buf.references() end, opts)  -- ref to thi
    vim.keymap.set("n", "<leader>ra", function() vim.lsp.buf.rename() end, opts)      -- rename ref
end)

-- Language servers
require('mason').setup({})
require('mason-lspconfig').setup({
    ensure_installed = {
        'tsserver',
        'eslint',
        'rust_analyzer',
        'julials',
        'pyright',
        'lua_ls',
    },
    handlers = {
        lsp_zero.default_setup,
        lua_ls = function() -- Configure lua language server for neovim
            local lua_opts = lsp_zero.nvim_lua_ls()
            require('lspconfig').lua_ls.setup(lua_opts)
        end,
    }
})

local cmp = require('cmp')
local cmp_format = lsp_zero.cmp_format()
cmp.setup({
    formatting = cmp_format,
    mapping = cmp.mapping.preset.insert({
        ['<CR>'] = cmp.mapping.confirm({ select = false }),     -- select=false to confirm if selected
        ['<C-Space>'] = cmp.mapping.complete(),
        ['Tab'] = nil,
        ['<S-Tab>'] = nil,
    })
})

vim.diagnostic.config({
    underline = false,
    virtual_text = {
        spacing = 8,
        severity = "Error",
    },
})
