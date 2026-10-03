# geo-quiz-cli

A **geography quiz game** in **pure Python** — no dependencies.

## Run it

```bash
python3 quiz.py
```

Pick a mode from the menu:

| # | Mode | What it is |
|---|------|------------|
| 1 | **capitals** | classic 10-round multiple-choice quiz — name the capital (48 countries) |
| 2 | **flags** | 8 rounds — a flag is drawn live in ANSI colors, guess the country (16 flags) |
| 3 | **outlines** | 8 rounds — a country's map shape in ASCII art, guess the country (10 shapes) |
| 4 | **lightning** | 10 capitals, 10 seconds each, no multiple choice — type fast! |
| 5 | **high scores** | persistent local leaderboard (`highscores.json`) with player names |

## How it works

- **Flag engine:** each flag is a 24×9 grid of single-character color
  codes (`'R'` → red, `'O'` → saffron, …) mapped to ANSI background
  colors — circles, diamonds, and Nordic crosses are generated with
  tiny geometry helpers (`_disk`, `_diamond`, `_nordic`).
- **Lightning timer:** `input_timeout()` puts the terminal in cbreak
  mode and uses `select()` on stdin, so keypresses arrive instantly and
  a live `[ 9.8s]` countdown redraws while you type. Falls back to
  plain `input()` where timers aren't available.
- **High scores:** every mode records `{name, mode, score, date}` to
  `highscores.json` next to `quiz.py`; the table survives between runs.
- The classic capitals quiz is unchanged: each round samples a country,
  picks 3 random wrong capitals as distractors, and shuffles the four
  options — so the quiz is different every time.
- Still one file, still zero dependencies: `python3 quiz.py` just works.

## Try changing

- `ROUNDS`, `FLAG_ROUNDS`, `OUTLINE_ROUNDS`, `LIGHTNING_TIME`.
- Add your own flag to `FLAGS` — one grid of color codes.
- Add a country shape to `OUTLINES` — a few lines of `#`.

Built by [Mohammad Ali](https://github.com/AliRender13).

## In the wild

- 🎬 [Code walkthrough video on LinkedIn](https://www.linkedin.com/feed/update/urn:li:activity:7512026440117379073/) — watch a full quiz round play out in 50 seconds.
