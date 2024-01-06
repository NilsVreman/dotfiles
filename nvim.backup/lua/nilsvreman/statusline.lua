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

vim.cmd("highlight NormalColour guifg=Grey88 guibg=Grey30")
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

    if count["errors"] == 0 and count["warnings"] == 0 and count["info"] == 0 and count["hints"] == 0 then
        return ""
    end

    local result = {}
    for k, v in pairs(count) do
        if v ~= 0 then
            table.insert(result, string.format("%s: %d", string.upper(string.sub(k, 1, 1)), v))
        end
    end

    return string.format("[%s]", table.concat(result, " | "))
end

function Update_Status_Line()
    return table.concat {
        update_mode_colors(),
        " %f > [%Y]",
        "%{&modified ? ' > [+]' : ''}",
        "%=",
        lsp(),
        "%=",
        " [%l/%L] (%c) | ",
        mode(),
        " "
    }
end

vim.o.statusline = "%!luaeval('Update_Status_Line()')"
