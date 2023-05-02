local modes = {
    ["n"] = "NORMAL",
    ["no"] = "NORMAL",
    ["v"] = "VISUAL",
    ["V"] = "V.LINE",
    [""] = "V.BLOCK",
    ["s"] = "SELECT",
    ["S"] = "S.LINE",
    [""] = "S.BLOCK",
    ["i"] = "INSERT",
    ["R"] = "REPLACE",
    ["Rv"] = "V.REPLACE",
    ["c"] = "COMMAND",
    ["cv"] = "VIM.EX",
    ["ce"] = "EX",
    ["r"] = "PROMPT",
    ["rm"] = "MORE",
    ["r?"] = "CONFIRM",
    ["!"] = "SHELL",
    ["t"] = "TERMINAL"
}

local function mode()
    local current_mode = vim.api.nvim_get_mode().mode
    return string.format("%s", modes[current_mode])
end

vim.cmd("highlight NormalColour guifg=Grey85 guibg=Grey30")
vim.cmd("highlight InsertColour guifg=Black guibg=#d79921")
vim.cmd("highlight CommandColour guifg=Black guibg=LightCoral")
vim.cmd("highlight ReplaceColour guifg=Black guibg=#b16286")
vim.cmd("highlight VisualColour guifg=Black guibg=#5fafaf")
vim.cmd("highlight OtherColour guifg=Black guibg=#d5c4a1")

-- Shamefully stolen from: https://nuxsh.is-a.dev/blog/custom-nvim-statusline.html
local function update_mode_colors()
    local current_mode = vim.api.nvim_get_mode().mode
    local mode_color = ""
    if current_mode == "n" or current_mode == "no" then
        mode_color = "%#NormalColour#"
    elseif current_mode == "i" or current_mode == "ic" then
        mode_color = "%#InsertColour#"
    elseif current_mode == "v" or current_mode == "V" or current_mode == "" then
        mode_color = "%#VisualColour#"
    elseif current_mode == "R" then
        mode_color = "%#ReplaceColour#"
    elseif current_mode == "c" then
        mode_color = "%#CommandColour#"
    else
        mode_color = "%#OtherColour#"
    end
    return mode_color
end

-- Info from the lsp about the current buffer
local function lsp()
    local count = {}
    local levels = {
        errors = "Error",
        warnings = "Warn",
        info = "Info",
        hints = "Hint",
    }

    for k, level in pairs(levels) do
        count[k] = vim.tbl_count(vim.diagnostic.get(0, { severity = level }))
    end

    local errors = string.format("E: %d", count["errors"])
    local warnings = string.format("W: %d", count["warnings"])
    local hints = string.format("H: %d", count["hints"])
    local info = string.format("I: %d", count["info"])

    return string.format("[%s | %s | %s | %s]", errors, warnings, info, hints)
end

function update_status_line()
    return table.concat {
        update_mode_colors(),
        " %f > [%Y : %n]",
        "%{&modified ? ' > [+]' : ''}",
        "%=",
        lsp(),
        " | [%l/%L] (%c) | ",
        mode(),
        " "
    }
end

vim.o.statusline = "%!luaeval('update_status_line()')"
