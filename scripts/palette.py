#!/usr/bin/env python3
"""Build lua/implicitly/palette.lua from ayu dark.

The ayu values are literal and canonical -- they come from
https://github.com/ayu-theme/ayu-colors (themes/dark.yaml) and are the hexes
every ayu port uses. They are not derived here, only mapped onto the key names
the highlight groups expect.

What IS derived: the handful of keys the group files need that ayu has no
equivalent for -- intermediate greys, the dim variants, and the diff surfaces.
Those are computed in OKLCH so they sit on the same perceptual ramp as the
values around them rather than being eyeballed.

    python3 scripts/palette.py --write    # regenerate lua/implicitly/palette.lua
    python3 scripts/palette.py --check    # assert the contrast floors
    python3 scripts/palette.py            # print the table with contrast ratios
"""

import math
import sys

# --- ayu dark, verbatim -------------------------------------------------------
AYU = {
    # surfaces
    "surface_base": "#0D1017",   # ui background: sidebars, statusline, panels
    "surface_lift": "#10141C",   # editor background
    "editor_line": "#161A24",    # cursorline
    "ui_line": "#1B1F29",        # separators, gutter
    "ui_popup": "#0F131A",
    "find_match": "#4C4126",
    # text
    "editor_fg": "#BFBDB6",
    "ui_fg": "#5A6378",          # comments, inactive text
    # syntax
    "keyword": "#FF8F40",
    "func": "#FFB454",
    "entity": "#59C2FF",
    "string": "#AAD94C",
    "regexp": "#95E6CB",
    "markup": "#F07178",
    "special": "#E6C08A",
    "constant": "#D2A6FF",
    "operator": "#F29668",
    "tag": "#39BAE6",
    # signals
    "accent": "#E6B450",
    "error": "#D95757",
    "vcs_added": "#70BF56",
    "vcs_modified": "#73B8FF",
    "vcs_removed": "#F26D78",
    "selection": "#3388FF",      # applied at 25% over the editor background
}

# --- OKLab <-> sRGB, for the derived keys only --------------------------------
M1 = [[0.4122214708, 0.5363325363, 0.0514459929],
      [0.2119034982, 0.6806995451, 0.1073969566],
      [0.0883024619, 0.2817188376, 0.6299787005]]
M2 = [[0.2104542553, 0.7936177850, -0.0040720468],
      [1.9779984951, -2.4285922050, 0.4505937099],
      [0.0259040371, 0.7827717662, -0.8086757660]]
M1i = [[1, 0.3963377774, 0.2158037573],
       [1, -0.1055613458, -0.0638541728],
       [1, -0.0894841775, -1.2914855480]]
M2i = [[4.0767416621, -3.3077115913, 0.2309699292],
       [-1.2684380046, 2.6097574011, -0.3413193965],
       [-0.0041960863, -0.7034186147, 1.7076147010]]


def _mul(m, v):
    return [sum(m[i][j] * v[j] for j in range(3)) for i in range(3)]


def _to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _to_srgb(c):
    c = max(0.0, min(1.0, c))
    return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def hex_to_rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def rgb_to_hex(rgb):
    return "#" + "".join("%02x" % round(max(0, min(1, c)) * 255) for c in rgb)


def hex_to_oklch(h):
    lms = [x ** (1 / 3) if x >= 0 else -(-x) ** (1 / 3)
           for x in _mul(M1, [_to_linear(c) for c in hex_to_rgb(h)])]
    lightness, a, b = _mul(M2, lms)
    return lightness, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def _oklch_to_linear(lightness, chroma, hue):
    a = chroma * math.cos(math.radians(hue))
    b = chroma * math.sin(math.radians(hue))
    return _mul(M2i, [x ** 3 for x in _mul(M1i, [lightness, a, b])])


def oklch(lightness, chroma, hue):
    while chroma > 0.001 and not all(-0.0015 <= c <= 1.0015
                                     for c in _oklch_to_linear(lightness, chroma, hue)):
        chroma -= 0.002
    return rgb_to_hex([_to_srgb(c) for c in _oklch_to_linear(lightness, chroma, hue)])


def shift(hex_value, d_lightness, chroma_scale=1.0):
    """Move a color along the OKLCH lightness axis, keeping its hue."""
    lightness, chroma, hue = hex_to_oklch(hex_value)
    return oklch(max(0.0, min(1.0, lightness + d_lightness)), chroma * chroma_scale, hue)


def over(fg, alpha, bg):
    f, b = hex_to_rgb(fg), hex_to_rgb(bg)
    return rgb_to_hex([alpha * f[i] + (1 - alpha) * b[i] for i in range(3)])


def luminance(h):
    r, g, b = (_to_linear(c) for c in hex_to_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    hi, lo = sorted([luminance(a), luminance(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


# --- mapping onto the key names the highlight groups use ----------------------
def build():
    a = AYU
    bg = a["surface_lift"]
    p = {
        # ayu puts the editor slightly above the surrounding UI, so bg_dark
        # (sidebars, floats, statusline) is the *darker* surface.base.
        "bg": bg,
        "bg_dark": a["surface_base"],
        "bg_dark1": a["ui_popup"],
        "bg_highlight": a["editor_line"],
        "fg": a["editor_fg"],
        "fg_dark": shift(a["editor_fg"], -0.09),
        "fg_gutter": a["ui_line"],
        "comment": a["ui_fg"],
        "dark3": shift(a["ui_fg"], -0.10),
        "dark5": shift(a["ui_fg"], 0.10),
        "terminal_black": shift(a["ui_fg"], -0.14),

        "orange": a["keyword"],
        "yellow": a["func"],
        "blue": a["entity"],
        "green": a["string"],
        "teal": a["regexp"],
        "red": a["markup"],
        "purple": a["constant"],
        "magenta": a["operator"],
        "cyan": a["tag"],
        "peach": a["special"],
        "accent": a["accent"],

        # Numbered variants. The suffix is the naming the group files inherited
        # and is NOT a lightness ordering: blue1/blue5/blue6 and green1 are
        # bright foregrounds (Type, @property, accent icons), while blue7 and
        # red1 are dark surfaces. Getting this backwards makes Type unreadable.
        "blue1": a["tag"],
        "blue5": shift(a["entity"], 0.06),
        "blue6": shift(a["regexp"], 0.05),
        "blue7": shift(a["entity"], -0.42),
        "green1": a["regexp"],
        "green2": shift(a["string"], -0.20),
        "red1": a["error"],
        "magenta2": shift(a["constant"], -0.14),

        "git_add": a["vcs_added"],
        "git_change": a["vcs_modified"],
        "git_delete": a["vcs_removed"],

        "bg_visual": over(a["selection"], 0.25, bg),
        "bg_search": a["find_match"],
        "error": a["error"],
    }
    # Diff surfaces, from the vcs hues at a fixed low lightness so the three
    # stay tellable apart against a near-black ground.
    for key, src in (("diff_add", "vcs_added"), ("diff_change", "vcs_modified"),
                     ("diff_delete", "vcs_removed")):
        lightness, chroma, hue = hex_to_oklch(a[src])
        p[key] = oklch(0.315, min(chroma, 0.085), hue)
    p["diff_text"] = oklch(0.400, 0.090, hex_to_oklch(a["vcs_modified"])[2])
    return p


# Floors, calibrated to what ayu actually is -- ayu runs a lower-contrast
# comment than most themes and that is the look, so the floor sits just under
# its real value rather than pushing it brighter.
FLOORS = {"fg": 8.0, "fg_dark": 6.0, "comment": 3.0, "dark5": 4.0,
          "blue1": 5.0, "blue5": 5.0, "blue6": 5.0, "green1": 5.0}
ACCENT_FLOOR = 4.0
ACCENTS = ["red", "orange", "yellow", "green", "teal", "cyan", "blue",
           "purple", "magenta", "peach", "accent"]


def check(p):
    bad = []
    for key, floor in {**FLOORS, **{k: ACCENT_FLOOR for k in ACCENTS}}.items():
        got = contrast(p[key], p["bg"])
        if got < floor:
            bad.append(f"{key} {p[key]} contrast {got:.2f} < {floor}")
    for key in ("bg_dark", "bg_dark1"):
        if luminance(p[key]) > luminance(p["bg"]):
            bad.append(f"{key} is lighter than bg")
    for x, y in (("diff_add", "diff_change"), ("diff_add", "diff_delete"),
                 ("diff_change", "diff_delete")):
        hx, hy = hex_to_oklch(p[x])[2], hex_to_oklch(p[y])[2]
        gap = min(abs(hx - hy), 360 - abs(hx - hy))
        if gap < 40:
            bad.append(f"{x}/{y} too alike: hue gap {gap:.0f}deg")
    return bad


LUA_PATH = "lua/implicitly/palette.lua"

LAYOUT = [
    ("bg", "ayu surface.lift -- editor"),
    ("bg_dark", "ayu surface.base -- sidebars, floats, statusline"),
    ("bg_dark1", None), ("bg_highlight", None),
    ("fg", None), ("fg_dark", None), ("fg_gutter", None), ("comment", None),
    ("dark3", None), ("dark5", None), ("terminal_black", None),
    (None, None),
    ("orange", "ayu keyword hex -- used here for constants, see below"),
    ("yellow", "ayu func"), ("blue", "ayu entity"),
    ("green", "ayu string"), ("teal", "ayu regexp"), ("red", "ayu markup"),
    ("purple", "ayu constant hex -- used here for keywords"),
    ("magenta", "ayu operator"), ("cyan", "ayu tag"),
    ("peach", "ayu special"), ("accent", "ayu accent"),
    (None, None),
    ("blue1", "bright: Type, Special, accent icons"),
    ("blue5", None), ("blue6", None), ("green1", "bright: @property, @variable.member"),
    ("blue7", "dark surface"), ("red1", None), ("green2", None), ("magenta2", None),
    (None, None),
    ("bg_visual", None), ("bg_search", None), ("error", None),
    (None, None),
    ("diff_add", None), ("diff_change", None), ("diff_delete", None), ("diff_text", None),
]

HEADER = """-- Generated by scripts/palette.py -- run `python3 scripts/palette.py --write`
-- to regenerate. Don't hand-edit; edit the generator.
--
-- ayu dark, from https://github.com/ayu-theme/ayu-colors (themes/dark.yaml).
-- The ayu values are verbatim; the rest are derived to fill keys the highlight
-- groups need and ayu has no equivalent for.
--
-- One deliberate departure: ayu's keyword orange and constant purple are
-- swapped. Six of ayu's eleven accents sit inside a 63-degree warm band, with
-- keyword only 6 degrees from operator and 18 from func. Keywords are the most
-- frequent token, so that band ends up dominating the screen. Purple sits 69
-- degrees clear of anything else; constants are rare enough that the orange
-- stays pleasant there. The key names below are the ayu hex they came from.

---@class Palette
local M = {
"""


def to_lua(p):
    lines = []
    for key, note in LAYOUT:
        if key is None:
            lines.append("")
            continue
        entry = f'  {key} = "{p[key]}",'
        lines.append(f"{entry:<28}-- {note}" if note else entry)
    return HEADER + "\n".join(lines) + f'''

  git = {{
    add = "{p["git_add"]}",
    change = "{p["git_change"]}",
    delete = "{p["git_delete"]}",
  }},
}}

return M
'''


if __name__ == "__main__":
    palette = build()
    failures = check(palette)
    if "--check" in sys.argv or "--write" in sys.argv:
        for f in failures:
            print("FAIL", f)
        if failures:
            sys.exit(1)
    if "--write" in sys.argv:
        with open(LUA_PATH, "w") as fh:
            fh.write(to_lua(palette))
        print(f"wrote {LUA_PATH}")
        sys.exit(0)
    if "--check" in sys.argv:
        print(f"ok: {len(FLOORS) + len(ACCENTS)} contrast floors met (bg {palette['bg']})")
        sys.exit(0)
    width = max(len(k) for k in palette)
    for key in sorted(palette):
        print(f"{key:<{width}}  {palette[key]}  cr={contrast(palette[key], palette['bg']):5.2f}")
