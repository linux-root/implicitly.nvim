local config = require("implicitly.config")

local M = {}

---@param opts? implicitly.Config
function M.load(opts)
  return require("implicitly.theme").setup(opts)
end

M.setup = config.setup

return M
