#!/usr/bin/env python3
"""Build the palette files under lua/implicitly/palette/.

The ayu values are literal and canonical -- they come from
https://github.com/ayu-theme/ayu-colors (themes/dark.yaml) and are the hexes
every ayu port uses. They are not derived here, only mapped onto the key names
the highlight groups expect.

What IS derived: the handful of keys the group files need that ayu has no
equivalent for -- intermediate greys, the dim variants, and the diff surfaces.
Those are computed in OKLCH so they sit on the same perceptual ramp as the
values around them rather than being eyeballed.

Three variants:

  ayu       ayu dark, values verbatim from the upstream theme.
  phosphor  green on black, the look of a phosphor CRT terminal. The three
            signature values come from hackertyper.net's own stylesheet:
            #000000 background, #00FF00 text, #3df7f7 cyan, #ff0000 red.
  jb        JetBrains Dark, values verbatim from jb.nvim's IntelliJ snapshot.

    python3 scripts/palette.py --write    # regenerate all palette files
    python3 scripts/palette.py --check    # assert the contrast floors
    python3 scripts/palette.py [variant]  # print a table with contrast ratios
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
#
# The key names are hue names inherited from the group files, and they are a
# poor fit once a second variant exists: after the keyword/constant swap,
# `purple` is whatever colors keywords and `orange` is whatever colors
# constants. In the phosphor variant that makes `purple` bright green. Renaming
# the keys to roles would touch every group file, so the names stay and the
# role each one plays is spelled out here instead:
#
#   purple  keywords        orange  constants, numbers
#   yellow  functions       blue    types, entities
#   green   strings         teal    regex
#   magenta operators       cyan    tags, preprocessor
#   peach   special chars   accent  warnings, borders
def build_ayu():
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


# --- phosphor ----------------------------------------------------------------
# hackertyper.net's stylesheet is #000000 background with #00FF00 text, plus a
# #3df7f7 cyan and a #ff0000 red. Those four are used literally; the rest of the
# ramp is generated around them at the same hue so the whole screen reads as one
# phosphor.
HT_BLACK = "#000000"
HT_GREEN = "#00FF00"
HT_CYAN = "#3df7f7"
HT_RED = "#ff0000"
PHOSPHOR_HUE = 145


def build_phosphor():
    g = lambda lightness, chroma: oklch(lightness, chroma, PHOSPHOR_HUE)
    p = {
        # The editor sits a hair above true black so floats and sidebars have
        # somewhere darker to go; at this lightness it is black to the eye.
        "bg": g(0.070, 0.020),
        "bg_dark": HT_BLACK,
        "bg_dark1": HT_BLACK,
        "bg_highlight": g(0.200, 0.050),
        "fg": g(0.800, 0.150),
        "fg_dark": g(0.700, 0.120),
        "fg_gutter": g(0.270, 0.060),
        "comment": g(0.480, 0.090),
        "dark3": g(0.380, 0.080),
        "dark5": g(0.600, 0.105),
        "terminal_black": g(0.330, 0.070),

        # Strings and constants are both frequent, so constants get a genuinely
        # different hue (amber) rather than another point on the green ramp --
        # two greens separated only by chroma read as the same color.
        "purple": HT_GREEN,                   # keywords -- the signature color
        "green": g(0.900, 0.120),             # strings
        "orange": oklch(0.840, 0.160, 88),    # constants, numbers
        "yellow": oklch(0.880, 0.170, 120),   # functions
        "blue": HT_CYAN,                      # types
        "peach": g(0.940, 0.070),             # special chars -- near-white green
        "teal": oklch(0.730, 0.100, 168),
        "magenta": oklch(0.800, 0.120, 195),  # operators
        "cyan": oklch(0.870, 0.100, 218),     # tags
        "accent": oklch(0.780, 0.150, 70),    # warnings, borders -- the one warm hue
        "red": oklch(0.680, 0.170, 25),       # markup; `error` keeps the literal #ff0000

        "blue1": HT_CYAN,
        "blue5": oklch(0.880, 0.090, 195),
        "blue6": oklch(0.930, 0.070, 180),
        "blue7": oklch(0.330, 0.070, 200),
        "green1": g(0.860, 0.130),
        "green2": g(0.620, 0.110),
        "red1": HT_RED,
        "magenta2": oklch(0.700, 0.140, 185),

        "git_add": g(0.720, 0.160),
        "git_change": oklch(0.740, 0.110, 200),
        "git_delete": oklch(0.640, 0.190, 25),

        "bg_visual": g(0.250, 0.070),
        "bg_search": oklch(0.320, 0.090, 110),
        "error": HT_RED,
    }
    for key, src_hue in (("diff_add", PHOSPHOR_HUE), ("diff_change", 200), ("diff_delete", 25)):
        p[key] = oklch(0.260, 0.075, src_hue)
    p["diff_text"] = oklch(0.360, 0.080, 200)
    return p


# --- jb ----------------------------------------------------------------------
# JetBrains Dark, from the IntelliJ snapshot in
# https://github.com/nickkadutskyi/jb.nvim (lua/jb/intellij-palette.json, the
# `dark` entries). Verbatim, keyed by the IntelliJ setting they came from.
JB = {
    "default_text_bg": "#191A1C",
    "default_text_fg": "#BCBEC4",
    "caret_row": "#1F2024",
    "line_number": "#4B5059",
    "line_number_caret": "#A1A3AB",
    "folded_bg": "#393B40",
    "folded_fg": "#868A91",
    "unused_code": "#6F737A",
    "comment": "#7A7E85",
    "doc_comment": "#5F826B",
    "keyword": "#CF8E6D",
    "string": "#6AAB73",
    "number": "#2AACB8",
    "function_decl": "#56A8F5",
    "field": "#C77DBB",
    "metadata": "#B3AE60",
    "type_parameter": "#16BAAC",
    "template_variable": "#B189F5",
    "hyperlink": "#548AF7",
    "completion_match": "#6089EF",
    "notification_bg": "#25324D",
    "warning": "#F2C55C",
    "bad_character": "#F75464",
    "error_underline": "#FA6675",
    "selection": "#214283",
    "text_search": "#114957",
    "vcs_added": "#549159",
    "vcs_modified": "#375FAD",
    "vcs_deleted": "#868A91",
    "diff_inserted": "#294436",
    "diff_changed": "#385570",
    "deleted_text": "#450505",
}


# JetBrains leaves types, operators, calls and punctuation in the default text
# color. The palette can't express "no color" for a role, so `blue` and
# `magenta` carry JetBrains' UI hues here and lua/implicitly/groups/jb.lua puts
# the syntax back to plain text.
def build_jb():
    j = JB
    bg = j["default_text_bg"]
    p = {
        "bg": bg,
        # IntelliJ's tool windows are lighter than the editor; here the
        # surrounding UI stays darker, like the other variants, so dim_inactive
        # still dims.
        "bg_dark": shift(bg, -0.025),
        "bg_dark1": shift(bg, -0.025),
        "bg_highlight": j["caret_row"],
        "fg": j["default_text_fg"],
        "fg_dark": j["line_number_caret"],
        "fg_gutter": j["folded_bg"],
        "comment": j["comment"],
        "dark3": j["line_number"],
        "dark5": j["folded_fg"],
        "terminal_black": j["unused_code"],

        "purple": j["keyword"],
        "orange": j["field"],              # constants and fields
        "yellow": j["function_decl"],
        "blue": j["hyperlink"],
        "green": j["string"],
        "cyan": j["number"],
        "teal": j["type_parameter"],
        "magenta": j["template_variable"],
        "peach": j["metadata"],            # annotations
        "accent": j["warning"],
        "red": j["bad_character"],

        "blue1": j["completion_match"],
        "blue5": shift(j["hyperlink"], 0.06),
        "blue6": shift(j["type_parameter"], 0.05),
        "blue7": j["notification_bg"],
        "green1": shift(j["string"], 0.08),
        "green2": j["doc_comment"],
        "red1": j["error_underline"],
        "magenta2": shift(j["template_variable"], -0.14),

        "git_add": j["vcs_added"],
        "git_change": j["vcs_modified"],
        "git_delete": j["vcs_deleted"],

        "bg_visual": j["selection"],
        "bg_search": j["text_search"],
        "error": j["bad_character"],

        "diff_add": j["diff_inserted"],
        "diff_change": j["notification_bg"],
        "diff_text": j["diff_changed"],
        "diff_delete": j["deleted_text"],

        # Popup borders are grey in the IDE; the warning yellow would be loud.
        "border_highlight": j["folded_bg"],
    }
    return p


VARIANTS = {"ayu": build_ayu, "phosphor": build_phosphor, "jb": build_jb}


# Floors, calibrated to what ayu actually is -- ayu runs a lower-contrast
# comment than most themes and that is the look, so the floor sits just under
# its real value rather than pushing it brighter.
FLOORS = {"fg": 8.0, "fg_dark": 6.0, "comment": 3.0, "dark5": 4.0,
          "blue1": 5.0, "blue5": 5.0, "blue6": 5.0, "green1": 5.0}
ACCENT_FLOOR = 4.0
ACCENTS = ["red", "orange", "yellow", "green", "teal", "cyan", "blue",
           "purple", "magenta", "peach", "accent"]


# Two syntax roles that land on nearly the same color are a bug you only notice
# after staring at a buffer for an hour. The floor sits just under ayu's own
# worst pair (constant vs operator, 0.039) -- upstream ayu is canonical and not
# ours to fail, but anything tighter than that is our own mistake.
MIN_ROLE_DISTANCE = 0.035
ROLE_KEYS = ["purple", "orange", "yellow", "blue", "green", "teal",
             "magenta", "cyan", "peach", "accent", "red"]


def _oklab(hex_value):
    lightness, chroma, hue = hex_to_oklch(hex_value)
    rad = math.radians(hue)
    return (lightness, chroma * math.cos(rad), chroma * math.sin(rad))


def role_distances(p):
    out = []
    for i, a in enumerate(ROLE_KEYS):
        for b in ROLE_KEYS[i + 1:]:
            pa, pb = _oklab(p[a]), _oklab(p[b])
            out.append((math.dist(pa, pb), a, b))
    return sorted(out)


def check(p):
    bad = []
    for gap, a, b in role_distances(p):
        if gap < MIN_ROLE_DISTANCE:
            bad.append(f"{a} {p[a]} and {b} {p[b]} are near-identical (gap {gap:.3f})")
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


LUA_DIR = "lua/implicitly/palette"

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
    ("border_highlight", None),
]

HEADERS = {
    "ayu": """-- Generated by scripts/palette.py -- run `python3 scripts/palette.py --write`
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
""",
    "phosphor": """-- Generated by scripts/palette.py -- run `python3 scripts/palette.py --write`
-- to regenerate. Don't hand-edit; edit the generator.
--
-- Green on black, the look of a phosphor CRT terminal. Four values are taken
-- literally from hackertyper.net's stylesheet -- #000000 background, #00FF00
-- text, #3df7f7 cyan, #ff0000 red -- and the rest of the ramp is generated
-- around them at the same hue so the screen reads as one phosphor.
--
-- The key names are hue names and they lie here: `purple` is the bright green
-- that colors keywords, `orange` is the lime on constants. See the role table
-- in scripts/palette.py.

---@class Palette
local M = {
""",
    "jb": """-- Generated by scripts/palette.py -- run `python3 scripts/palette.py --write`
-- to regenerate. Don't hand-edit; edit the generator.
--
-- JetBrains Dark, from the IntelliJ snapshot in
-- https://github.com/nickkadutskyi/jb.nvim (lua/jb/intellij-palette.json).
--
-- JetBrains leaves types, operators and calls in the default text color, which
-- a palette can't say. `blue` and `magenta` carry UI hues here, and
-- lua/implicitly/groups/jb.lua turns the syntax back to plain text. The inline
-- notes below are the ayu names the keys were laid out for; see the role table
-- in scripts/palette.py.

---@class Palette
local M = {
""",
}


def to_lua(p, variant):
    lines = []
    for key, note in LAYOUT:
        if key is None:
            lines.append("")
            continue
        if key not in p:
            continue
        entry = f'  {key} = "{p[key]}",'
        lines.append(f"{entry:<28}-- {note}" if note else entry)
    return HEADERS[variant] + "\n".join(lines) + f'''

  git = {{
    add = "{p["git_add"]}",
    change = "{p["git_change"]}",
    delete = "{p["git_delete"]}",
  }},
}}

return M
'''


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    names = args or list(VARIANTS)

    failures = {n: check(VARIANTS[n]()) for n in names}
    if "--check" in sys.argv or "--write" in sys.argv:
        for name, bad in failures.items():
            for f in bad:
                print(f"FAIL [{name}] {f}")
        if any(failures.values()):
            sys.exit(1)

    if "--write" in sys.argv:
        for name in names:
            path = f"{LUA_DIR}/{name}.lua"
            with open(path, "w") as fh:
                fh.write(to_lua(VARIANTS[name](), name))
            print(f"wrote {path}")
        sys.exit(0)

    if "--check" in sys.argv:
        for name in names:
            palette = VARIANTS[name]()
            n = len(FLOORS) + len(ACCENTS)
            gap, a, b = role_distances(palette)[0]
            print(f"ok [{name}]: {n} contrast floors met (bg {palette['bg']}); "
                  f"closest roles {a}/{b} gap {gap:.3f}")
        sys.exit(0)

    for name in names:
        palette = VARIANTS[name]()
        print(f"--- {name}")
        width = max(len(k) for k in palette)
        for key in sorted(palette):
            print(f"  {key:<{width}}  {palette[key]}  cr={contrast(palette[key], palette['bg']):5.2f}")
