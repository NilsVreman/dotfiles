vim.keymap.set("n", "<leader>pv", vim.cmd.Ex)       -- Go back to netrw mode

---- Movement
-- visual
vim.keymap.set("v", "J", ":m '>+1<CR>gv=gv")        -- Move visual marked up and down
vim.keymap.set("v", "K", ":m '<-2<CR>gv=gv")

-- normal
vim.keymap.set("n", "J", "maJ`a")
vim.keymap.set("n", "n", "nzzzv")                   -- Keep search in middle
vim.keymap.set("n", "N", "Nzzzv")                   -- Keep search in middle

vim.keymap.set({"n", "v"}, "H", "^")
vim.keymap.set({"n", "v"}, "L", "$")
vim.keymap.set({"n", "v"}, "M", "%")
vim.keymap.set("n", "<leader>m", "ma%mb%x`bhx`a")    -- Remove inner parenthesis

---- Copy-Pasting
vim.keymap.set({"n", "v"}, "<leader>y", "\"+y")     -- Copy to clipboard using <leader>y
vim.keymap.set("x", "<leader>p", [["_dP]])          -- Paste while pushing pasted value to void buf

vim.keymap.set("n", "Y", "Vy")

---- Buffers and windows
vim.keymap.set("n", "gp", ":bp<CR>")
vim.keymap.set("n", "gn", ":bn<CR>")
vim.keymap.set("n", "gl", ":ls<CR>")
vim.keymap.set("n", "gc", ":bp<bar>sp<bar>bn<bar>bd<CR>")

---- Insert
vim.keymap.set("n", "<leader>o", "mzo<Esc>`zh")
vim.keymap.set("n", "<leader>O", "mzO<Esc>`zh")

---- Additional
vim.keymap.set("n", "Q", "<nop>")

vim.keymap.set("n", "<leader>n", ":noh<CR>")

-- Close quickfix list
vim.keymap.set("n", "<leader>vq", ":cclose<CR>")

-- change all occurrences under cursor
vim.keymap.set("n", "<leader>s", [[:%s/\<<C-r><C-w>\>/<C-r><C-w>/gI<Left><Left><Left>]])

-- Open terminal in split window
vim.keymap.set("n", "<leader>th", ":sp<CR><C-w>j:term<CR>A")
vim.keymap.set("n", "<leader>tv", ":vsp<CR>:term<CR>A")
