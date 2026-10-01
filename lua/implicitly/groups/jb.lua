local M = {}

-- Overrides for style = "jb" only, applied after every other group file.
--
-- JetBrains colors what the IDE colors: keywords, strings, numbers, function
-- declarations, fields and annotations. Types, operators, calls, parameters
-- and punctuation stay in the default text color. The shared group files color
-- all of those, so they are put back to plain text here.

---@type implicitly.HighlightsFn
function M.get(c)
  -- stylua: ignore
  return {
    -- plain text, like the IDE
    Type                                      = { fg = c.fg },
    Operator                                  = { fg = c.fg },
    Delimiter                                 = { fg = c.fg },
    ["@type.builtin"]                         = "Type",
    ["@constructor"]                          = "Type",
    ["@lsp.type.interface"]                   = "Type",
    ["@lsp.typemod.type.defaultLibrary"]      = "Type",
    ["@lsp.typemod.typeAlias.defaultLibrary"] = "Type",
    ["@operator"]                             = "Operator",
    ["@punctuation.bracket"]                  = "Operator",
    ["@punctuation.delimiter"]                = "Operator",
    ["@function.call"]                        = { fg = c.fg },
    ["@function.method.call"]                 = "@function.call",
    ["@function.builtin"]                     = "@function.call",
    ["@variable.parameter"]                   = { fg = c.fg },
    ["@module"]                               = { fg = c.fg },
    ["@label"]                                = { fg = c.fg },

    -- LSPs send the same function/method token for a call and a declaration,
    -- and Neovim links both to @function. Defer to treesitter, which can tell
    -- them apart -- otherwise every call turns declaration blue.
    ["@lsp.type.function"]                    = {},
    ["@lsp.type.method"]                      = {},

    -- the colors JetBrains does use
    Number                                    = { fg = c.cyan },
    Boolean                                   = { fg = c.purple }, -- true/false are keywords
    Include                                   = { fg = c.purple },
    Constant                                  = { fg = c.orange, italic = true },
    PreProc                                   = { fg = c.peach }, -- annotations
    ["@constant.builtin"]                     = { fg = c.purple }, -- null, nil
    ["@variable.builtin"]                     = { fg = c.purple }, -- this, self
    ["@string.escape"]                        = { fg = c.purple },
    ["@property"]                             = { fg = c.orange }, -- fields
    ["@variable.member"]                      = { fg = c.orange },
    ["@string.documentation"]                 = { fg = c.green2, italic = true },
    ["@comment.documentation"]                = { fg = c.green2, italic = true },
    CursorLineNr                              = { fg = c.fg_dark },
    MatchParen                                = { bg = c.fg_gutter, bold = true },

    -- scala.lua colors traits and abstract classes as types
    ["@lsp.type.interface.scala"]             = "Type",
    ["@lsp.typemod.class.abstract.scala"]     = "Type",
    ["@lsp.type.typeParameter.scala"]         = { fg = c.teal },
    ["@character.special.scala"]              = { fg = c.cyan, bold = true }, -- the $ in s"$x"
  }
end

return M
