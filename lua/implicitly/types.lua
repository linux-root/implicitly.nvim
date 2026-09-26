---@class implicitly.Highlight: vim.api.keyset.highlight
---@field style? vim.api.keyset.highlight

---@alias implicitly.Highlights table<string,implicitly.Highlight|string>

---@alias implicitly.HighlightsFn fun(colors: ColorScheme, opts:implicitly.Config):implicitly.Highlights

---@class implicitly.Cache
---@field groups implicitly.Highlights
---@field inputs table
