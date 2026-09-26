local M = {}

M.url = "https://github.com/tree-sitter/tree-sitter-scala"

-- Scala carries a few things the generic treesitter mapping has no slot for, and
-- they are exactly the things that are hard to read when everything looks alike:
-- the implicit/given layer, heavy type-level code, and symbolic operators that
-- are really just method names. Those get their own colors here.

---@type implicitly.HighlightsFn
function M.get(c, opts)
  -- stylua: ignore
  return {
    -- `given`, `using`, `implicit`, `inline`, `opaque`, `transparent`, `erased`.
    -- Pink is the theme's signature color; the implicit layer is worth spotting.
    ["@keyword.scala"]                   = { fg = c.pink, style = opts.styles.keywords },
    ["@keyword.modifier.scala"]          = { fg = c.pink, style = opts.styles.keywords },
    ["@keyword.conditional.scala"]       = { fg = c.pink, style = opts.styles.keywords },
    ["@keyword.repeat.scala"]            = { fg = c.pink, style = opts.styles.keywords },
    ["@keyword.return.scala"]            = { fg = c.pink, style = opts.styles.keywords },
    ["@keyword.exception.scala"]         = { fg = c.pink, style = opts.styles.keywords },
    ["@keyword.function.scala"]          = { fg = c.magenta, style = opts.styles.functions },
    ["@keyword.import.scala"]            = { fg = c.magenta },

    -- Types do a lot of work in Scala, so they get the second seed hue rather
    -- than the generic Type color.
    ["@type.scala"]                      = { fg = c.purple },
    ["@type.definition.scala"]           = { fg = c.purple, bold = true },
    ["@constructor.scala"]               = { fg = c.teal },

    -- Symbolic methods (`<*>`, `|@|`, `:::`, `=>>`, `<:<`) are calls, not syntax.
    -- Orange separates them from the blue-ish punctuation around them.
    ["@operator.scala"]                  = { fg = c.orange },
    ["@keyword.operator.scala"]          = { fg = c.pink, style = opts.styles.keywords },
    -- string interpolation: the grammar splits the marker across two captures
    ["@punctuation.special.scala"]       = { fg = c.orange }, -- s"${x}"
    ["@character.special.scala"]         = { fg = c.orange }, -- s"$x"

    ["@function.method.scala"]           = { fg = c.blue },
    ["@function.call.scala"]             = { fg = c.blue },
    ["@variable.parameter.scala"]        = { fg = c.fg_dark },
    ["@variable.member.scala"]           = { fg = c.green1 },
    ["@attribute.scala"]                 = { fg = c.yellow }, -- @tailrec, @main
    ["@module.scala"]                    = { fg = c.fg_dark },

    -- .sbt and .sc go through the scala grammar, so they pick up the groups
    -- above as-is -- the capture suffix follows the parser, not the filetype.

    -- Metals semantic tokens. Verify these against `:Inspect` on real code --
    -- the set Metals actually emits is the source of truth, and a group for a
    -- token it never sends is just dead weight.
    ["@lsp.type.class.scala"]            = { fg = c.purple },
    ["@lsp.type.interface.scala"]        = { fg = c.purple },  -- traits
    ["@lsp.type.typeParameter.scala"]    = { fg = c.magenta, italic = true },
    ["@lsp.type.enum.scala"]             = { fg = c.purple },
    ["@lsp.type.enumMember.scala"]       = { fg = c.orange },
    ["@lsp.type.method.scala"]           = { fg = c.blue },
    ["@lsp.type.namespace.scala"]        = { fg = c.fg_dark },
    -- `implicit` is a real Metals modifier: anything the compiler supplied
    -- rather than something you wrote goes italic.
    ["@lsp.mod.implicit.scala"]          = { italic = true },
    ["@lsp.typemod.variable.implicit.scala"] = { fg = c.teal, italic = true },
    ["@lsp.typemod.method.implicit.scala"]   = { fg = c.teal, italic = true },
    ["@lsp.typemod.variable.readonly.scala"] = {}, -- vals are the norm, don't shout
    ["@lsp.typemod.variable.mutable.scala"]  = { underline = true }, -- vars are not
    ["@lsp.typemod.class.abstract.scala"]    = { fg = c.purple, italic = true },
  }
end

return M
