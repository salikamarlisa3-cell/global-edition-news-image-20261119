#!/usr/bin/env python3
"""The Global Edition — Thursday 19 November 2026.

Draws a one-page poster of the day's world news: 52 stories from named
outlets, 17 illustrated panels, a dot-matrix world map with a pin for
every featured story, a UTC timeline, a by-the-numbers strip, a markets
strip and a date-check box. Pillow only, fully deterministic: the same
image bytes on every run. Writes entry.png to $MAKEFUN_OUTPUT_DIR
(default /output).
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

W = H = 1024
PAPER = (247, 242, 231)
INK = (26, 26, 46)
FAINT = (110, 104, 92)
RED = (179, 57, 46)
BLUE = (36, 86, 166)
GOLD = (178, 132, 20)
GREEN = (46, 120, 74)
SKY = (214, 228, 240)
SAND = (238, 226, 198)
GREY = (198, 194, 184)

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


# ---------------------------------------------------------------- stories
# (number, headline, outlet, region, glyph, pin lon/lat or None)
STORIES = [
    (1, "Trump, Xi, Putin hold first trilateral summit", "USA Today",
     "ASIA", "flags", (114.1, 22.6)),
    (2, "World Court delivers Gambia v. Myanmar judgment", "Reuters",
     "EUROPE", "gavel", (4.3, 52.1)),
    (3, "Crimea Bridge hit a third time; traffic halted", "Independent",
     "EUROPE", "bridge", (34.1, 45.0)),
    (4, "IG Metall calls 24h strikes in auto and steel", "Reuters",
     "EUROPE", "factory", (10.4, 51.1)),
    (5, "Dozens missing as migrant boat capsizes", "Reuters",
     "AFRICA", "boat", (-17.4, 14.7)),
    (6, "COP31 final stretch; new draft text due", "Reuters",
     "CLIMATE", "globe", (30.7, 36.9)),
    (7, "Hawkish Fed minutes; Wall St's 5th straight loss", "CaixaBank",
     "AMERICAS", "chartdown", (-74.0, 40.7)),
    (8, "Anthropic lists on Nasdaq, IPO priced at $83", "IC Markets",
     "AMERICAS", "chip", (-73.9, 40.75)),
    (9, "GTA VI launch day: midnight unlocks worldwide", "Rockstar",
     "AMERICAS", "game", (-118.2, 34.1)),
    (10, "Giannis faces Bucks first time; Heat win 137-130", "Reuters",
     "AMERICAS", "ball", (-80.2, 25.8)),
    (11, "Bangladesh lockdown day; Hasina return fears", "Daily Star",
     "ASIA", "lock", (90.4, 23.8)),
    (12, "Saudi coalition repels missiles toward Riyadh", "Al Jazeera",
     "MIDEAST", "missile", (46.7, 24.6)),
    (13, "Venezuela touts AI for cleaner oil at COP31", "Reuters",
     "AMERICAS", "oilleaf", (-66.9, 10.5)),
    (14, "UNHCR halts refugee registration in Malaysia", "Reuters",
     "ASIA", "idcard", (101.7, 3.1)),
    (15, "Indonesia parliament passes asset forfeiture law", "Reuters",
     "ASIA", "scales", (106.8, -6.2)),
    (16, "Ethiopian Airlines probes ShebaMiles data breach", "Reuters",
     "AFRICA", "plane", (38.7, 9.0)),
    (17, "PHP ships critical security release, all versions", "PHP.net",
     "TECH", "code", (-30.0, 32.0)),
    (18, "Trump-Xi bilateral working lunch in Shenzhen", "AFP",
     "ASIA", None, None),
    (19, "APEC leaders' meeting, Shenzhen, 18-19 Nov", "Diplomatic Watch",
     "ASIA", None, None),
    (20, "Putin: all three want the Ukraine war resolved", "USA Today",
     "ASIA", None, None),
    (21, "Elon Musk accompanies Trump to China", "BBN Times",
     "ASIA", None, None),
    (22, "Russian drones damage 29 homes in Kyiv region", "Ukrinform",
     "EUROPE", None, None),
    (23, "Ukrainian drones hit Afipsky, Ilsky refineries", "Rus. MoD",
     "EUROPE", None, None),
    (24, "Zelensky: positions strong near Dobropillia", "Independent",
     "EUROPE", None, None),
    (25, "EU approves e-declaration for posted workers", "EU Council",
     "EUROPE", None, None),
    (26, "EU deal on methane regulation amendments", "EU Council",
     "EUROPE", None, None),
    (27, "EU adopts cross-border protection for adults", "EU Council",
     "EUROPE", None, None),
    (28, "EU signs off chemicals simplification law", "EU Council",
     "EUROPE", None, None),
    (29, "Swiss bankers seek changes to banking overhaul", "Reuters",
     "EUROPE", None, None),
    (30, "Bucharest Security Conference 2026 announced", "SNSPA",
     "MIDEAST", None, None),
    (31, "Qatar warns Gulf escalation threatens talks", "Anadolu",
     "MIDEAST", None, None),
    (32, "Brent about $92, WTI about $82 on the day", "CaixaBank",
     "MIDEAST", None, None),
    (33, "Nvidia slips 3% despite revenue up 103%", "TRW News",
     "AMERICAS", None, None),
    (34, "Bitcoin trades near $62,500", "TRW News",
     "AMERICAS", None, None),
    (35, "IEA World Energy Outlook 2026 released", "OCI advisory",
     "CLIMATE", None, None),
    (36, "Global South youth demonstrate inside COP31", "Africa Sust.",
     "AFRICA", None, None),
    (37, "COP31 draft seeks $120bn adaptation finance", "Antalya reports",
     "CLIMATE", None, None),
    (38, "75 countries back Turkiye '35 by 35' power goal", "Reuters",
     "MIDEAST", None, None),
    (39, "PostgreSQL 19 GA slips to 19 Nov via RC2", "PostgreSQL",
     "TECH", None, None),
    (40, "India v New Zealand first Test opens, Wellington", "Indian sports",
     "TECH", None, None),
    (41, "Sindhu back in world top five; Sen into top 10", "Indian sports",
     "TECH", None, None),
    (42, "Vaishali wins by forfeit at Total Chess", "Indian sports",
     "TECH", None, None),
    (43, "Rockets 119, Pacers 104 - Durant scores 21", "Reuters",
     "AMERICAS", None, None),
    (44, "Nuggets 105, Celtics 101; Jazz 109, Lakers 97", "Reuters",
     "AMERICAS", None, None),
    (45, "Mavericks 116, Warriors 94; Bulls 137, Nets 107", "Reuters",
     "AMERICAS", None, None),
    (46, "Grizzlies 124, Cavaliers 121; 76ers 121, Magic 115", "Reuters",
     "AMERICAS", None, None),
    (47, "Wizards 103, Raptors 99", "Reuters",
     "AMERICAS", None, None),
    (48, "Nigeria NGX falls a second day; Aradel -10%", "TRW News",
     "AFRICA", None, None),
    (49, "India signs defence deals with Israel, Japan", "Indian reports",
     "ASIA", None, None),
    (50, "Goldman Sachs upgrades India to overweight", "Indian reports",
     "ASIA", None, None),
    (51, "Delhi-NCR schools reopen as GRAP-III lifted", "Indian reports",
     "ASIA", None, None),
    (52, "ICJ: Myanmar blocked probes, refused evidence", "BBC",
     "EUROPE", None, None),
]

REGIONS = [
    ("AMERICAS", "The Americas"),
    ("EUROPE", "Europe"),
    ("MIDEAST", "Middle East"),
    ("AFRICA", "Africa"),
    ("ASIA", "Asia"),
    ("CLIMATE", "Climate & Energy"),
    ("TECH", "Oceania & Tech"),
]

TIMELINE = [
    ("01:58", "UNHCR halts Malaysia registration"),
    ("04:50", "Indonesia passes asset forfeiture law"),
    ("09:18", "Swiss bankers seek overhaul changes"),
    ("09:28", "Ethiopian Airlines breach probe"),
    ("10:17", "IG Metall calls 24h strikes"),
    ("14:00", "PHP critical security release"),
]

NUMBERS = [
    ("10,000", "Rohingya killed, court finds"),
    ("815,000", "targeted in 2017, ICJ"),
    ("$83", "Anthropic IPO price"),
    ("184", "drones Russia says downed"),
    ("29", "Kyiv-region homes damaged"),
    ("$120bn", "adaptation finance sought"),
    ("75", "countries back '35 by 35'"),
    ("24h", "IG Metall strike call"),
]

MARKETS = ("Markets on the day: Brent ~$92 - WTI ~$82 - Bitcoin ~$62,500 - "
           "Nvidia -3% on revenue +103% - Wall Street's fifth straight loss - "
           "Nigeria's NGX down a second day")

LEFT_OUT = [
    "Voyager 1 reached one light-day from Earth on 18 Nov - yesterday's milestone.",
    "Iran's strikes on Kuwait and Bahrain, and the US strike on Qeshm, were 17-18 Nov.",
    "Peltola's Alaska Senate win was called on 18 Nov - yesterday.",
    "Jensen Huang's Nvidia exit dates to 12-13 Nov; only the earnings reaction is today's.",
    "A reported Russian plane crash in Siberia (19 dead) is unconfirmed - excluded.",
]

# continent polygons as (lon, lat) outlines for the dot-matrix map
LAND = [
    [(-168, 66), (-140, 70), (-125, 71), (-110, 68), (-95, 69), (-85, 66),
     (-80, 62), (-78, 58), (-85, 55), (-90, 50), (-85, 47), (-76, 44),
     (-70, 42), (-74, 38), (-76, 34), (-80, 30), (-81, 25), (-84, 29),
     (-90, 28), (-97, 26), (-97, 22), (-94, 18), (-90, 15), (-83, 9),
     (-79, 9), (-77, 4), (-80, 0), (-81, -4), (-77, -12), (-70, -18),
     (-70, -24), (-70, -32), (-72, -40), (-74, -48), (-72, -54), (-66, -55),
     (-68, -50), (-65, -42), (-62, -35), (-52, -28), (-41, -20), (-35, -8),
     (-38, -4), (-44, 0), (-50, 4), (-58, 7), (-64, 10), (-70, 12),
     (-75, 10), (-80, 8), (-85, 12), (-90, 14), (-95, 16), (-102, 18),
     (-105, 22), (-110, 24), (-114, 29), (-120, 34), (-124, 42), (-124, 48),
     (-130, 55), (-140, 60), (-155, 59), (-165, 60)],
    [(-9, 43), (-2, 44), (0, 46), (-5, 48), (-1, 50), (2, 51), (5, 53),
     (8, 55), (8, 57), (12, 56), (18, 56), (21, 55), (24, 58), (28, 60),
     (30, 62), (28, 66), (32, 70), (45, 68), (60, 69), (75, 72), (90, 74),
     (105, 77), (120, 73), (135, 72), (150, 70), (162, 66), (170, 66),
     (178, 65), (170, 60), (158, 52), (142, 50), (138, 44), (132, 43),
     (128, 40), (122, 38), (120, 34), (121, 30), (118, 25), (110, 20),
     (108, 14), (106, 8), (103, 5), (100, 8), (98, 14), (94, 17), (91, 22),
     (88, 21), (86, 19), (80, 14), (77, 8), (73, 18), (70, 22), (66, 25),
     (61, 25), (57, 27), (52, 28), (50, 29), (48, 30), (50, 26), (55, 24),
     (58, 23), (55, 20), (52, 16), (48, 14), (44, 12), (43, 15), (40, 20),
     (38, 24), (36, 28), (34, 31), (30, 31), (26, 32), (22, 33), (18, 33),
     (12, 34), (10, 34), (10, 37), (8, 39), (4, 40), (0, 39), (-2, 37),
     (-6, 36), (-9, 37), (-9, 43)],
    [(-17, 15), (-10, 14), (-5, 10), (2, 6), (6, 4), (9, 4), (13, -2),
     (12, -10), (14, -18), (16, -26), (18, -32), (26, -34), (32, -28),
     (35, -22), (36, -16), (38, -10), (40, -4), (42, 2), (48, 8), (51, 11),
     (44, 11), (40, 15), (38, 20), (36, 24), (34, 28), (32, 31), (30, 31),
     (24, 32), (18, 33), (12, 34), (6, 34), (0, 35), (-6, 35), (-10, 31),
     (-14, 24), (-17, 20), (-17, 15)],
    [(95, 5), (100, 6), (104, 8), (107, 12), (110, 16), (114, 20),
     (118, 24), (121, 28), (126, 34), (130, 38), (134, 42), (138, 44),
     (141, 46), (141, 50), (138, 46), (134, 44), (130, 42), (126, 40),
     (122, 36), (120, 32), (118, 28), (114, 22), (110, 18), (106, 12),
     (102, 8), (98, 6), (95, 5)],
    [(112, -11), (114, -18), (113, -24), (115, -32), (118, -35), (124, -33),
     (130, -32), (134, -33), (137, -35), (140, -38), (144, -38), (147, -38),
     (150, -37), (153, -30), (153, -24), (151, -18), (146, -14), (142, -11),
     (141, -14), (139, -18), (136, -22), (135, -26), (133, -30), (130, -32),
     (126, -33), (120, -34), (116, -34), (114, -28), (113, -20), (112, -14),
     (112, -11)],
    [(166, -46), (170, -44), (173, -41), (176, -38), (178, -37), (175, -40),
     (172, -43), (168, -46), (166, -46)],
]


# ---------------------------------------------------------------- drawing
def wrap(draw, text, fnt, width):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def fit_lines(draw, text, path, width, start, min_size, max_lines):
    size = start
    while size > min_size:
        fnt = font(path, size)
        lines = wrap(draw, text, fnt, width)
        if len(lines) <= max_lines:
            return fnt, lines
        size -= 1
    fnt = font(path, min_size)
    return fnt, wrap(draw, text, fnt, width)[:max_lines]


def glyph(draw, kind, x, y, s):
    """Tiny scene pictograms inside an s-by-s box at (x, y)."""
    cx, cy = x + s / 2, y + s / 2
    if kind == "flags":
        for i, col in enumerate((RED, GOLD, BLUE)):
            fx = x + 6 + i * (s - 12) / 2
            draw.line([fx, y + 8, fx, y + s - 6], fill=INK, width=2)
            draw.rectangle([fx, y + 8, fx + (s - 12) / 2 - 4, y + 8 + s / 4],
                           fill=col)
        draw.line([x + 6, y + s - 6, x + s - 6, y + s - 6], fill=INK, width=2)
    elif kind == "gavel":
        draw.polygon([(cx - s * .3, cy - s * .3), (cx - s * .1, cy - s * .42),
                      (cx + s * .02, cy - s * .22), (cx - s * .18, cy - s * .1)],
                     fill=INK)
        draw.line([cx - s * .08, cy - s * .16, cx + s * .3, cy + s * .22],
                  fill=INK, width=max(3, int(s * .07)))
        draw.line([x + s * .18, y + s * .82, x + s * .82, y + s * .82],
                  fill=RED, width=3)
    elif kind == "bridge":
        draw.line([x + 4, cy + s * .2, x + s - 4, cy + s * .2], fill=INK, width=3)
        for t in (0.25, 0.5, 0.75):
            draw.line([x + s * t, y + 8, x + s * t, cy + s * .2], fill=INK, width=2)
        draw.line([x + 4, y + 8, x + s - 4, y + 8], fill=INK, width=2)
        draw.polygon([(cx - 6, cy - s * .22), (cx + 8, cy - s * .05),
                      (cx - 2, cy + s * .1)], fill=RED)
    elif kind == "factory":
        draw.rectangle([x + 6, cy, x + s - 6, y + s - 8], outline=INK, width=2)
        draw.rectangle([x + 10, y + s * .3, x + 20, cy], fill=INK)
        draw.rectangle([x + 26, y + s * .42, x + 36, cy], fill=INK)
        draw.line([x + 4, cy + s * .3, x + s - 4, cy + s * .3], fill=RED, width=3)
    elif kind == "boat":
        draw.polygon([(x + 8, cy), (x + s - 8, cy), (x + s - 16, cy + s * .22),
                      (x + 16, cy + s * .22)], fill=INK)
        draw.line([cx, y + 8, cx, cy], fill=INK, width=2)
        draw.polygon([(cx, y + 10), (cx, cy - 2), (cx + s * .22, cy - 2)],
                     fill=SKY, outline=INK)
        for i in range(3):
            draw.arc([x + 6 + i * s / 3, cy + s * .26, x + 6 + (i + 1) * s / 3,
                      cy + s * .44], 0, 180, fill=BLUE, width=2)
    elif kind == "globe":
        draw.ellipse([cx - s * .32, cy - s * .32, cx + s * .32, cy + s * .32],
                     outline=GREEN, width=3)
        draw.line([cx - s * .32, cy, cx + s * .32, cy], fill=GREEN, width=1)
        draw.line([cx, cy - s * .32, cx, cy + s * .32], fill=GREEN, width=1)
        draw.ellipse([cx - s * .14, cy - s * .32, cx + s * .14, cy + s * .32],
                     outline=GREEN, width=1)
    elif kind == "chartdown":
        pts = [(x + 8, y + s * .3), (x + s * .35, y + s * .42),
               (x + s * .55, y + s * .38), (x + s * .8, y + s * .66)]
        draw.line(pts, fill=RED, width=3)
        draw.polygon([(x + s * .8, y + s * .66), (x + s * .68, y + s * .64),
                      (x + s * .79, y + s * .52)], fill=RED)
        draw.line([x + 6, y + s - 8, x + s - 6, y + s - 8], fill=INK, width=1)
    elif kind == "chip":
        draw.rectangle([cx - s * .26, cy - s * .26, cx + s * .26, cy + s * .26],
                       outline=INK, width=3)
        for i in range(-1, 2):
            draw.line([cx + i * s * .16, cy - s * .26, cx + i * s * .16,
                       cy - s * .4], fill=INK, width=2)
            draw.line([cx + i * s * .16, cy + s * .26, cx + i * s * .16,
                       cy + s * .4], fill=INK, width=2)
        draw.text((cx, cy), "AI", font=font(SANS_B, int(s * .24)), fill=BLUE,
                  anchor="mm")
    elif kind == "game":
        draw.rounded_rectangle([x + 8, cy - s * .2, x + s - 8, cy + s * .2],
                               radius=8, outline=INK, width=3)
        draw.line([x + s * .22, cy - 6, x + s * .22, cy + 6], fill=RED, width=3)
        draw.line([x + s * .22 - 6, cy, x + s * .22 + 6, cy], fill=RED, width=3)
        for dx, dy in ((0, -5), (5, 0), (0, 5), (-5, 0)):
            draw.ellipse([x + s * .72 + dx - 2, cy + dy - 2,
                          x + s * .72 + dx + 2, cy + dy + 2], fill=BLUE)
    elif kind == "ball":
        draw.ellipse([cx - s * .3, cy - s * .3, cx + s * .3, cy + s * .3],
                     outline=INK, width=3)
        draw.line([cx - s * .3, cy, cx + s * .3, cy], fill=INK, width=1)
        draw.arc([cx - s * .14, cy - s * .3, cx + s * .14, cy + s * .3],
                 90, 270, fill=INK, width=1)
        draw.arc([cx - s * .14, cy - s * .3, cx + s * .14, cy + s * .3],
                 270, 90, fill=INK, width=1)
    elif kind == "lock":
        draw.rectangle([cx - s * .26, cy - s * .02, cx + s * .26, cy + s * .32],
                       fill=INK)
        draw.arc([cx - s * .17, cy - s * .3, cx + s * .17, cy + s * .1],
                 180, 360, fill=INK, width=4)
        draw.ellipse([cx - 3, cy + s * .1, cx + 3, cy + s * .1 + 6], fill=PAPER)
    elif kind == "missile":
        draw.polygon([(x + s * .3, y + s * .7), (x + s * .62, y + s * .38),
                      (x + s * .72, y + s * .48), (x + s * .4, y + s * .8)],
                     fill=INK)
        draw.polygon([(x + s * .62, y + s * .38), (x + s * .78, y + s * .3),
                      (x + s * .7, y + s * .46)], fill=RED)
        draw.line([x + 8, y + s - 8, x + s * .4, y + s - 8], fill=INK, width=2)
        draw.line([x + s * .55, y + s - 8, x + s - 8, y + s - 8], fill=INK, width=2)
    elif kind == "oilleaf":
        draw.ellipse([cx - s * .12, cy - s * .34, cx + s * .12, cy + s * .02],
                     fill=INK)
        draw.polygon([(cx - s * .26, cy + s * .3), (cx + s * .05, cy - s * .05),
                      (cx + s * .3, cy + s * .12), (cx + s * .08, cy + s * .34),
                      (cx - s * .14, cy + s * .3)], fill=GREEN)
    elif kind == "idcard":
        draw.rectangle([x + 8, y + s * .22, x + s - 8, y + s * .78],
                       outline=INK, width=3)
        draw.ellipse([x + s * .2, cy - s * .1, x + s * .38, cy + s * .08],
                     fill=BLUE)
        draw.line([x + s * .48, cy - s * .04, x + s * .8, cy - s * .04],
                  fill=INK, width=2)
        draw.line([x + s * .48, cy + s * .1, x + s * .8, cy + s * .1],
                  fill=INK, width=2)
        draw.line([x + s * .2, y + s * .66, x + s * .8, y + s * .66],
                  fill=RED, width=3)
    elif kind == "scales":
        draw.line([cx, y + 8, cx, y + s - 10], fill=INK, width=3)
        draw.line([x + 10, y + s * .22, x + s - 10, y + s * .22], fill=INK, width=2)
        for sx in (x + 10, x + s - 10):
            draw.polygon([(sx, y + s * .22), (sx - 8, y + s * .5),
                          (sx + 8, y + s * .5)], outline=INK)
        draw.line([x + s * .3, y + s - 8, x + s * .7, y + s - 8], fill=INK, width=3)
    elif kind == "plane":
        draw.polygon([(x + 6, cy + s * .12), (x + s * .4, cy - s * .05),
                      (x + s - 10, cy - s * .28), (x + s - 4, cy - s * .05),
                      (x + s * .42, cy + s * .1), (x + s * .2, cy + s * .3),
                      (x + s * .14, cy + s * .12)], fill=INK)
        draw.line([x + 8, y + s - 8, x + s - 8, y + s - 8], fill=BLUE, width=2)
    elif kind == "code":
        f = font(SANS_B, int(s * .44))
        draw.text((cx, cy), "</>", font=f, fill=BLUE, anchor="mm")
    else:
        draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=GOLD)


def in_poly(lon, lat, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > lat) != (y2 > lat):
            xin = x1 + (lat - y1) * (x2 - x1) / (y2 - y1)
            if lon < xin:
                inside = not inside
    return inside


def draw_map(draw, x0, y0, w, h):
    draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(233, 238, 244))
    step = 7
    cols = int(w / step)
    rows = int(h / step)
    for r in range(rows):
        lat = 82 - (r + 0.5) * 164 / rows
        for c in range(cols):
            lon = -180 + (c + 0.5) * 360 / cols
            if any(in_poly(lon, lat, p) for p in LAND):
                px = x0 + c * step + step / 2
                py = y0 + r * step + step / 2
                draw.ellipse([px - 1.6, py - 1.6, px + 1.6, py + 1.6],
                             fill=(96, 110, 128))
    pins = [(s[0], s[5]) for s in STORIES if s[5]]
    for num, (lon, lat) in pins:
        px = x0 + (lon + 180) / 360 * w
        py = y0 + (82 - lat) / 164 * h
        draw.ellipse([px - 8, py - 8, px + 8, py + 8], fill=RED)
        draw.text((px, py), str(num), font=font(SANS_B, 9), fill=(255, 255, 255),
                  anchor="mm")
    draw.text((x0 + 8, y0 + h - 18), "Featured stories 1-17, pinned",
              font=font(SANS, 9), fill=FAINT)


def panel(draw, story, x, y, w, h, lead=False):
    num, head, outlet, _reg, g, _pin = story
    draw.rectangle([x, y, x + w, y + h], fill=(255, 253, 247), outline=GREY)
    if lead:
        gs = 64
        glyph(draw, g, x + 10, y + (h - gs) // 2, gs)
        draw.ellipse([x + 6, y + 6, x + 26, y + 26], fill=INK)
        draw.text((x + 16, y + 16), str(num), font=font(SANS_B, 11),
                  fill=(255, 255, 255), anchor="mm")
        tx = x + 86
        fnt, lines = fit_lines(draw, head, SANS_B, w - tx + x - 10, 15, 10, 3)
        ty = y + 12
        for ln in lines:
            draw.text((tx, ty), ln, font=fnt, fill=INK)
            ty += fnt.size + 3
        draw.text((tx, y + h - 18), outlet.upper(), font=font(SANS, 9),
                  fill=RED)
    else:
        gs = 30
        glyph(draw, g, x + 4, y + (h - gs) // 2, gs)
        draw.ellipse([x + 3, y + 3, x + 19, y + 19], fill=INK)
        draw.text((x + 11, y + 11), str(num), font=font(SANS_B, 8),
                  fill=(255, 255, 255), anchor="mm")
        tx = x + 40
        fnt, lines = fit_lines(draw, head, SANS, w - tx + x - 6, 9, 7, 4)
        ty = y + 5
        for ln in lines:
            draw.text((tx, ty), ln, font=fnt, fill=INK)
            ty += fnt.size + 1


def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # masthead
    d.text((W / 2, 8), "THE GLOBAL EDITION", font=font(SERIF_B, 38),
           fill=INK, anchor="ma")
    d.line([28, 56, W - 28, 56], fill=INK, width=3)
    d.text((W / 2, 61), "Thursday 19 November 2026  -  The World in One Day"
           "  -  52 stories  -  7 regions  -  every story reported that day",
           font=font(SANS, 12), fill=FAINT, anchor="ma")

    by_num = {s[0]: s for s in STORIES}
    # leads: stories 1 and 2
    panel(d, by_num[1], 28, 84, 474, 104, lead=True)
    panel(d, by_num[2], 522, 84, 474, 104, lead=True)

    # illustrated tiles for featured 3-17: rows of 8 and 7
    rest = [by_num[i] for i in range(3, 18)]
    tw, th, tg = 115, 62, 6
    for i, st in enumerate(rest):
        row, col = divmod(i, 8)
        px = 28 + col * (tw + tg) + (row * (tw + tg)) // 2
        py = 196 + row * (th + tg)
        panel(d, st, px, py, tw, th)

    # map + timeline
    my = 340
    draw_map(d, 28, my, 636, 140)
    tx = 680
    d.rectangle([tx, my, W - 28, my + 140], fill=(255, 253, 247), outline=GREY)
    d.text((tx + 10, my + 7), "THE DAY IN UTC", font=font(SANS_B, 12), fill=INK)
    ty = my + 30
    for hh, txt in TIMELINE:
        d.text((tx + 10, ty), hh, font=font(SANS_B, 10), fill=BLUE)
        fnt, lines = fit_lines(d, txt, SANS, 224, 10, 8, 2)
        ly = ty
        for ln in lines:
            d.text((tx + 54, ly), ln, font=fnt, fill=INK)
            ly += 12
        ty += 18

    # story columns
    cy = 492
    col_w = [150, 152, 118, 112, 152, 138, 128]
    x = 28
    for (code, label), cw in zip(REGIONS, col_w):
        d.rectangle([x, cy, x + cw, cy + 19], fill=INK)
        d.text((x + cw / 2, cy + 9), label.upper(), font=font(SANS_B, 9),
               fill=(255, 255, 255), anchor="mm")
        ty = cy + 24
        for st in STORIES:
            if st[3] != code:
                continue
            head = f"{st[0]}. {st[1]}"
            fnt, lines = fit_lines(d, head, SANS, cw - 4, 8, 7, 3)
            for ln in lines:
                d.text((x + 2, ty), ln, font=fnt, fill=INK)
                ty += fnt.size + 1
            d.text((x + 2, ty), st[2], font=font(SANS, 7), fill=RED)
            ty += 9
        x += cw + 3

    # numbers strip
    ny = 830
    d.line([28, ny, W - 28, ny], fill=INK, width=2)
    d.text((28, ny + 5), "BY THE NUMBERS", font=font(SANS_B, 12), fill=INK)
    nx = 28
    nw = (W - 56) / 8
    for val, lab in NUMBERS:
        d.text((nx + nw / 2, ny + 24), val, font=font(SERIF_B, 17), fill=RED,
               anchor="ma")
        fnt, lines = fit_lines(d, lab, SANS, nw - 8, 9, 7, 3)
        ly = ny + 50
        for ln in lines:
            d.text((nx + nw / 2, ly), ln, font=fnt, fill=FAINT, anchor="ma")
            ly += 10
        nx += nw

    # markets strip
    ky = 918
    d.rectangle([28, ky, W - 28, ky + 22], fill=SAND)
    d.text((W / 2, ky + 11), MARKETS, font=font(SANS, 10), fill=INK, anchor="mm")

    # left-out box + footer
    by = 944
    d.rectangle([28, by, W - 28, by + 58], outline=GREY)
    d.text((38, by + 4), "LEFT OUT - AND WHY (the date-check box)",
           font=font(SANS_B, 9), fill=INK)
    ly = by + 19
    for item in LEFT_OUT:
        d.text((38, ly), "- " + item, font=font(SANS, 8), fill=FAINT)
        ly += 8
    d.text((W / 2, H - 11),
           "Sources: Reuters, AP wires, EU Council, USA Today, The Independent,"
           " Al Jazeera, CaixaBank Research and same-day regional press, 19 Nov 2026.",
           font=font(SANS, 8), fill=FAINT, anchor="ma")
    return img


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    build().save(os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
