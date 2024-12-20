import argparse
from math import ceil
import numpy as np
from tabulate import tabulate

TALENT_MIN_LEVEL = 1    # minimum level for a Talent
TALENT_MAX_LEVEL = 10   # maximum level for a Talent
NUM_BOOK_TIERS = 3      # three tiers: Teachings, Guide, Philosophies
CONVERSION_FACTOR = 3   # 3 lower-tier books for 1 higher-tier book

parser = argparse.ArgumentParser(
    prog="gitbcalc",
    usage="talents.py current_levels target_levels [-b|--books BOOKS] [-a|--allow-conversion]"
)

parser.add_argument("current_levels",
                    help="comma-separated array of current Talent levels")
parser.add_argument("target_levels",
                    help="comma-separated array of target Talent levels")
parser.add_argument("-b", "--books",
                    help="comma-separated array of available Talent books")
parser.add_argument("-a", "--allow-conversion", action="store_true",
                    help="convert excess available Talent books")
args = parser.parse_args()

start_levels = np.array([int(i) for i in args.current_levels.split(",")])
end_levels = np.array([int(i) for i in args.target_levels.split(",")])
if start_levels.size != end_levels.size:
    raise ValueError("number of current and target Talent levels do not match")

books = None
if args.books is not None:
    books = np.array([int(i) for i in args.books.split(",")])
    if books.size != NUM_BOOK_TIERS:
        raise ValueError("unexpected number of Talent book tiers")

books_by_levelup = np.array([
    [3, 0, 0],  # 1 -> 2
    [0, 2, 0],  # 2 -> 3
    [0, 4, 0],  # 3 -> 4
    [0, 6, 0],  # 4 -> 5
    [0, 9, 0],  # 5 -> 6
    [0, 0, 4],  # 6 -> 7
    [0, 0, 6],  # 7 -> 8
    [0, 0, 12], # 8 -> 9
    [0, 0, 16], # 9 -> 10
])

# this is added to for every levelup
books_needed = np.array([0, 0, 0])

# iterate over each talent
for i in range(start_levels.size):
    start = start_levels[i]
    end = end_levels[i]

    if not TALENT_MIN_LEVEL <= start <= TALENT_MAX_LEVEL:
        raise ValueError("current Talent level out of bounds")
    if not TALENT_MIN_LEVEL <= end <= TALENT_MAX_LEVEL:
        raise ValueError("target Talent level out of bounds")
    if end < start:
        raise ValueError("target Talent level is lower then current Talent level")

    # for every level between the current and target level, add the required
    # number of books
    for j in range(start, end):
        books_needed += books_by_levelup[j - 1]

books_to_craft = [0, 0]
if books is not None:
    books_needed -= books

    if args.allow_conversion:
        # iterate over each tier that can be converted to a higher tier. any
        # negative number of books needed is treated as excess that can be
        # converted to the next tier
        for i in range(NUM_BOOK_TIERS - 1):
            excess_books = abs(books_needed[i])

            # if there aren't enough books to convert, skip
            if excess_books < CONVERSION_FACTOR:
                continue

            # iterate over each higher tier of book. if lacking, get how many
            # books of this tier would be needed to make up for it by conversion
            to_convert = 0
            for j in range(i + 1, NUM_BOOK_TIERS):
                if books_needed[j] > 0:
                    to_convert += books_needed[j] * (CONVERSION_FACTOR ** (j - i))
            
            # convert as many books as possible
            if to_convert > 0:
                conversible_books = min(
                    excess_books - (excess_books % CONVERSION_FACTOR),
                    to_convert
                )
                books_to_craft[i] = conversible_books / CONVERSION_FACTOR
                books_needed[i + 1] -= books_to_craft[i]

    # remove any negative numbers
    books_needed = [max(0, i) for i in books_needed]

# print in tabular form
headers = ["Tier", "Name", "Needed"]
table = [
    [1, "Teachings", books_needed[0]],
    [2, "Guide", books_needed[1]],
    [3, "Philosophies", books_needed[2]]
]
if args.allow_conversion:
    headers.append("Craft")
    for i in range(len(table)):
        table[i].append(books_to_craft[i - 1] if i > 0 else None)

print()
print(tabulate(table, headers))
print()
# print("""
# NOTE: If you are super stingy with your Resin and want to spend only as much as
# is minimally needed, don't convert your books yet if you're still farming for
# more. That's because less than 3 of any lower-tier book is not conversible, so
# you'll have to end up doing ~1-3 more runs if you need more higher-tier books.
# """)

# from https://docs.google.com/spreadsheets/d/e/2PACX-1vTiAN0_E-IdKHUQYJ5EUrMD7h7Vb08J1xCYNJGmIhxXus98YBjKTP-Xb8Ljoyc3bQ7WhrcROVorcWjY/pubhtml#
average_books_per_run = [2.20, 1.97, 0.23]
average_tier_3_books_per_run = (average_books_per_run[0] / 9) + (average_books_per_run[1] / 3) + average_books_per_run[2]
runs_remaining_estimate = ceil(books_needed[2] / average_tier_3_books_per_run)
print(f"Roughly estimating {runs_remaining_estimate} more run" f"{'s' if runs_remaining_estimate != 1 else ''}" " needed")
print()