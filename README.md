# geo-quiz-cli

A **geography quiz game** in **pure Python** — no dependencies.

## Run it

```bash
python3 quiz.py
```

Ten rounds, four options each: name the capital of the country. 48
countries in the pool, questions shuffled every game, best score tracked.

## How it works

- Each round samples a country, then picks 3 random wrong capitals as
  distractors and shuffles the four options — so the quiz is different
  every time.
- Everything is one file and one list: adding a country is a single line.

## Try changing

- `ROUNDS` for a longer game.
- Add a "hard mode" with no multiple choice (type the capital yourself).

Built by [Mohammad Ali](https://github.com/AliRender13).
