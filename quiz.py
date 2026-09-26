"""
geo-quiz-cli
A geography quiz game in pure Python (no dependencies).

Ten rounds, four options each: name the capital of the country.
Tracks your score and lets you play again.

Run:
    python3 quiz.py
"""
import random

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
    return score


def main():
    print("🌍  geo-quiz — how well do you know the world's capitals?")
    best = 0
    while True:
        best = max(best, play())
        again = input(f"\nbest so far: {best}/{ROUNDS}. play again? (y/n): "
                      ).strip().lower()
        if again != "y":
            print("thanks for playing!")
            break


if __name__ == "__main__":
    main()
