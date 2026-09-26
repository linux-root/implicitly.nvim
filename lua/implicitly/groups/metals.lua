local M = {}

M.url = "https://github.com/scalameta/nvim-metals"

---@type implicitly.HighlightsFn
function M.get(c, opts)
  -- stylua: ignore
  return {
    -- Inferred types, implicit arguments and implicit conversions, rendered
    -- inline by Metals (`showInferredType`, `showImplicitArguments`,
    -- `showImplicitConversionsAndClasses`). These are annotations, not source
    -- text -- they must recede, or toggling them on makes the buffer unreadable.
    MetalsDecoration          = { fg = c.comment, italic = true },
    MetalsDecorationLineEnd   = { fg = c.comment, italic = true },
    MetalsHint                = { fg = c.comment, italic = true },

    -- Matched to the diagnostic colors so Metals never diverges from the rest
    -- of LSP in the same buffer.
    MetalsError               = { fg = c.error },
    MetalsWarning             = { fg = c.warning },
    MetalsInfo                = { fg = c.info },
    MetalsHintVirtualText     = { fg = c.hint, italic = true },

    -- Worksheet (`.sc`) evaluation output, shown at end of line.
    MetalsWorksheet           = { fg = c.teal, bg = c.bg_highlight, italic = true },

    -- :MetalsDoctor and the tree view use the float/sidebar palette.
    MetalsDoctorHeading       = { fg = c.purple, bold = true },
    MetalsDoctorSubHeading    = { fg = c.blue1 },
    MetalsDoctorError         = { fg = c.error },
    MetalsDoctorWarning       = { fg = c.warning },
    MetalsDoctorSuccess       = { fg = c.green },
    MetalsTreeViewGuide       = { fg = c.fg_gutter },
    MetalsTreeViewLabel       = { fg = c.fg },
    MetalsTreeViewDescription = { fg = c.comment },

    -- Build/compile status.
    MetalsStatus              = { fg = c.fg_dark, bg = c.bg_statusline },
    MetalsRunnable            = { fg = c.green },
    MetalsTestSuccess         = { fg = c.green },
    MetalsTestFailure         = { fg = c.error },
  }
end

return M
