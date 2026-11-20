# The World in One Day — Thursday 19 November 2026

A one-image poster of the world's news on Thursday 19 November 2026,
drawn programmatically with Python and Pillow: 52 stories from named
outlets in 7 region columns, 17 illustrated panels for the featured
stories, a dot-matrix world map with a pin per featured story, a UTC
timeline of the day, a by-the-numbers strip, a markets strip and a
date-check box listing what was left out and why.

Every story was reported on 19 November 2026 by the outlet named beside
it; the full sourcing notes are in SOURCES.md (Reuters and AP wires,
the EU Council press list, USA Today, The Independent, Al Jazeera,
CaixaBank Research and same-day regional press).

The program is deterministic — the same `entry.png` bytes on every run —
and needs no network.

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Writes `entry.png` (1024x1024) to `$MAKEFUN_OUTPUT_DIR` (default
`/output`).

[![Bounty](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![Rank](https://make.fun/badge/news-image-20261119/salikamarlisa3-cell/global-edition-news-image-20261119/rank.svg)](https://make.fun/bounty/news-image-20261119/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![Reward](https://make.fun/badge/news-image-20261119/salikamarlisa3-cell/global-edition-news-image-20261119/reward.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
