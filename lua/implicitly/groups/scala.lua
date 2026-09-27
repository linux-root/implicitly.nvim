local M = {}

M.url = "https://github.com/tree-sitter/tree-sitter-scala"

-- Only what the generic mapping gets wrong for Scala.
--
-- ayu's own role assignments already cover most of it -- keywords purple, types
-- blue, operators salmon -- so groups that would merely restate the generic
-- result are left out rather than written down. What remains is the Scala
-- grammar disagreeing with the generic mapping (imports, annotations, string
-- interpolation), and the Metals semantic tokens nothing else knows about.

---@type implicitly.HighlightsFn
function M.get(c, opts)
  -- stylua: ignore
  return {
    -- The grammar routes these through Conditional/Repeat/Exception, which skip
    -- the keyword style; in Scala they are keywords like any other.
    ["@keyword.conditional.scala"]       = { fg = c.purple, style = opts.styles.keywords },
    ["@keyword.repeat.scala"]            = { fg = c.purple, style = opts.styles.keywords },
    ["@keyword.exception.scala"]         = { fg = c.purple, style = opts.styles.keywords },
    ["@keyword.operator.scala"]          = { fg = c.purple, style = opts.styles.keywords },
    -- `import` is Include -> PreProc, which is the tag color. It is a keyword.
    ["@keyword.import.scala"]            = { fg = c.purple },

    ["@attribute.scala"]                 = { fg = c.peach }, -- @tailrec, @main
    ["@character.special.scala"]         = { fg = c.magenta }, -- the $ in s"$x"
    ["@module.scala"]                    = { fg = c.fg_dark }, -- package paths recede

    -- Metals semantic tokens. Verified against `:Inspect` on real code -- the
    -- set Metals actually emits is the source of truth, and a group for a token
    -- it never sends is just dead weight.
    ["@lsp.type.interface.scala"]        = { fg = c.blue }, -- traits
    ["@lsp.type.namespace.scala"]        = { fg = c.fg_dark },
    ["@lsp.type.typeParameter.scala"]    = { fg = c.blue, italic = true },
    ["@lsp.typemod.class.abstract.scala"] = { fg = c.blue, italic = true },

    -- `implicit` is a real Metals modifier: anything the compiler supplied
    -- rather than something you wrote goes italic.
    ["@lsp.mod.implicit.scala"]          = { italic = true },
    ["@lsp.typemod.variable.implicit.scala"] = { fg = c.teal, italic = true },
    ["@lsp.typemod.method.implicit.scala"]   = { fg = c.teal, italic = true },
    ["@lsp.typemod.variable.mutable.scala"]  = { underline = true }, -- vals are the norm
  }
end

return M
