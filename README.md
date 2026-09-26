# implicitly

A dark Neovim colorscheme.

```lua
{
  "linux-root/implicitly.nvim",
  lazy = false,
  priority = 1000,
  opts = {},
  config = function(_, opts)
    require("implicitly").setup(opts)
    vim.cmd.colorscheme("implicitly")
  end,
}
```
