# SPDX-License-Identifier: MIT
"""THE WORLD IN ONE DAY - Thursday 19 November 2026.

A one-image world-news poster for make.fun's news-image-20261119 bounty.
The program draws the whole front page itself - masthead, UTC timeline,
dot-matrix world map with numbered pins, 17 illustrated feature panels,
35 numbered briefs, a by-the-numbers box, a weather & disaster box and a
date-check box - with a small software rasterizer written for this entry
(pure Python standard library: no network, no external assets, fully
deterministic). Every story was reported on 19 November 2026 by the
outlet named on the page; SOURCES.md maps each number to its report.

Run:  python3 main.py            (writes /output/entry.png)
      MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import struct
import zlib

W, H = 1024, 1024


# ---------------------------------------------------------------- PNG out
def save_png(path, w, h, rgb):
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, col):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(col)

    def rect(self, x, y, w, h, col):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        row = bytes(col) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def frame(self, x, y, w, h, col, t=1):
        self.rect(x, y, w, t, col)
        self.rect(x, y + h - t, w, t, col)
        self.rect(x, y, t, h, col)
        self.rect(x + w - t, y, t, h, col)

    def line(self, x0, y0, x1, y1, col, t=1):
        dx, dy = x1 - x0, y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        r = t // 2
        for i in range(steps + 1):
            x = x0 + dx * i // steps
            y = y0 + dy * i // steps
            self.rect(x - r, y - r, t, t, col)

    def circle(self, cx, cy, r, col, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill and d2 <= r * r:
                    self.set(xx, yy, col)
                elif not fill and r * r - 2 * r <= d2 <= r * r + 2 * r:
                    self.set(xx, yy, col)

    def poly(self, pts, col):
        ys = [p[1] for p in pts]
        for yy in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    xs.append(x0 + (yy - y0) * (x1 - x0) // (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.rect(xs[i], yy, xs[i + 1] - xs[i] + 1, 1, col)


# ---------------------------------------------------------------- font
# Hand-drawn 5x7 pixel font (this entry's own letterforms), one entry per
# character: seven rows of five bits, top row first.
_G = {
    " ": "00000 00000 00000 00000 00000 00000 00000",
    "A": "01110 10001 10001 11111 10001 10001 10001",
    "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110",
    "D": "11100 10010 10001 10001 10001 10010 11100",
    "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111",
    "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110",
    "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 10001 11001 10101 10011 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101",
    "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110",
    "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010",
    "X": "10001 01010 00100 00100 00100 01010 10001",
    "Y": "10001 01010 00100 00100 00100 00100 00100",
    "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110",
    "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111",
    "3": "11111 00010 00100 00010 00001 10001 01110",
    "4": "00010 00110 01010 10010 11111 00010 00010",
    "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110",
    "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110",
    "9": "01110 10001 10001 01111 00001 00010 01100",
    ".": "00000 00000 00000 00000 00000 01100 01100",
    ",": "00000 00000 00000 00000 01100 00100 01000",
    ":": "00000 01100 01100 00000 01100 01100 00000",
    ";": "00000 01100 01100 00000 01100 00100 01000",
    "'": "00100 00100 01000 00000 00000 00000 00000",
    "-": "00000 00000 00000 01110 00000 00000 00000",
    "/": "00001 00010 00010 00100 01000 01000 10000",
    "(": "00010 00100 01000 01000 01000 00100 00010",
    ")": "01000 00100 00010 00010 00010 00100 01000",
    "!": "00100 00100 00100 00100 00100 00000 00100",
    "?": "01110 10001 00001 00110 00100 00000 00100",
    "%": "11001 11010 00010 00100 01000 01011 10011",
    "+": "00000 00100 00100 01110 00100 00100 00000",
    "&": "01100 10010 10100 01000 10101 10010 01101",
    "$": "00100 01111 10100 01110 00101 11110 00100",
    "#": "01010 01010 11111 01010 11111 01010 01010",
    "@": "01110 10001 10111 10101 10110 10000 01110",
    "*": "00000 00100 10101 01110 10101 00100 00000",
    '"': "01010 01010 00000 00000 00000 00000 00000",
    "<": "00010 00100 01000 10000 01000 00100 00010",
    ">": "01000 00100 00010 00001 00010 00100 01000",
    "=": "00000 00000 11111 00000 11111 00000 00000",
    "_": "00000 00000 00000 00000 00000 00000 11111",
    "[": "01110 01000 01000 01000 01000 01000 01110",
    "]": "01110 00010 00010 00010 00010 00010 01110",
}
FONT = {c: [int(r, 2) for r in rows.split()] for c, rows in _G.items()}


def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, s, col, scale=1, bold=False):
    for ch in s.upper():
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = glyph[row]
            for b in range(5):
                if bits & (1 << (4 - b)):
                    cv.rect(x + b * scale, y + row * scale, scale, scale, col)
                    if bold:
                        cv.rect(x + b * scale + scale, y + row * scale,
                                scale, scale, col)
        x += 6 * scale + (scale if bold else 0)
    return x


def wrap(s, max_chars):
    lines, cur = [], ""
    for word in s.split():
        if len(cur) + (1 if cur else 0) + len(word) <= max_chars:
            cur = cur + (" " if cur else "") + word
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_block(cv, x, y, s, col, scale, max_chars, line_h, bold=False,
               max_lines=None):
    lines = wrap(s, max_chars)
    if max_lines:
        lines = lines[:max_lines]
    for ln in lines:
        draw_text(cv, x, y, ln, col, scale, bold)
        y += line_h
    return y


# ---------------------------------------------------------------- palette
PAPER = (247, 243, 234)
INK = (18, 24, 38)
FAINT = (90, 96, 110)
RED = (178, 34, 40)
BLUE = (27, 73, 128)
TEAL = (10, 110, 108)
GOLD = (176, 124, 18)
GREEN = (46, 110, 52)
PURPLE = (96, 52, 140)
SLATE = (62, 72, 88)
ORANGE = (196, 96, 20)
WHITE = (255, 255, 255)
SKY = (214, 228, 240)
SAND = (238, 226, 196)
PALE = (233, 228, 214)

REGION_COL = {
    "ASIA-PACIFIC": TEAL, "EUROPE": BLUE, "MIDDLE EAST": GOLD,
    "NORTH AMERICA": RED, "AFRICA": GREEN, "LATIN AMERICA": PURPLE,
    "CLIMATE": GREEN, "WORLD COURT": SLATE, "MARKETS": SLATE,
    "TECH": SLATE, "CULTURE": PURPLE, "SPORT": ORANGE,
}

# ------------------------------------------------------------- world map
# Dot-matrix world map, 92 x 42 cells. LAND[row] lists (first, last) land
# cell spans for that row, sketched from the standard world outline.
LAND = {
    1: [(35, 39)],
    2: [(14, 16), (20, 24), (34, 40), (48, 48), (60, 63), (70, 75)],
    3: [(4, 8), (12, 18), (22, 26), (33, 41), (55, 62), (68, 76), (82, 90)],
    4: [(3, 10), (11, 30), (34, 40), (47, 52), (53, 91)],
    5: [(3, 11), (11, 31), (35, 39), (41, 41), (47, 53), (54, 91)],
    6: [(4, 10), (12, 32), (37, 38), (44, 45), (47, 53), (54, 90)],
    7: [(12, 33), (44, 46), (47, 55), (56, 89)],
    8: [(13, 33), (44, 46), (45, 57), (58, 88)],
    9: [(13, 32), (44, 58), (59, 87)],
    10: [(13, 31), (44, 58), (63, 79), (81, 83)],
    11: [(13, 30), (43, 46), (48, 50), (51, 59), (60, 70), (71, 82), (80, 83)],
    12: [(13, 30), (43, 58), (55, 62), (60, 66), (64, 69), (70, 81), (80, 82)],
    13: [(14, 28), (42, 59), (55, 60), (64, 69), (72, 79)],
    14: [(15, 23), (42, 59), (56, 60), (64, 68), (70, 74), (76, 78)],
    15: [(16, 22), (42, 58), (57, 60), (64, 68), (70, 74), (76, 78)],
    16: [(20, 24), (43, 57), (65, 67), (70, 73), (77, 77)],
    17: [(25, 30), (43, 57), (65, 66), (70, 73)],
    18: [(26, 33), (44, 56), (69, 72)],
    19: [(26, 35), (45, 56), (69, 74), (77, 80)],
    20: [(27, 36), (46, 56), (70, 76), (79, 82)],
    21: [(27, 36), (46, 57), (71, 78), (81, 84)],
    22: [(27, 35), (47, 57), (82, 86)],
    23: [(28, 34), (48, 57), (76, 79), (82, 84)],
    24: [(28, 34), (48, 57), (57, 59), (75, 85)],
    25: [(28, 33), (49, 56), (57, 58), (75, 86)],
    26: [(28, 32), (49, 56), (57, 58), (75, 86)],
    27: [(28, 31), (50, 55), (76, 85)],
    28: [(28, 30), (50, 54), (77, 84)],
    29: [(28, 30), (80, 84)],
    30: [(28, 29)],
    31: [(28, 29), (89, 90)],
    32: [(28, 28), (88, 89)],
    33: [(28, 28)],
}
MAP_COLS, MAP_ROWS, CELL = 92, 42, 4


def draw_map(cv, x, y):
    cv.rect(x - 6, y - 6, MAP_COLS * CELL + 12, MAP_ROWS * CELL + 12, SKY)
    for row, spans in LAND.items():
        for a, b in spans:
            for c in range(a, b + 1):
                cv.circle(x + c * CELL + 1, y + row * CELL + 1, 1,
                          (120, 148, 108))
    return x, y


def pin_xy(x, y, lat, lon):
    return (x + int((lon + 180) / 360 * MAP_COLS * CELL),
            y + int((90 - lat) / 180 * MAP_ROWS * CELL))


# story number -> (lat, lon) for the map pins
PINS = {
    1: (22.5, 114.1), 2: (52.1, 4.3), 3: (44.9, 34.1), 4: (51.1, 6.9),
    5: (14.7, -17.3), 6: (36.9, 30.7), 7: (40.7, -74.0), 8: (41.5, -73.0),
    9: (27.0, -81.0), 10: (43.0, -87.9), 11: (23.8, 90.4),
    12: (24.6, 46.7), 13: (10.5, -66.9), 14: (3.1, 101.7),
    15: (-6.2, 106.8), 16: (9.0, 38.7), 17: (51.5, 0.0),
}


# ---------------------------------------------------------------- content
# Every story below was reported on Thursday 19 November 2026 by the
# outlet credited on the page. See SOURCES.md for the full mapping.
LEAD = {
    "n": 1, "region": "ASIA-PACIFIC", "place": "SHENZHEN, CHINA",
    "head": "TRUMP, XI AND PUTIN HOLD FIRST-EVER THREE-WAY SUMMIT",
    "body": ("The presidents of the United States, China and Russia met for "
             "90 minutes on the sidelines of the APEC summit in Shenzhen - "
             "the first trilateral talks between the three powers. Ukraine, "
             "the Iran war, nuclear weapons, trade and artificial "
             "intelligence were all on the table. The joint statement that "
             "followed promised only cooperation on trade, technology and "
             "economic growth: pledges, not breakthroughs. Putin said all "
             "three shared an interest in resolving the war in Ukraine. "
             "Trump called Xi his friend."),
    "credit": "USA TODAY / AJU PRESS",
    "proof": "PROOF: ON THE RECORD AT APEC - SHENZHEN, 19 NOV",
}

# (number, region, place, headline, body, credit, art-key)
FEATURES = [
    (2, "WORLD COURT", "THE HAGUE",
     "WORLD COURT DELIVERS JUDGMENT IN ROHINGYA GENOCIDE CASE",
     "ICJ judgment in The Gambia v. Myanmar: 10,000 Rohingya killed "
     "in 2017, 815,000 targeted, systematic hate speech.",
     "REUTERS LIVE / TBS", "court"),
    (3, "EUROPE", "CRIMEA - BERLIN",
     "CRIMEA BRIDGE HIT A THIRD TIME; ALLIES GATHER IN BERLIN",
     "Traffic on the 19-km bridge was suspended after a third Ukrainian "
     "attack this week. In Berlin, Ukraine's backers met in a show of "
     "support.",
     "THE INDEPENDENT / REUTERS", "bridge"),
    (4, "EUROPE", "GERMANY",
     "IG METALL CALLS 24-HOUR STRIKES AT CAR AND STEEL PLANTS",
     "Germany's largest union called Friday walkouts at hundreds of "
     "auto and steel firms in a pay fight covering 3.7 million workers. "
     "It wants 5%.",
     "REUTERS", "factory"),
    (5, "AFRICA", "SENEGAL",
     "DOZENS MISSING AS MIGRANT BOAT CAPSIZES OFF SENEGAL",
     "A boat with about 50 Europe-bound migrants capsized off Yenne, "
     "south of Dakar; dozens missing. 8,200 reached the Canaries in 12 "
     "days.",
     "REUTERS", "boat"),
    (6, "CLIMATE", "ANTALYA, TURKIYE",
     "COP31 ENTERS ITS FINAL STRETCH, DIVIDED OVER FOSSIL FUELS",
     "A new draft decision was due Thursday, with the fossil-fuel "
     "phase-out wording, adaptation money and transition finance "
     "unresolved.",
     "REUTERS / OCI", "sun"),
    (7, "MARKETS", "NEW YORK",
     "HAWKISH FED MINUTES; WALL STREET SLIPS A FIFTH DAY",
     "Minutes showed October's hold was a close call; nearly all "
     "officials expect more hikes. Gold fell 3% to $3,725.",
     "CAIXABANK RESEARCH", "chart"),
    (8, "TECH", "NEW YORK",
     "ANTHROPIC MAKES ITS NASDAQ DEBUT, PRICED AT $83",
     "The AI lab's shares were set to open on Nasdaq as ANT after an "
     "IPO priced at $83 - reported to raise about $90 billion, the "
     "largest debut ever.",
     "IC / NORDFX", "bell"),
    (9, "CULTURE", "WORLDWIDE",
     "GTA VI LAUNCH DAY: VICE CITY OPENS AT MIDNIGHT",
     "Grand Theft Auto VI went on sale for PS5 and Xbox Series X|S, "
     "unlocking at midnight per time zone after two delays. Download: "
     "some 212 GB.",
     "ROCKSTAR / PRESS REPORTS", "palm"),
    (10, "SPORT", "MIAMI",
     "GIANNIS SINKS HIS OLD TEAM AS HEAT BEAT BUCKS 137-130",
     "Facing Milwaukee since his July trade, Antetokounmpo posted "
     "27 points, 13 rebounds, 9 assists. Bucks: 11 straight losses.",
     "REUTERS / FIELD LEVEL MEDIA", "ball"),
    (11, "ASIA-PACIFIC", "DHAKA",
     "BANGLADESH ON LOCKDOWN AS UNREST OVER HASINA FLARES",
     "Security stepped up nationwide for a lockdown day called by "
     "supporters of ex-PM Sheikh Hasina after weeks of arson attacks.",
     "THE DAILY STAR / REUTERS", "shield"),
    (12, "MIDDLE EAST", "RIYADH",
     "SAUDI-LED COALITION REPELS HOUTHI MISSILES AIMED AT RIYADH",
     "The coalition said it turned back Houthi missiles fired toward "
     "Riyadh, a day after Iran struck US bases in the Gulf.",
     "AL JAZEERA", "missile"),
    (13, "LATIN AMERICA", "AT COP31",
     "VENEZUELA PITCHES AI AS ITS PATH TO 'CLEANER OIL'",
     "Venezuela's AI-and-hydrocarbons minister: AI will monitor "
     "methane leaks while output rises to 1.5M barrels a day.",
     "REUTERS", "pump"),
    (14, "ASIA-PACIFIC", "KUALA LUMPUR",
     "UNHCR HALTS REFUGEE REGISTRATION IN MALAYSIA",
     "The UN refugee agency stopped registering asylum seekers after "
     "Malaysia decided to build its own system. Most of those affected "
     "are Rohingya from Myanmar; UNHCR says it backs the transition.",
     "REUTERS", "tent"),
    (15, "ASIA-PACIFIC", "JAKARTA",
     "INDONESIA PASSES ASSET-FORFEITURE LAW",
     "Parliament approved seizing assets tied to corruption and other "
     "crimes without first securing a conviction, for holdings worth at "
     "least 1 billion rupiah (about $54,885), in a plenary vote held on "
     "Thursday.",
     "REUTERS", "gavel"),
    (16, "AFRICA", "ADDIS ABABA",
     "ETHIOPIAN AIRLINES PROBES LOYALTY-PROGRAMME BREACH",
     "Africa's biggest airline is investigating a cyber incident that "
     "hit ShebaMiles, its loyalty scheme with 5.38 million members. "
     "Flights were not disrupted; the scale of the breach is not yet "
     "clear.",
     "REUTERS", "plane"),
    (17, "TECH", "WORLDWIDE",
     "PHP ISSUES CRITICAL SECURITY RELEASE FOR ALL VERSIONS",
     "The PHP team shipped emergency fixes in a 14:00-14:30 UTC window "
     "for every supported branch. The worst flaws are rated CRITICAL, "
     "though they need non-default setups; administrators were urged "
     "to patch at once.",
     "PHP.NET", "server"),
]

BRIEFS = [
    (18, "TRUMP-XI WORKING LUNCH OPENS SUMMIT DAY IN SHENZHEN (AFP)"),
    (19, "APEC'S 21 ECONOMIES MEET: 'PROSPER TOGETHER' (DIPLOMATIC WATCH)"),
    (20, "PUTIN: ALL THREE SHARE INTEREST IN ENDING UKRAINE WAR (USA TODAY)"),
    (21, "MUSK TRAVELS WITH TRUMP TO CHINA, SITS OUT THE TALKS (OFFICIALS)"),
    (22, "RUSSIAN DRONES DAMAGE 29 HOMES, ENERGY SITE IN KYIV REGION (UKRINFORM)"),
    (23, "UKRAINE DRONES HIT 2 RUSSIAN REFINERIES; 184 DOWNED CLAIMED (MOD)"),
    (24, "ZELENSKY: FRONT POSITIONS STRONG IN DONETSK REGION (INDEPENDENT)"),
    (25, "EU APPROVES E-DECLARATION FOR POSTED WORKERS (EU COUNCIL)"),
    (26, "EU PROVISIONAL DEAL TO AMEND METHANE RULES (EU COUNCIL)"),
    (27, "EU ADOPTS CROSS-BORDER ADULT-PROTECTION RULES (EU COUNCIL)"),
    (28, "EU SIGNS OFF SIMPLER CHEMICALS LAW (EU COUNCIL)"),
    (29, "SWISS BANKERS: BANKING OVERHAUL GOES TOO FAR (REUTERS)"),
    (30, "BUCHAREST CONFERENCE TO TACKLE NATO-FLANK HYBRID THREATS (SNSPA)"),
    (31, "QATAR WARNS GULF ESCALATION COULD DERAIL TALKS (ANADOLU)"),
    (32, "BRENT NEAR $92, WTI $82 AS SURPLUS WEIGHS (CAIXABANK)"),
    (33, "NVIDIA -3% DESPITE REVENUE GROWTH OF 103% (TRW WIRE)"),
    (34, "BITCOIN NEAR $62,500 AS RISK APPETITE COOLS (TRW WIRE)"),
    (35, "IEA WORLD ENERGY OUTLOOK 2026 PUBLISHED (OCI)"),
    (36, "GLOBAL SOUTH YOUTH DEMONSTRATE INSIDE COP31 (ASM)"),
    (37, "COP31 DRAFT SEEKS $120BN+ FOR ADAPTATION (ANTALYA REPORTS)"),
    (38, "75 COUNTRIES BACK TURKIYE 35-BY-35 POWER PLEDGE (REUTERS)"),
    (39, "POSTGRESQL 19 REACHES GENERAL AVAILABILITY (RELEASE TEAM)"),
    (40, "INDIA-NEW ZEALAND FIRST TEST OPENS IN WELLINGTON (INDIAN REPORTS)"),
    (41, "SINDHU BACK IN WORLD TOP FIVE; SEN IN TOP TEN (INDIAN REPORTS)"),
    (42, "VAISHALI WINS BY FORFEIT AT TOTAL CHESS (INDIAN REPORTS)"),
    (43, "ROCKETS 119, PACERS 104 - DURANT 21 (REUTERS/FLM)"),
    (44, "NUGGETS 105, CELTICS 101; JAZZ 109, LAKERS 97 (FLM)"),
    (45, "MAVERICKS 116, WARRIORS 94; BULLS 137, NETS 107 (FLM)"),
    (46, "GRIZZLIES 124, CAVS 121; 76ERS 121, MAGIC 115 (FLM)"),
    (47, "WIZARDS 103, RAPTORS 99 (REUTERS/FLM)"),
    (48, "NIGERIA NGX FALLS AGAIN; ARADEL -10% (TRW WIRE)"),
    (49, "INDIA SEALS DEFENCE DEALS WITH ISRAEL, JAPAN (INDIAN REPORTS)"),
    (50, "GOLDMAN UPGRADES INDIA TO OVERWEIGHT (INDIAN REPORTS)"),
    (51, "DELHI-NCR SCHOOLS REOPEN; GRAP-III LIFTED (INDIAN REPORTS)"),
    (52, "ICJ: MYANMAR FAILED TO INVESTIGATE ATROCITIES (BBC VIA TBS)"),
]

TIMELINE = [
    "00:00 LOCAL - GTA VI UNLOCKS WORLDWIDE",
    "01:58 - UNHCR HALTS MALAYSIA REGISTRATION",
    "04:45 - TRUMP-XI WORKING LUNCH, SHENZHEN",
    "04:50 - INDONESIA FORFEITURE LAW PASSES",
    "06:30 - TRUMP-XI-PUTIN THREE-WAY TALKS OPEN",
    "09:00 - ICJ READS ROHINGYA JUDGMENT, THE HAGUE",
    "09:28 - ETHIOPIAN BREACH PROBE",
    "10:17 - IG METALL CALLS STRIKES",
    "14:00 - PHP CRITICAL RELEASE",
    "14:30 - ANTHROPIC OPENS ON NASDAQ",
]

NUMBERS = [
    ("90 MIN", "THE SHENZHEN THREE-WAY TALKS"),
    ("3.7M", "WORKERS IN IG METALL'S PAY FIGHT"),
    ("10,000", "ROHINGYA KILLED IN 2017 - ICJ"),
    ("815,000", "ROHINGYA TARGETED - ICJ"),
    ("8,200", "CANARY ISLAND ARRIVALS IN 12 DAYS"),
    ("5.38M", "LOYALTY MEMBERS IN THE BREACH PROBE"),
    ("$83", "ANTHROPIC'S IPO PRICE PER SHARE"),
    ("19 KM", "THE CRIMEA BRIDGE, EUROPE'S LONGEST"),
]

WEATHER = [
    "CYCLONE AKVAN: ODISHA SHUTS SCHOOLS AND THE RAILWAYS LEAD "
    "PREPAREDNESS AS THE STORM NEARS (INDIAN REPORTS)",
    "WEST AFRICA ROUTE: NEARLY 600 PEOPLE DEAD OR MISSING AT SEA IN "
    "2026 (UNHCR VIA REUTERS)",
    "KYIV REGION: AN ENERGY FACILITY IS HIT AS THE WINTER FRONT "
    "NEARS (UKRINFORM)",
]

LEFT_OUT = [
    "VOYAGER 1 HIT ONE LIGHT-DAY FROM EARTH ON NOV 18 (NASA) - "
    "YESTERDAY'S MILESTONE.",
    "IRAN-US GULF STRIKES WERE NOV 17-18 (WSJ/REUTERS) - IN THE "
    "NOV 18 EDITION.",
    "PELTOLA'S ALASKA WIN WAS CALLED NOV 18 (AP) - YESTERDAY'S NEWS.",
    "SIBERIA PLANE-CRASH REPORT UNCONFIRMED BY ANY WIRE - NOT "
    "PRINTED.",
]


# ------------------------------------------------------------ illustrations
def art_lead(cv, x, y, w, h):
    """Shenzhen skyline under the three leaders' flags."""
    cv.rect(x, y, w, h, (198, 216, 232))
    cv.circle(x + w - 42, y + 22, 13, GOLD)
    base = y + h
    heights = [38, 62, 47, 78, 55, 88, 66, 44, 72, 52, 84, 40]
    bx = x + 4
    for i, bh in enumerate(heights):
        bw = (w - 8) // len(heights)
        cv.rect(bx, base - bh, bw - 3, bh, (52, 68, 96))
        for wy in range(base - bh + 6, base - 6, 9):
            cv.rect(bx + 3, wy, 3, 3, (250, 220, 130))
        bx += bw
    cv.rect(x, base - 2, w, 2, INK)
    fy = y + 8
    for i, kind in enumerate(["us", "cn", "ru"]):
        fx = x + 26 + i * 52
        cv.line(fx, fy, fx, fy + 44, INK, 2)
        if kind == "us":
            for s in range(4):
                cv.rect(fx + 2, fy + s * 5, 26, 3,
                        RED if s % 2 == 0 else WHITE)
            cv.rect(fx + 2, fy, 12, 9, BLUE)
        elif kind == "cn":
            cv.rect(fx + 2, fy, 26, 19, RED)
            cv.circle(fx + 8, fy + 6, 3, GOLD)
            cv.circle(fx + 15, fy + 4, 1, GOLD)
            cv.circle(fx + 16, fy + 9, 1, GOLD)
        else:
            cv.rect(fx + 2, fy, 26, 6, WHITE)
            cv.rect(fx + 2, fy + 6, 26, 6, BLUE)
            cv.rect(fx + 2, fy + 12, 26, 7, RED)


def art_court(cv, x, y, w, h):
    cx = x + w // 2
    cv.poly([(cx - 44, y + 14), (cx + 44, y + 14), (cx, y + 2)], SLATE)
    cv.rect(x + 8, y + 16, w - 16, 4, SLATE)
    for i in range(4):
        cv.rect(x + 14 + i * ((w - 28) // 3), y + 22, 6, h - 32, SLATE)
    cv.rect(x + 8, y + h - 10, w - 16, 4, SLATE)
    cv.rect(x + 4, y + h - 5, w - 8, 3, INK)
    cv.line(cx - 16, y + 24, cx + 16, y + 24, GOLD, 2)
    cv.line(cx - 16, y + 24, cx - 16, y + 30, GOLD, 2)
    cv.line(cx + 16, y + 24, cx + 16, y + 30, GOLD, 2)
    cv.poly([(cx - 22, y + 38), (cx - 10, y + 38), (cx - 16, y + 30)], GOLD)
    cv.poly([(cx + 10, y + 38), (cx + 22, y + 38), (cx + 16, y + 30)], GOLD)


def art_bridge(cv, x, y, w, h):
    wy = y + h - 14
    for i in range(6):
        cv.line(x + 6 + i * (w // 6), wy + 6, x + 16 + i * (w // 6),
                wy + 6, BLUE, 2)
    cv.rect(x + 6, y + 26, w - 12, 4, SLATE)
    for tx in (x + w // 3, x + 2 * w // 3):
        cv.rect(tx, y + 8, 4, 22, SLATE)
        cv.line(tx + 2, y + 8, x + 8, y + 26, SLATE, 1)
        cv.line(tx + 2, y + 8, x + w - 8, y + 26, SLATE, 1)
    bx, by = x + w // 2, y + 24
    for dx, dy in ((-10, 0), (10, 0), (0, -9), (0, 9), (-7, -7), (7, -7),
                   (-7, 7), (7, 7)):
        cv.line(bx, by, bx + dx, by + dy, ORANGE, 2)
    cv.circle(bx, by, 4, GOLD)


def art_factory(cv, x, y, w, h):
    base = y + h - 4
    cv.rect(x + 8, base - 26, w - 40, 26, SLATE)
    cv.poly([(x + 8, base - 26), (x + 26, base - 38), (x + 44, base - 26)],
            SLATE)
    cv.rect(x + w - 30, base - 48, 8, 48, SLATE)
    cv.rect(x + w - 44, base - 40, 7, 40, SLATE)
    for i in range(3):
        cv.circle(x + w - 26 + i * 5, base - 52 - i * 4, 4 - i // 2,
                  (200, 200, 205))
    cv.circle(x + 24, base - 14, 9, GOLD, fill=False)
    for a in range(8):
        import math
        gx = x + 24 + int(11 * math.cos(a * 0.785))
        gy = base - 14 + int(11 * math.sin(a * 0.785))
        cv.rect(gx - 1, gy - 1, 3, 3, GOLD)
    for i in range(3):
        sx = x + w // 2 + i * 16
        cv.line(sx, base, sx, base - 20, RED, 2)
        cv.rect(sx - 5, base - 30, 12, 9, RED)


def art_boat(cv, x, y, w, h):
    cv.circle(x + w - 20, y + 12, 7, GOLD)
    cv.circle(x + w - 24, y + 10, 6, PAPER)
    wy = y + h - 16
    cv.poly([(x + 12, wy), (x + w - 12, wy), (x + w - 24, wy + 9),
             (x + 24, wy + 9)], (120, 66, 30))
    cv.line(x + w // 2, wy, x + w // 2, wy - 30, INK, 2)
    cv.poly([(x + w // 2 + 2, wy - 30), (x + w // 2 + 2, wy - 4),
             (x + w // 2 + 20, wy - 4)], (240, 240, 235))
    for i in range(5):
        cv.line(x + 6 + i * (w // 5), wy + 13, x + 16 + i * (w // 5),
                wy + 13, BLUE, 2)
    for i in range(4):
        cv.circle(x + 26 + i * 14, wy - 3, 3, INK)


def art_sun(cv, x, y, w, h):
    cx, cy = x + 30, y + 24
    cv.circle(cx, cy, 12, GOLD)
    for a in range(8):
        import math
        cv.line(cx + int(15 * math.cos(a * 0.785)),
                cy + int(15 * math.sin(a * 0.785)),
                cx + int(20 * math.cos(a * 0.785)),
                cy + int(20 * math.sin(a * 0.785)), GOLD, 2)
    cv.poly([(x + 58, y + 40), (x + 78, y + 12), (x + 92, y + 38),
             (x + 76, y + 46)], GREEN)
    cv.line(x + 62, y + 40, x + 88, y + 16, GREEN, 1)
    tx = x + w - 18
    cv.rect(tx, y + 8, 5, 30, RED)
    cv.circle(tx + 2, y + 42, 6, RED)
    cv.rect(tx + 1, y + 20, 3, 18, WHITE)


def art_chart(cv, x, y, w, h):
    cv.line(x + 8, y + 6, x + 8, y + h - 10, FAINT, 1)
    cv.line(x + 8, y + h - 10, x + w - 6, y + h - 10, FAINT, 1)
    pts = [(x + 10, y + 12), (x + 30, y + 18), (x + 48, y + 14),
           (x + 66, y + 26), (x + 84, y + 30), (x + w - 12, y + 40)]
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], RED, 2)
    cv.poly([(x + w - 12, y + 46), (x + w - 20, y + 34),
             (x + w - 4, y + 34)], RED)
    for bx, bh in ((x + 16, 12), (x + 34, 18), (x + 52, 10), (x + 70, 20)):
        cv.rect(bx, y + h - 10 - bh, 8, bh, SLATE)


def art_bell(cv, x, y, w, h):
    cx = x + 30
    cv.circle(cx, y + 12, 4, GOLD)
    cv.poly([(cx - 13, y + 34), (cx + 13, y + 34), (cx + 8, y + 16),
             (cx - 8, y + 16)], GOLD)
    cv.rect(cx - 16, y + 34, 32, 4, GOLD)
    cv.circle(cx, y + 42, 4, GOLD)
    draw_text(cv, x + 56, y + 10, "ANT", INK, 2, bold=True)
    cv.line(x + 58, y + 40, x + 78, y + 26, GREEN, 2)
    cv.line(x + 78, y + 26, x + 92, y + 32, GREEN, 2)
    cv.poly([(x + 92, y + 26), (x + 92, y + 38), (x + 84, y + 30)], GREEN)


def art_palm(cv, x, y, w, h):
    cv.rect(x, y, w, h, (250, 214, 170))
    cv.circle(x + w - 24, y + 14, 9, (244, 160, 40))
    tx = x + 26
    for i in range(9):
        cv.line(tx + i, y + h - 8 - i * 3, tx + i + 3, y + h - 8 - i * 3,
                (120, 84, 40), 2)
    top = (tx + 26, y + h - 36)
    for dx, dy in ((-20, -8), (-12, -13), (0, -15), (13, -12), (21, -6)):
        cv.line(top[0], top[1], top[0] + dx, top[1] + dy, GREEN, 2)
    cv.rect(x + 52, y + h - 20, 44, 10, RED)
    cv.rect(x + 60, y + h - 27, 26, 8, RED)
    cv.circle(x + 62, y + h - 9, 5, INK)
    cv.circle(x + 86, y + h - 9, 5, INK)
    cv.rect(x + 66, y + h - 25, 12, 5, SKY)


def art_ball(cv, x, y, w, h):
    cx, cy, r = x + 30, y + 26, 19
    cv.circle(cx, cy, r, ORANGE)
    cv.circle(cx, cy, r, INK, fill=False)
    cv.line(cx - r, cy, cx + r, cy, INK, 1)
    cv.line(cx, cy - r, cx, cy + r, INK, 1)
    cv.line(cx - 12, cy - 15, cx - 12, cy + 15, INK, 1)
    cv.line(cx + 12, cy - 15, cx + 12, cy + 15, INK, 1)
    hx = x + w - 34
    cv.rect(hx, y + 10, 26, 3, RED)
    cv.line(hx + 3, y + 13, hx + 6, y + 26, FAINT, 1)
    cv.line(hx + 12, y + 13, hx + 12, y + 26, FAINT, 1)
    cv.line(hx + 21, y + 13, hx + 18, y + 26, FAINT, 1)
    cv.line(hx + 6, y + 26, hx + 18, y + 26, FAINT, 1)


def art_shield(cv, x, y, w, h):
    for i, bh in enumerate((18, 26, 14)):
        cv.rect(x + 6 + i * 16, y + h - 12 - bh, 11, bh, SLATE)
    pts = [(x + w - 40, y + 6), (x + w - 14, y + 6), (x + w - 14, y + 26),
           (x + w - 27, y + 42), (x + w - 40, y + 26)]
    cv.poly(pts, TEAL)
    cv.poly([(px + 3, py + 3) for px, py in
             [(x + w - 38, y + 10), (x + w - 16, y + 10), (x + w - 16,
              y + 25), (x + w - 27, y + 37), (x + w - 38, y + 25)]],
            (90, 180, 175))
    fx, fy = x + 18, y + 16
    cv.poly([(fx, fy + 12), (fx + 5, fy), (fx + 10, fy + 12),
             (fx + 5, fy + 16)], ORANGE)
    cv.poly([(fx + 3, fy + 12), (fx + 5, fy + 5), (fx + 7, fy + 12),
             (fx + 5, fy + 14)], GOLD)


def art_missile(cv, x, y, w, h):
    for i in range(7):
        cv.line(x + 10 + i * 5, y + 40 - i * 2, x + 16 + i * 5,
                y + 38 - i * 2, FAINT, 1)
    cv.poly([(x + 52, y + 8), (x + 62, y + 14), (x + 46, y + 26),
             (x + 40, y + 18)], RED)
    cv.poly([(x + 40, y + 18), (x + 34, y + 24), (x + 42, y + 26)],
            ORANGE)
    cv.poly([(x + 66, y + 40), (x + 80, y + 26), (x + 94, y + 40)],
            TEAL)
    cv.line(x + 66, y + 40, x + 94, y + 40, TEAL, 2)
    cv.line(x + 62, y + 20, x + 74, y + 30, GOLD, 2)
    cv.line(x + 74, y + 20, x + 62, y + 30, GOLD, 2)


def art_pump(cv, x, y, w, h):
    base = y + h - 6
    cv.line(x + 10, base, x + w - 8, base, INK, 2)
    cv.poly([(x + 30, base), (x + 40, base - 26), (x + 46, base)],
            SLATE)
    cv.line(x + 40, base - 26, x + 82, base - 34, SLATE, 3)
    cv.line(x + 40, base - 26, x + 16, base - 18, SLATE, 3)
    cv.poly([(x + 82, base - 34), (x + 90, base - 28), (x + 82, y + 6)],
            SLATE)
    cv.line(x + 86, base - 28, x + 86, base - 10, INK, 2)
    cv.circle(x + 24, base - 10, 6, GOLD, fill=False)
    for nx, ny in ((x + 58, y + 8), (x + 72, y + 14), (x + 60, y + 20)):
        cv.circle(nx, ny, 2, TEAL)
    cv.line(x + 58, y + 8, x + 72, y + 14, TEAL, 1)
    cv.line(x + 72, y + 14, x + 60, y + 20, TEAL, 1)


def art_tent(cv, x, y, w, h):
    cv.poly([(x + 10, y + h - 8), (x + w // 2, y + 8),
             (x + w - 10, y + h - 8)], (240, 240, 238))
    cv.poly([(x + w // 2 - 10, y + h - 8), (x + w // 2, y + 24),
             (x + w // 2 + 10, y + h - 8)], BLUE)
    cv.line(x + w // 2, y + 8, x + w // 2, y + 2, INK, 1)
    cv.rect(x + w // 2, y + 2, 10, 6, BLUE)
    cv.line(x + 6, y + h - 6, x + w - 6, y + h - 6, INK, 1)


def art_gavel(cv, x, y, w, h):
    cv.rect(x + 8, y + 8, 30, 36, WHITE)
    cv.frame(x + 8, y + 8, 30, 36, FAINT, 1)
    for i in range(4):
        cv.line(x + 12, y + 15 + i * 7, x + 34, y + 15 + i * 7, FAINT, 1)
    cv.line(x + 52, y + 34, x + 78, y + 12, (120, 84, 40), 4)
    cv.rect(x + 72, y + 4, 16, 9, (120, 84, 40))
    cv.rect(x + 70, y + 13, 16, 5, (120, 84, 40))
    cv.line(x + 46, y + 42, x + 58, y + 42, GOLD, 2)
    cv.line(x + 84, y + 40, x + 92, y + 40, GOLD, 2)


def art_plane(cv, x, y, w, h):
    cy = y + 20
    cv.poly([(x + 6, cy), (x + w - 20, cy - 4), (x + w - 6, cy + 2),
             (x + w - 20, cy + 8), (x + 6, cy + 6)], SLATE)
    cv.poly([(x + 14, cy - 2), (x + 24, cy - 12), (x + 32, cy - 2)],
            SLATE)
    cv.poly([(x + 40, cy + 4), (x + 54, cy + 16), (x + 62, cy + 4)],
            SLATE)
    for i in range(6):
        cv.rect(x + 16 + i * 10, cy, 4, 3, SKY)
    lx, ly = x + w - 30, y + 30
    cv.rect(lx, ly + 6, 18, 13, GOLD)
    cv.line(lx + 3, ly + 6, lx + 3, ly, GOLD, 2)
    cv.line(lx + 15, ly + 6, lx + 15, ly + 2, GOLD, 2)
    cv.circle(lx + 9, ly + 12, 3, INK)


def art_server(cv, x, y, w, h):
    for i in range(3):
        sy = y + 6 + i * 13
        cv.rect(x + 10, sy, 44, 10, SLATE)
        cv.circle(x + 16, sy + 5, 2, GREEN)
        cv.rect(x + 24, sy + 3, 24, 2, (140, 150, 165))
    cv.poly([(x + 74, y + 8), (x + 86, y + 30), (x + 62, y + 30)],
            GOLD)
    cv.frame(x + 73, y + 17, 3, 7, INK, 1)
    cv.rect(x + 73, y + 26, 3, 3, INK)


ART = {
    "court": art_court, "bridge": art_bridge, "factory": art_factory,
    "boat": art_boat, "sun": art_sun, "chart": art_chart, "bell": art_bell,
    "palm": art_palm, "ball": art_ball, "shield": art_shield,
    "missile": art_missile, "pump": art_pump, "tent": art_tent,
    "gavel": art_gavel, "plane": art_plane, "server": art_server,
}


# ------------------------------------------------------------- spotlights
# Stories 14-17 run as illustrated spotlights at the head of the briefs.
SPOTLIGHTS = [
    (14, "ASIA-PACIFIC", "UNHCR HALTS MALAYSIA REGISTRATION",
     "UN AGENCY STOPS REGISTERING ASYLUM SEEKERS; MALAYSIA BUILDS ITS "
     "OWN SYSTEM. (REUTERS)", "tent"),
    (15, "ASIA-PACIFIC", "INDONESIA PASSES FORFEITURE LAW",
     "SEIZURE OF CRIME-LINKED ASSETS WITHOUT A CONVICTION, ABOVE "
     "RP1BN IN VALUE. (REUTERS)", "gavel"),
    (16, "AFRICA", "ETHIOPIAN AIRLINES BREACH PROBE",
     "CYBER INCIDENT HITS THE SHEBAMILLES LOYALTY SCHEME AND ITS "
     "5.38M MEMBERS. (REUTERS)", "plane"),
    (17, "TECH", "PHP CRITICAL SECURITY RELEASE",
     "EMERGENCY FIXES FOR ALL SUPPORTED VERSIONS IN A 14:00 UTC "
     "WINDOW. (PHP.NET)", "server"),
]


def mini_art(cv, x, y, key):
    if key == "tent":
        cv.poly([(x + 2, y + 26), (x + 20, y + 4), (x + 38, y + 26)],
                (240, 240, 238))
        cv.poly([(x + 15, y + 26), (x + 20, y + 14), (x + 25, y + 26)],
                BLUE)
    elif key == "gavel":
        cv.line(x + 8, y + 24, x + 26, y + 8, (120, 84, 40), 3)
        cv.rect(x + 22, y + 2, 13, 7, (120, 84, 40))
        cv.line(x + 4, y + 28, x + 34, y + 28, GOLD, 2)
    elif key == "plane":
        cv.poly([(x + 2, y + 16), (x + 30, y + 12), (x + 38, y + 16),
                 (x + 30, y + 20), (x + 2, y + 20)], SLATE)
        cv.poly([(x + 8, y + 14), (x + 15, y + 5), (x + 20, y + 14)],
                SLATE)
    elif key == "server":
        for i in range(3):
            cv.rect(x + 4, y + 3 + i * 9, 24, 7, SLATE)
            cv.circle(x + 8, y + 6 + i * 9, 1, GREEN)
        cv.poly([(x + 34, y + 8), (x + 39, y + 18), (x + 29, y + 18)],
                GOLD)


# ----------------------------------------------------------------- layout
def header_strip(cv, x, y, w, label, col):
    cv.rect(x, y, w, 13, col)
    draw_text(cv, x + 5, y + 3, label, WHITE, 1, bold=True)


def feature_panel(cv, x, y, feat):
    n, region, place, head, body, credit, art = feat
    w, h = 246, 112
    cv.frame(x, y, w, h, INK, 1)
    header_strip(cv, x, y, w, "%d - %s - %s" % (n, region, place),
                 REGION_COL.get(region, SLATE))
    draw_block(cv, x + 6, y + 17, head, INK, 1, 33, 9, bold=True,
               max_lines=2)
    ART[art](cv, x + 4, y + 40, 96, 50)
    draw_block(cv, x + 106, y + 38, body, INK, 1, 22, 8, max_lines=7)
    draw_text(cv, x + 6, y + 100, credit, FAINT, 1)


def box(cv, x, y, w, h, title, lines_fn):
    cv.frame(x, y, w, h, INK, 1)
    cv.rect(x, y, w, 13, INK)
    draw_text(cv, x + 5, y + 3, title, WHITE, 1, bold=True)
    lines_fn(x + 6, y + 18)


def render():
    cv = Canvas(W, H, PAPER)

    # masthead
    draw_text(cv, 10, 8, "THE WORLD IN ONE DAY", INK, 3, bold=True)
    draw_text(cv, 664, 10, "THURSDAY 19 NOVEMBER 2026", RED, 2, bold=True)
    draw_text(cv, 10, 34,
              "ONE IMAGE - EVERY STORY SOURCED AND NUMBERED - 52 STORIES"
              " - 7 REGIONS - 17 ILLUSTRATED PANELS", INK, 1)
    draw_text(cv, 840, 34, "GLOBAL EDITION - NO. 20261119", FAINT, 1)
    cv.rect(0, 44, W, 3, RED)
    cv.rect(0, 49, W, 1, INK)

    # UTC timeline band
    cv.rect(0, 56, W, 34, INK)
    draw_text(cv, 10, 59, "THE DAY IN UTC", GOLD, 1, bold=True)
    tl = "  |  ".join(TIMELINE)
    draw_block(cv, 130, 59, tl, WHITE, 1, 148, 9, max_lines=3)

    # lead panel
    lx, ly, lw, lh = 8, 98, 604, 224
    cv.frame(lx, ly, lw, lh, INK, 2)
    header_strip(cv, lx, ly, lw,
                 "1 - ASIA-PACIFIC - SHENZHEN, CHINA - LEAD STORY", TEAL)
    draw_block(cv, lx + 8, ly + 19, LEAD["head"], INK, 2, 42, 17,
               bold=True, max_lines=2)
    art_lead(cv, lx + 8, ly + 58, lw - 16, 86)
    draw_block(cv, lx + 8, ly + 150, LEAD["body"], INK, 1, 97, 9,
               max_lines=6)
    cv.rect(lx + 8, ly + 206, lw - 16, 13, SAND)
    draw_text(cv, lx + 12, ly + 209, LEAD["proof"], INK, 1, bold=True)
    draw_text(cv, lx + lw - 8 - text_w(LEAD["credit"], 1), ly + 209,
              LEAD["credit"], FAINT, 1)

    # map panel
    mx, my, mw = 620, 98, 396
    cv.frame(mx, my, mw, 224, INK, 2)
    header_strip(cv, mx, my, mw, "THE DAY ON THE MAP", BLUE)
    draw_text(cv, mx + 8, my + 17,
              "PINS MATCH THE STORY NUMBERS", FAINT, 1)
    gx, gy = mx + 14, my + 28
    draw_map(cv, gx, gy)
    for n, (lat, lon) in PINS.items():
        px, py = pin_xy(gx, gy, lat, lon)
        cv.circle(px, py, 6, RED)
        label = str(n)
        draw_text(cv, px - (5 if len(label) == 1 else 8), py - 3,
                  label, WHITE, 1, bold=True)
    draw_block(cv, mx + 8, my + 204,
               "1 SHENZHEN 2 HAGUE 3 CRIMEA 4 GERMANY 5 SENEGAL 6 ANTALYA "
               "7-8 NEW YORK 9 FLORIDA 10 MILWAUKEE 11 DHAKA 12 RIYADH "
               "13 CARACAS 14 KUALA LUMPUR 15 JAKARTA 16 ADDIS 17 GREENWICH",
               INK, 1, 64, 8, max_lines=3)

    # feature rows (stories 2-13)
    rows_y = [330, 450, 570]
    for i, feat in enumerate(FEATURES[:12]):
        x = 8 + (i % 4) * 254
        y = rows_y[i // 4]
        feature_panel(cv, x, y, feat)

    # boxes strip
    by = 690

    def numbers_fn(x, y):
        for big, small in NUMBERS:
            draw_text(cv, x, y, big, RED, 1, bold=True)
            draw_text(cv, x + text_w(big, 1) + 12, y, "- " + small, INK, 1)
            y += 8

    def weather_fn(x, y):
        for item in WEATHER:
            y = draw_block(cv, x, y, item, INK, 1, 53, 8) + 3

    def leftout_fn(x, y):
        for item in LEFT_OUT:
            y = draw_block(cv, x, y, item, INK, 1, 53, 8) + 1

    box(cv, 8, by, 330, 88, "BY THE NUMBERS", numbers_fn)
    box(cv, 346, by, 330, 88, "WEATHER AND DISASTER", weather_fn)
    box(cv, 684, by, 330, 88, "LEFT OUT - AND WHY (DATE CHECK)",
        leftout_fn)

    # briefs
    draw_text(cv, 8, 786,
              "MORE OF THE DAY - STORIES 14 TO 52, IN BRIEF", INK, 1,
              bold=True)
    draw_text(cv, 560, 786,
              "EVERY BRIEF NAMES ITS OUTLET; FULL CITATIONS IN SOURCES.MD",
              FAINT, 1)
    cv.rect(0, 796, W, 1, INK)
    cols_x = [8, 262, 516, 770]
    col_w, top, bottom = 246, 800, 1018
    col = 0
    y = top
    blocks = []
    for n, region, head, body, key in SPOTLIGHTS:
        blocks.append(("spot", n, region, head, body, key))
    for n, text in BRIEFS:
        blocks.append(("brief", n, text))
    for blk in blocks:
        if blk[0] == "spot":
            _, n, region, head, body, key = blk
            head_lines = wrap(head, 33)
            body_lines = wrap(body, 33)
            need = 9 + (len(head_lines) + len(body_lines)) * 8 + 5
            if y + need > bottom:
                col += 1
                y = top
            if col > 3:
                break
            x = cols_x[col]
            mini_art(cv, x + 2, y + 6, key)
            draw_text(cv, x + 48, y, "%d - %s" % (n, region),
                      REGION_COL.get(region, SLATE), 1, bold=True)
            yy = y + 9
            for ln in head_lines:
                draw_text(cv, x + 48, yy, ln, INK, 1, bold=True)
                yy += 8
            for ln in body_lines:
                draw_text(cv, x + 48, yy, ln, INK, 1)
                yy += 8
            y += need
        else:
            _, n, text = blk
            full = "%d. %s" % (n, text)
            lines = wrap(full, 39)
            need = len(lines) * 8 + 2
            if y + need > bottom:
                col += 1
                y = top
            if col > 3:
                break
            x = cols_x[col]
            for ln in lines:
                draw_text(cv, x, y, ln, INK, 1)
                y += 8
            y += 2
    return cv


def main():
    cv = render()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    save_png(os.path.join(out_dir, "entry.png"), W, H, cv.px)


if __name__ == "__main__":
    main()
