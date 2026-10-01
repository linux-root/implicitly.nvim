# implicitly

A dark Neovim colorscheme.

```
:colorscheme implicitly            -- phosphor
:colorscheme implicitly-phosphor
:colorscheme implicitly-ayu
:colorscheme implicitly-jb
```

```lua
{
  "linux-root/implicitly.nvim",
  lazy = false,
  priority = 1000,
  opts = { style = "phosphor" },
  config = function(_, opts)
    require("implicitly").setup(opts)
    vim.cmd.colorscheme("implicitly")
  end,
}
```
