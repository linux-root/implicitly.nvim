local Config = require("implicitly.config")
local Util = require("implicitly.util")

local M = {}

-- stylua: ignore
M.plugins = {
  ["blink.cmp"]                     = "blink",
  ["bufferline.nvim"]               = "bufferline",
  ["flash.nvim"]                    = "flash",
  ["fzf-lua"]                       = "fzf",
  ["gitsigns.nvim"]                 = "gitsigns",
  ["grug-far.nvim"]                 = "grug-far",
  ["lazy.nvim"]                     = "lazy",
  ["mini.icons"]                    = "mini_icons",
  ["neotest"]                       = "neotest",
  ["neotest-scala"]                 = "neotest",
  ["noice.nvim"]                    = "noice",
  ["nvim-dap"]                      = "dap",
  ["nvim-dap-ui"]                   = "dap",
  ["nvim-metals"]                   = "metals",
  ["nvim-notify"]                   = "notify",
  ["sidekick.nvim"]                 = "sidekick",
  ["snacks.nvim"]                   = "snacks",
  ["trouble.nvim"]                  = "trouble",
  ["which-key.nvim"]                = "which-key",
}

local me = debug.getinfo(1, "S").source:sub(2)
me = vim.fn.fnamemodify(me, ":h")

-- The cache keys on the resolved colors and the plugin list, so editing a group
-- file leaves stale highlights in place until the cache is cleared by hand --
-- a trap when you are the one editing the theme, since the version string that
-- would otherwise turn the cache over only moves on a release. Fold the newest
-- source mtime into the cache inputs so edits invalidate it themselves.
local function source_stamp()
  local uv = vim.uv or vim.loop
  local newest = 0
  local root = vim.fn.fnamemodify(me, ":h")
  for _, dir in ipairs({ me, root, root .. "/palette", root .. "/colors" }) do
    for _, file in ipairs(vim.fn.glob(dir .. "/*.lua", false, true)) do
      local stat = uv.fs_stat(file)
      newest = math.max(newest, stat and stat.mtime.sec or 0)
    end
  end
  return newest
end

function M.get_group(name)
  ---@type {get: implicitly.HighlightsFn, url: string}
  return Util.mod("implicitly.groups." .. name)
end

---@param colors ColorScheme
---@param opts implicitly.Config
function M.get(name, colors, opts)
  local mod = M.get_group(name)
  return mod.get(colors, opts)
end

---@param colors ColorScheme
---@param opts implicitly.Config
function M.setup(colors, opts)
  local groups = {
    base = true,
    kinds = true,
    scala = true,
    semantic_tokens = true,
    treesitter = true,
  }

  if opts.plugins.all then
    for _, group in pairs(M.plugins) do
      groups[group] = true
    end
  elseif opts.plugins.auto and package.loaded.lazy then
    local plugins = require("lazy.core.config").plugins
    for plugin, group in pairs(M.plugins) do
      if plugins[plugin] then
        groups[group] = true
      end
    end
  end

  -- manually enable/disable plugins
  for plugin, group in pairs(M.plugins) do
    local use = opts.plugins[group]
    use = use == nil and opts.plugins[plugin] or use
    if use ~= nil then
      if type(use) == "table" then
        use = use.enabled
      end
      groups[group] = use or nil
    end
  end

  local names = vim.tbl_keys(groups)
  table.sort(names)

  local cache_key = opts.style
  local cache = opts.cache and Util.cache.read(cache_key)

  local inputs = {
    colors = colors,
    plugins = names,
    version = Config.version,
    sources = source_stamp(),
    opts = { transparent = opts.transparent, styles = opts.styles, dim_inactive = opts.dim_inactive },
  }

  local ret = cache and vim.deep_equal(inputs, cache.inputs) and cache.groups

  if not ret then
    ret = {}
    -- merge highlights
    for group in pairs(groups) do
      for k, v in pairs(M.get(group, colors, opts)) do
        ret[k] = v
      end
    end
    -- After the merge, not as one more group: pairs() has no order, and these
    -- have to win over base, treesitter and scala.
    if opts.style == "jb" then
      for k, v in pairs(M.get("jb", colors, opts)) do
        ret[k] = v
      end
    end
    Util.resolve(ret)
    if opts.cache then
      Util.cache.write(cache_key, { groups = ret, inputs = inputs })
    end
  end
  opts.on_highlights(ret, colors)

  return ret, groups
end

return M
