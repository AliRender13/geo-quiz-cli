"""
geo-quiz-cli
A geography quiz game in pure Python (no dependencies).

Four game modes:
  1. capitals  - classic 10-round multiple-choice quiz (the original)
  2. flags     - guess the country from its flag, drawn in ANSI colors
  3. outlines  - guess the country from its ASCII map outline
  4. lightning - capitals against the clock (10 seconds each)

Plus a persistent local high-score table (highscores.json).

Run:
    python3 quiz.py
"""
import json
import os
import random
import sys
import time

# ---------------------------------------------------------------------------
# country data (kept from the original)
# ---------------------------------------------------------------------------

COUNTRIES = [
    ("India", "New Delhi"), ("France", "Paris"), ("Japan", "Tokyo"),
    ("Brazil", "Brasilia"), ("Egypt", "Cairo"), ("Canada", "Ottawa"),
    ("Australia", "Canberra"), ("Germany", "Berlin"), ("Italy", "Rome"),
    ("Spain", "Madrid"), ("Mexico", "Mexico City"), ("Argentina", "Buenos Aires"),
    ("South Africa", "Pretoria"), ("Nigeria", "Abuja"), ("Kenya", "Nairobi"),
    ("China", "Beijing"), ("Russia", "Moscow"), ("United Kingdom", "London"),
    ("United States", "Washington, D.C."), ("South Korea", "Seoul"),
    ("Thailand", "Bangkok"), ("Vietnam", "Hanoi"), ("Indonesia", "Jakarta"),
    ("Turkey", "Ankara"), ("Greece", "Athens"), ("Portugal", "Lisbon"),
    ("Netherlands", "Amsterdam"), ("Sweden", "Stockholm"), ("Norway", "Oslo"),
    ("Finland", "Helsinki"), ("Poland", "Warsaw"), ("Ukraine", "Kyiv"),
    ("Saudi Arabia", "Riyadh"), ("UAE", "Abu Dhabi"), ("Iran", "Tehran"),
    ("Pakistan", "Islamabad"), ("Bangladesh", "Dhaka"), ("Nepal", "Kathmandu"),
    ("Sri Lanka", "Sri Jayawardenepura Kotte"), ("Myanmar", "Naypyidaw"),
    ("Malaysia", "Kuala Lumpur"), ("Singapore", "Singapore"),
    ("New Zealand", "Wellington"), ("Peru", "Lima"), ("Chile", "Santiago"),
    ("Colombia", "Bogota"), ("Ethiopia", "Addis Ababa"), ("Morocco", "Rabat"),
]

ROUNDS = 10
LETTERS = "ABCD"

# ---------------------------------------------------------------------------
# flag art: each flag is a list of strings; every character maps to an
# ANSI background color (see ANSI_BG / ANSI_BG_256), rendered 2 spaces wide.
# ---------------------------------------------------------------------------

ANSI_BG = {
    'K': 40, 'R': 41, 'G': 42, 'Y': 43,
    'B': 44, 'M': 45, 'C': 46, 'W': 47,
}
ANSI_BG_256 = {'O': 208, 'N': 21, 'E': 34, 'S': 33}  # saffron, navy, ...


def _cell(ch):
    if ch in ANSI_BG:
        return f"\033[{ANSI_BG[ch]}m  "
    return f"\033[48;5;{ANSI_BG_256[ch]}m  "


def show_flag(rows):
    for row in rows:
        print(''.join(_cell(c) for c in row) + "\033[0m")


def _disk(w, h, cx, cy, r, fg, bg):
    rows = []
    for y in range(h):
        s = ''
        for x in range(w):
            s += fg if (x - cx) ** 2 + ((y - cy) * 2) ** 2 <= r * r else bg
        rows.append(s)
    return rows


def _diamond(w, h, cx, cy, a, b, fg, bg):
    rows = []
    for y in range(h):
        s = ''
        for x in range(w):
            s += fg if abs(x - cx) / a + abs(y - cy) * 2 / b <= 1 else bg
        rows.append(s)
    return rows


def _stripes(w, h, bands):
    rows = []
    for n, ch in bands:
        rows += [ch * w] * n
    return rows


def _union_jack(w=24, h=9):
    rows = []
    for y in range(h):
        s = ''
        for x in range(w):
            dx = x - (w - 1) / 2
            dy = (y - (h - 1) / 2) * 2
            d = abs(abs(dx) / 2.4 - abs(dy))  # distance from the diagonals
            if x in (11, 12) or y == 4:
                s += 'R'
            elif 10 <= x <= 13 or 3 <= y <= 5:
                s += 'W'
            elif d < 0.55:
                s += 'R'
            elif d < 1.5:
                s += 'W'
            else:
                s += 'B'
        rows.append(s)
    return rows


def _nordic(bg, cross, cx0=7, cw=3, cy0=3, chh=3, w=24, h=9):
    rows = []
    for y in range(h):
        s = ''
        for x in range(w):
            s += cross if (cx0 <= x < cx0 + cw or cy0 <= y < cy0 + chh) else bg
        rows.append(s)
    return rows


def _norway(w=24, h=9):
    rows = []
    for y in range(h):
        s = ''
        for x in range(w):
            white = 6 <= x < 11 or 3 <= y < 6
            blue = white and (8 <= x < 10 or y == 4)
            s += 'B' if blue else ('W' if white else 'R')
        rows.append(s)
    return rows


def _greece(w=24, h=9):
    rows = []
    for y in range(h):
        s = ''
        for x in range(w):
            if x < 7 and y < 5:  # canton with cross
                s += 'W' if (2 <= x <= 4 or 1 <= y <= 3) else 'B'
            else:
                s += 'B' if y % 2 == 0 else 'W'
        rows.append(s)
    return rows


def _canada(w=24, h=9):
    rows = ['R' * 6 + 'W' * 12 + 'R' * 6 for _ in range(h)]
    leaf = [  # simplified maple leaf
        "....RR....",
        "...RRRR...",
        ".RRRRRRRR.",
        "...RRRR...",
        "....RR....",
    ]
    rows = [list(r) for r in rows]
    for i, line in enumerate(leaf):
        for j, ch in enumerate(line):
            if ch == 'R':
                rows[2 + i][7 + j] = 'R'
    return [''.join(r) for r in rows]


def _egypt(w=24, h=9):
    rows = [list(r) for r in _stripes(w, h, [(3, 'R'), (3, 'W'), (3, 'K')])]
    for y in (3, 4, 5):  # simplified eagle emblem
        for x in (11, 12):
            rows[y][x] = 'Y'
    return [''.join(r) for r in rows]


def _india(w=24, h=9):
    rows = []
    for y in range(h):
        s = ''
        for x in range(w):
            if y < 3:
                s += 'O'  # saffron
            elif y > 5:
                s += 'G'  # green
            else:
                s += 'N' if (x - 11.5) ** 2 + ((y - 4) * 2) ** 2 <= 1.7 ** 2 else 'W'
        rows.append(s)
    return rows


def _brazil(w=24, h=9):
    rows = [list(r) for r in _diamond(w, h, 11.5, 4, 10, 7, 'Y', 'G')]
    for y in range(h):
        for x in range(w):
            if (x - 11.5) ** 2 + ((y - 4) * 2) ** 2 <= 2.2 ** 2:
                rows[y][x] = 'B'  # celestial globe
    return [''.join(r) for r in rows]


FLAGS = {
    "India": _india(),
    "France": ['B' * 8 + 'W' * 8 + 'R' * 8 for _ in range(9)],
    "Japan": _disk(24, 9, 11.5, 4, 3.0, 'R', 'W'),
    "Germany": _stripes(24, 9, [(3, 'K'), (3, 'R'), (3, 'Y')]),
    "Italy": ['G' * 8 + 'W' * 8 + 'R' * 8 for _ in range(9)],
    "Spain": _stripes(24, 9, [(2, 'R'), (5, 'Y'), (2, 'R')]),
    "Netherlands": _stripes(24, 9, [(3, 'R'), (3, 'W'), (3, 'B')]),
    "Russia": _stripes(24, 9, [(3, 'W'), (3, 'B'), (3, 'R')]),
    "Brazil": _brazil(),
    "Canada": _canada(),
    "United Kingdom": _union_jack(),
    "Sweden": _nordic('B', 'Y'),
    "Norway": _norway(),
    "Greece": _greece(),
    "Nigeria": ['G' * 8 + 'W' * 8 + 'G' * 8 for _ in range(9)],
    "Egypt": _egypt(),
}

# ---------------------------------------------------------------------------
# country outlines: hand-drawn simplified ASCII map shapes
# ---------------------------------------------------------------------------

OUTLINES = {
    "Italy": [
        "            ####",
        "           ######",
        "           ######",
        "            #####",
        "            ####",
        "            ###",
        "           ###",
        "           ###",
        "          ###",
        "         ###",
        "       ####",
        "     ######",
        "   ########",
    ],
    "India": [
        "   ############",
        "  ##############",
        " ###############",
        "  ##############",
        "  #############",
        "   ############",
        "   ###########",
        "    #########",
        "    ########",
        "     ######",
        "     #####",
        "      ###",
        "      ##",
    ],
    "France": [
        "    ########",
        "  ############",
        " ##############",
        " ##############",
        " #############",
        "  ############",
        "  ###########",
        "   #########",
        "   ########",
        "    ######",
    ],
    "United Kingdom": [
        "      ####",
        "    ########",
        "   ##########",
        "   #########",
        "    ########",
        "     ######",
        "      #####",
        "      ####",
        "       ###",
    ],
    "Japan": [
        "      ##",
        "     ####",
        "    ######",
        "     ####",
        "      ###",
        "       ###",
        "        ###",
        "        ####",
        "         ###",
        "          ##",
    ],
    "Brazil": [
        "  ################",
        " ##################",
        "####################",
        "#####################",
        " ###################",
        "  #################",
        "   ###############",
        "    #############",
        "     ###########",
        "      #########",
        "       #######",
        "        #####",
    ],
    "Australia": [
        "      ########",
        "   ###############",
        "  ##################",
        " ####################",
        "######################",
        " ####################",
        "  ##################",
        "   ####  ##########",
        "         ########",
        "          ######",
    ],
    "Spain": [
        "  ##############",
        " ################",
        "##################",
        "###################",
        "###################",
        " #################",
        "  ###############",
        "   #############",
        "    ###########",
    ],
    "Egypt": [
        "##################",
        "###################",
        "###################",
        "###################",
        " ##################",
        "  ################",
        "   ##############",
        "    ############",
    ],
    "United States": [
        "  ######################",
        "########################",
        "#########################",
        "#########################",
        "########################",
        " #######################",
        "  #####################",
        "   ####  ###############",
        "         ###############",
        "          #############",
        "           ###########",
    ],
}

FLAG_ROUNDS = 8
OUTLINE_ROUNDS = 8
LIGHTNING_QUESTIONS = 10
LIGHTNING_TIME = 10.0
# lightning pool: short, typeable capitals only
LIGHTNING_POOL = [c for c in COUNTRIES if len(c[1]) <= 10 and "," not in c[1]]

CYAN = "\033[96m"
RESET = "\033[0m"


def show_outline(rows):
    for row in rows:
        print(CYAN + row + RESET)

# ---------------------------------------------------------------------------
# mode 1: classic capitals quiz (the original, unchanged)
# ---------------------------------------------------------------------------

def ask(country, correct, options):
    print(f"\nWhat is the capital of {country}?")
    for letter, city in zip(LETTERS, options):
        print(f"  {letter}. {city}")
    while True:
        ans = input("answer (A-D): ").strip().upper()
        if ans in LETTERS:
            return options[LETTERS.index(ans)] == correct
        print("please answer A, B, C or D.")


def play():
    questions = random.sample(COUNTRIES, ROUNDS)
    score = 0
    for country, capital in questions:
        distractors = random.sample([c for _, c in COUNTRIES if c != capital], 3)
        options = distractors + [capital]
        random.shuffle(options)
        if ask(country, capital, options):
            print("correct!")
            score += 1
        else:
            print(f"nope — it's {capital}.")
    print(f"\nfinal score: {score}/{ROUNDS}")
    return score, ROUNDS


# ---------------------------------------------------------------------------
# shared multiple-choice helper for the visual modes
# ---------------------------------------------------------------------------

def _pick(options_text, prompt="answer (A-D): "):
    for letter, text in zip(LETTERS, options_text):
        print(f"  {letter}. {text}")
    while True:
        ans = input(prompt).strip().upper()
        if ans in LETTERS:
            return options_text[LETTERS.index(ans)]
        print("please answer A, B, C or D.")


# ---------------------------------------------------------------------------
# mode 2: flag quiz
# ---------------------------------------------------------------------------

def flag_quiz():
    print("\n🏳️  FLAG QUIZ — which country does this flag belong to?")
    names = random.sample(sorted(FLAGS), FLAG_ROUNDS)
    score = 0
    for i, country in enumerate(names, 1):
        distractors = random.sample([n for n in FLAGS if n != country], 3)
        options = distractors + [country]
        random.shuffle(options)
        print(f"\n--- flag {i}/{FLAG_ROUNDS} ---")
        show_flag(FLAGS[country])
        print()
        if _pick(options) == country:
            print("correct! 🎉")
            score += 1
        else:
            print(f"nope — it's {country}.")
    print(f"\n🏳️  flag score: {score}/{FLAG_ROUNDS}")
    return score, FLAG_ROUNDS


# ---------------------------------------------------------------------------
# mode 3: country-outline quiz
# ---------------------------------------------------------------------------

def outline_quiz():
    print("\n🗺️  OUTLINE QUIZ — which country is shaped like this?")
    names = random.sample(sorted(OUTLINES), OUTLINE_ROUNDS)
    score = 0
    for i, country in enumerate(names, 1):
        distractors = random.sample([n for n in OUTLINES if n != country], 3)
        options = distractors + [country]
        random.shuffle(options)
        print(f"\n--- outline {i}/{OUTLINE_ROUNDS} ---")
        show_outline(OUTLINES[country])
        print()
        if _pick(options) == country:
            print("correct! 🎉")
            score += 1
        else:
            print(f"nope — it's {country}.")
    print(f"\n🗺️  outline score: {score}/{OUTLINE_ROUNDS}")
    return score, OUTLINE_ROUNDS


# ---------------------------------------------------------------------------
# mode 4: lightning round — timed free-text input, no multiple choice
# ---------------------------------------------------------------------------

def input_timeout(prompt, timeout):
    """Read a line with a live countdown. Returns the typed text,
    or None if time runs out. Falls back to plain input() where
    termios/select are unavailable (non-tty, Windows)."""
    if os.name == "nt" or not sys.stdin.isatty():
        try:
            return input(prompt)
        except EOFError:
            return None
    import select
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf = []
    try:
        tty.setcbreak(fd)  # keypresses arrive immediately, no Enter needed
        end = time.time() + timeout
        sys.stdout.write(prompt)
        sys.stdout.flush()
        while True:
            remaining = end - time.time()
            if remaining <= 0:
                sys.stdout.write("\n  ⏰ time's up!\n")
                sys.stdout.flush()
                return None
            sys.stdout.write(f"\r\033[K{prompt}[{remaining:4.1f}s] "
                             f"{''.join(buf)}")
            sys.stdout.flush()
            r, _, _ = select.select([sys.stdin], [], [], 0.1)
            if not r:
                continue
            ch = os.read(fd, 1).decode("utf-8", "ignore")
            if ch in ("\r", "\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
                return "".join(buf)
            if ch in ("\x7f", "\x08"):      # backspace
                buf = buf[:-1]
            elif ch == "\x03":              # ctrl-C
                raise KeyboardInterrupt
            elif ch == "\x1b":              # swallow escape sequences
                select.select([sys.stdin], [], [], 0.05)
                while select.select([sys.stdin], [], [], 0)[0]:
                    os.read(fd, 8)
            elif ch.isprintable():
                buf.append(ch)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def lightning_round():
    print("\n⚡ LIGHTNING ROUND — type the capital, "
          f"{LIGHTNING_TIME:.0f} seconds each!")
    print("No multiple choice. Spelling counts (case doesn't).\n")
    questions = random.sample(LIGHTNING_POOL, LIGHTNING_QUESTIONS)
    score = 0
    for i, (country, capital) in enumerate(questions, 1):
        print(f"[{i}/{LIGHTNING_QUESTIONS}] capital of {country}?")
        ans = input_timeout("  > ", LIGHTNING_TIME)
        if ans is None:
            print(f"    too slow — it's {capital}.")
        elif ans.strip().lower() == capital.lower():
            print("    ⚡ correct!")
            score += 1
        else:
            print(f"    nope — it's {capital}.")
    print(f"\n⚡ lightning score: {score}/{LIGHTNING_QUESTIONS}")
    return score, LIGHTNING_QUESTIONS


# ---------------------------------------------------------------------------
# persistent local high-score table
# ---------------------------------------------------------------------------

SCORES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "highscores.json")


def load_scores():
    try:
        with open(SCORES_PATH) as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def record_score(mode, score, total):
    if score <= 0:
        return
    try:
        name = input("new entry for the leaderboard! your name: "
                     ).strip()[:20] or "player"
    except EOFError:
        name = "player"
    scores = load_scores()
    scores.append({"name": name, "mode": mode, "score": score,
                   "total": total, "date": time.strftime("%Y-%m-%d")})
    try:
        with open(SCORES_PATH, "w") as f:
            json.dump(scores, f, indent=2)
        print("saved to the local leaderboard 🏆")
    except OSError:
        print("(couldn't save the high-score file)")


def show_scores():
    scores = load_scores()
    if not scores:
        print("\nno high scores yet — be the first!")
        return
    scores.sort(key=lambda s: (-s["score"], s["mode"]))
    print("\n🏆  HIGH SCORES  (top 10)")
    print(f"  {'#':<3}{'name':<16}{'mode':<12}{'score':<8}date")
    for i, s in enumerate(scores[:10], 1):
        print(f"  {i:<3}{s['name']:<16}{s['mode']:<12}"
              f"{s['score']}/{s['total']:<6}{s.get('date', '')}")


# ---------------------------------------------------------------------------
# menu
# ---------------------------------------------------------------------------

def menu():
    print("  1. capitals   — classic 10-round quiz")
    print("  2. flags      — guess the country from its flag")
    print("  3. outlines   — guess the country from its shape")
    print("  4. lightning  — capitals against the clock")
    print("  5. high scores")
    print("  6. quit")
    while True:
        try:
            c = input("pick 1-6: ").strip()
        except EOFError:
            return "6"
        if len(c) == 1 and c in "123456":
            return c
        print("pick 1, 2, 3, 4, 5 or 6.")


def main():
    print("🌍  geo-quiz-cli — how well do you know the world?")
    while True:
        print()
        choice = menu()
        if choice == "1":
            score, total = play()
            record_score("capitals", score, total)
        elif choice == "2":
            score, total = flag_quiz()
            record_score("flags", score, total)
        elif choice == "3":
            score, total = outline_quiz()
            record_score("outlines", score, total)
        elif choice == "4":
            score, total = lightning_round()
            record_score("lightning", score, total)
        elif choice == "5":
            show_scores()
        else:
            print("thanks for playing!")
            break


if __name__ == "__main__":
    main()
