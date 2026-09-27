local Util = require("implicitly.util")

local M = {}

---@type string[]
M.styles = { "phosphor", "ayu" }

---@param opts? implicitly.Config
function M.setup(opts)
  opts = require("implicitly.config").extend(opts)

  local ok, palette = pcall(Util.mod, "implicitly.palette." .. opts.style)
  if not ok then
    error(("implicitly: unknown style %q (expected one of: %s)")
      :format(opts.style, table.concat(M.styles, ", ")))
  end

  ---@class ColorScheme: Palette
  local colors = vim.deepcopy(palette)

  Util.bg = colors.bg
  Util.fg = colors.fg

  colors.none = "NONE"

  colors.diff = {
    add = colors.diff_add,
    delete = colors.diff_delete,
    change = colors.diff_change,
    text = colors.diff_text,
  }

  colors.git.ignore = colors.dark3
  colors.black = Util.blend_bg(colors.bg, 0.8, "#000000")
  colors.border_highlight = colors.accent
  colors.border = colors.black

  -- Popups and statusline always get a dark background
  colors.bg_popup = colors.bg_dark
  colors.bg_statusline = colors.bg_dark

  -- Sidebar and Floats are configurable
  colors.bg_sidebar = opts.styles.sidebars == "transparent" and colors.none
    or opts.styles.sidebars == "dark" and colors.bg_dark
    or colors.bg

  colors.bg_float = opts.styles.floats == "transparent" and colors.none
    or opts.styles.floats == "dark" and colors.bg_dark
    or colors.bg

  -- bg_visual and bg_search come straight from ayu (selection, findMatch)
  colors.fg_sidebar = colors.fg_dark
  colors.fg_float = colors.fg

  colors.todo = colors.cyan
  colors.warning = colors.accent
  colors.info = colors.blue
  colors.hint = colors.teal

  colors.rainbow = {
    colors.orange,
    colors.yellow,
    colors.green,
    colors.teal,
    colors.blue,
    colors.purple,
    colors.magenta,
    colors.peach,
  }

  -- stylua: ignore
  --- @class TerminalColors
  colors.terminal = {
    black          = colors.black,
    black_bright   = colors.terminal_black,
    red            = colors.red,
    red_bright     = Util.brighten(colors.red),
    green          = colors.green,
    green_bright   = Util.brighten(colors.green),
    yellow         = colors.yellow,
    yellow_bright  = Util.brighten(colors.yellow),
    blue           = colors.blue,
    blue_bright    = Util.brighten(colors.blue),
    magenta        = colors.purple,
    magenta_bright = Util.brighten(colors.purple),
    cyan           = colors.cyan,
    cyan_bright    = Util.brighten(colors.cyan),
    white          = colors.fg_dark,
    white_bright   = colors.fg,
  }

  opts.on_colors(colors)

  return colors, opts
end

return M
