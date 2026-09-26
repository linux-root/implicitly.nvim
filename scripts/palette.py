#!/usr/bin/env python3
"""Derive the `implicitly` palette from its four seed colors.

The seeds (https://colorhunt.co/palette/1801614f1787eb3678fb773c) are all violet
and warm -- there is no green, teal, blue or yellow anywhere in them. A syntax
theme needs those hues for diff, diagnostics and strings, so they are generated
here in OKLCH at a lightness band matched to the seeds, with chroma clamped into
the sRGB gamut. That keeps the derived hues from reading as a different palette
bolted onto the seeds.

    python3 scripts/palette.py --write    # regenerate lua/implicitly/palette.lua
    python3 scripts/palette.py --check    # assert the contrast floors
    python3 scripts/palette.py            # print the table with contrast ratios
"""

import math
import sys

SEEDS = {"indigo": "#180161", "purple": "#4F1787", "pink": "#EB3678", "orange": "#FB773C"}
GROUND_HUE = 288  # the seed indigo's hue, rounded -- everything neutral rides on it

# --- OKLab <-> sRGB ----------------------------------------------------------
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
    """OKLCH -> hex, walking chroma down until the color fits in sRGB."""
    while chroma > 0.001 and not all(-0.0015 <= c <= 1.0015
                                     for c in _oklch_to_linear(lightness, chroma, hue)):
        chroma -= 0.002
    return rgb_to_hex([_to_srgb(c) for c in _oklch_to_linear(lightness, chroma, hue)])


def luminance(h):
    r, g, b = (_to_linear(c) for c in hex_to_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    hi, lo = sorted([luminance(a), luminance(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


# --- the palette -------------------------------------------------------------
def build():
    g = lambda lightness, chroma: oklch(lightness, chroma, GROUND_HUE)
    p = {
        # ground: the seed indigo's hue, walked from near-black up to near-white
        "bg_dark1": g(0.120, 0.090),
        "bg_dark": g(0.155, 0.100),
        "bg": g(0.190, 0.105),
        "bg_highlight": g(0.245, 0.110),
        "fg_gutter": g(0.310, 0.090),
        "dark3": g(0.440, 0.080),
        "comment": g(0.530, 0.075),
        "dark5": g(0.580, 0.075),
        "fg_dark": g(0.810, 0.040),
        "fg": g(0.905, 0.035),
        "terminal_black": g(0.380, 0.085),
        # the two bright seeds, verbatim
        "pink": SEEDS["pink"],
        "orange": SEEDS["orange"],
        # derived, filling the empty H 85..265 arc
        "red": oklch(0.660, 0.190, 15),
        "yellow": oklch(0.780, 0.150, 85),
        "green": oklch(0.765, 0.150, 148),
        "teal": oklch(0.740, 0.115, 180),
        "cyan": oklch(0.790, 0.110, 215),
        "blue": oklch(0.700, 0.140, 265),
        "purple": oklch(0.680, 0.160, 300),
        "magenta": oklch(0.720, 0.165, 330),
    }
    # Numbered variants. The suffix is tokyonight's naming, not a lightness
    # ordering: blue1/blue5/blue6 and green1 are *bright* foregrounds (Type,
    # @property, icons), while blue7 and red1 are dark surfaces. Getting this
    # backwards makes Type unreadable, so the roles are spelled out here.
    for name, (lightness, chroma, hue) in {
        "blue1": (0.800, 0.120, 220),   # bright -- Type, Special, accent icons
        "blue5": (0.860, 0.090, 225),   # bright -- operators, delimiters
        "blue6": (0.910, 0.070, 200),   # bright -- regex
        "blue7": (0.380, 0.090, 270),   # dark   -- diff change surface
        "green1": (0.810, 0.110, 168),  # bright -- @property, @variable.member
        "green2": (0.660, 0.100, 175),  # mid    -- diff add surface
        "red1": (0.560, 0.190, 20),     # mid    -- diff delete surface
        "magenta2": (0.600, 0.230, 355),
    }.items():
        p[name] = oklch(lightness, chroma, hue)
    # the two dark seeds stay as literal raised surfaces
    p["seed_indigo"] = SEEDS["indigo"]
    p["seed_purple"] = SEEDS["purple"]
    # Diff surfaces. Blending an accent toward the background is what tokyonight
    # does, but on a saturated violet ground it muddies every hue into the same
    # blue-grey -- add and change came out indistinguishable. Setting them
    # directly at a fixed low lightness keeps the three hues apart.
    p["diff_add"] = oklch(0.330, 0.085, 150)
    p["diff_change"] = oklch(0.330, 0.080, 260)
    p["diff_delete"] = oklch(0.330, 0.105, 15)
    p["diff_text"] = oklch(0.430, 0.100, 260)
    p["git_add"] = oklch(0.560, 0.110, 155)
    p["git_change"] = oklch(0.560, 0.100, 255)
    p["git_delete"] = oklch(0.520, 0.130, 10)
    return p


# Contrast floors. Anything a person reads as text has to clear these against bg;
# the ground colors are surfaces, so they are capped instead of floored.
FLOORS = {"fg": 12.0, "fg_dark": 8.0, "comment": 3.0, "dark5": 3.5,
          # these read as foreground despite the numeric suffix
          "blue1": 6.0, "blue5": 8.0, "blue6": 8.0, "green1": 6.0}
ACCENT_FLOOR = 4.5
ACCENTS = ["red", "pink", "orange", "yellow", "green", "teal", "cyan", "blue", "purple", "magenta"]


def _hue_gap(a, b):
    ha, hb = hex_to_oklch(a)[2], hex_to_oklch(b)[2]
    return min(abs(ha - hb), 360 - abs(ha - hb))


def check(p):
    bad = []
    for key, floor in FLOORS.items():
        got = contrast(p[key], p["bg"])
        if got < floor:
            bad.append(f"{key} {p[key]} contrast {got:.2f} < {floor}")
    for key in ACCENTS:
        got = contrast(p[key], p["bg"])
        if got < ACCENT_FLOOR:
            bad.append(f"{key} {p[key]} contrast {got:.2f} < {ACCENT_FLOOR}")
    for a, b in (("diff_add", "diff_change"), ("diff_add", "diff_delete"),
                 ("diff_change", "diff_delete")):
        if contrast(p[a], p[b]) > 1.35 or _hue_gap(p[a], p[b]) < 40:
            bad.append(f"{a}/{b} too alike: hue gap {_hue_gap(p[a], p[b]):.0f}deg")
    for key in ("bg_dark", "bg_dark1"):
        if luminance(p[key]) > luminance(p["bg"]):
            bad.append(f"{key} is lighter than bg")
    return bad


LUA_PATH = "lua/implicitly/palette.lua"

# Emission order and the notes that go next to each entry. Anything in build()
# but not listed here still gets written, in the trailing block.
LAYOUT = [
    ("bg", "seed #180161, darkened"), ("bg_dark", None), ("bg_dark1", None),
    ("bg_highlight", None), ("fg", None), ("fg_dark", None), ("fg_gutter", None),
    ("comment", None), ("dark3", None), ("dark5", None), ("terminal_black", None),
    (None, None),
    ("pink", "seed, verbatim"), ("orange", "seed, verbatim"),
    (None, None),
    ("red", None), ("yellow", None), ("green", None), ("teal", None),
    ("cyan", None), ("blue", None), ("purple", None), ("magenta", None),
    (None, None),
    ("blue1", "bright: Type, Special, accent icons"), ("blue5", "bright: operators"),
    ("blue6", "bright: regex"), ("green1", "bright: @property, @variable.member"),
    (None, None),
    ("blue7", None), ("red1", None), ("green2", None), ("magenta2", None),
]

HEADER = """-- Generated by scripts/palette.py -- run `python3 scripts/palette.py --write`
-- to re-derive. Don't hand-edit; edit the generator.
--
-- Seeds: https://colorhunt.co/palette/1801614f1787eb3678fb773c
-- #180161 #4F1787 #EB3678 #FB773C -- all violet and warm. No green, teal, cyan
-- or blue exists in that set, so those are derived in OKLCH at a lightness band
-- matched to the seeds, which keeps diff and diagnostics readable without
-- reading as a second palette bolted on.
--
-- The numeric suffixes are tokyonight's naming and are NOT a lightness ordering:
-- blue1/blue5/blue6/green1 are bright foregrounds, blue7/red1 are dark surfaces.

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
        lines.append(f"{entry:<26}-- {note}" if note else entry)
    return HEADER + "\n".join(lines) + f'''

  -- the two dark seeds, verbatim, as raised surfaces (visual, search, borders)
  seed_indigo = "{p["seed_indigo"]}",
  seed_purple = "{p["seed_purple"]}",

  -- diff surfaces, set directly rather than blended: see build()
  diff_add = "{p["diff_add"]}",
  diff_change = "{p["diff_change"]}",
  diff_delete = "{p["diff_delete"]}",
  diff_text = "{p["diff_text"]}",

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
    if "--check" in sys.argv:
        failures = check(palette)
        for f in failures:
            print("FAIL", f)
        if not failures:
            print(f"ok: {len(FLOORS) + len(ACCENTS)} contrast floors met (bg {palette['bg']})")
        sys.exit(1 if failures else 0)
    if "--write" in sys.argv:
        failures = check(palette)
        if failures:
            for f in failures:
                print("FAIL", f)
            sys.exit(1)
        with open(LUA_PATH, "w") as fh:
            fh.write(to_lua(palette))
        print(f"wrote {LUA_PATH}")
        sys.exit(0)
    width = max(len(k) for k in palette)
    for key in sorted(palette):
        print(f"{key:<{width}}  {palette[key]}  cr={contrast(palette[key], palette['bg']):5.2f}")
