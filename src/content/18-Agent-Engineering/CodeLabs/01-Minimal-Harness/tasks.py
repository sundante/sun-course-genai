"""Eight small repository tasks for the minimal harness. Each task is a set of files written into a
fresh workspace, an instruction, visible tests the agent may run (tests/test_visible.py), and hidden
tests only the grader runs. Tests are plain assert scripts: `python tests/test_visible.py`."""

from dataclasses import dataclass, field


@dataclass
class Task:
    tid: str
    instruction: str
    files: dict[str, str]
    visible: str
    hidden: str
    notes: str = ""
    extra: dict = field(default_factory=dict)


HEADER = "import os, sys\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n"

TASKS = [
    Task(
        "moving_average",
        "moving_average in stats.py returns the wrong number of windows. Fix it.",
        {"stats.py": '''def moving_average(xs, k):
    """Averages of every window of k consecutive values, in order."""
    if k <= 0:
        raise ValueError("k must be positive")
    return [sum(xs[i:i + k]) / k for i in range(len(xs) - k)]
'''},
        HEADER + "from stats import moving_average\nassert moving_average([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]\nprint('ok')\n",
        HEADER + "from stats import moving_average\nassert moving_average([1, 2, 3], 3) == [2.0]\nassert moving_average([5], 1) == [5.0]\nassert moving_average([1, 2], 3) == []\n"
        "try:\n    moving_average([1], 0)\n    raise SystemExit('expected ValueError')\nexcept ValueError:\n    pass\nprint('ok')\n",
    ),
    Task(
        "slugify",
        "Implement slugify(text) in text_utils.py as its docstring describes.",
        {"text_utils.py": '''def slugify(text: str) -> str:
    """Lowercase; runs of characters that are not a-z or 0-9 become a single '-';
    no leading or trailing '-'. Example: "Hello, World!" -> "hello-world"."""
    raise NotImplementedError
'''},
        HEADER + "from text_utils import slugify\nassert slugify('Hello, World!') == 'hello-world'\nprint('ok')\n",
        HEADER + "from text_utils import slugify\nassert slugify('  Multiple   spaces  ') == 'multiple-spaces'\nassert slugify('C++ & Python 3.12') == 'c-python-3-12'\n"
        "assert slugify('---') == ''\nassert slugify('Already-slugged') == 'already-slugged'\nprint('ok')\n",
    ),
    Task(
        "parse_duration",
        "parse_duration('1h30m') should return 5400 but returns the wrong value. Fix durations.py.",
        {"durations.py": '''import re

UNITS = {"h": 3600, "m": 60, "s": 1}


def parse_duration(text: str) -> int:
    """Parse strings like '2h', '45m', '1h30m', '1h5m10s' into seconds."""
    total = 0
    for number, unit in re.findall(r"(\\d+)([hms])", text):
        total += int(number) * UNITS["m" if unit == "h" else unit]
    return total
'''},
        HEADER + "from durations import parse_duration\nassert parse_duration('1h30m') == 5400\nprint('ok')\n",
        HEADER + "from durations import parse_duration\nassert parse_duration('2h') == 7200\nassert parse_duration('45m') == 2700\nassert parse_duration('1h5m10s') == 3910\nassert parse_duration('90s') == 90\nprint('ok')\n",
    ),
    Task(
        "inventory",
        "Inventory.remove lets stock go negative. It must raise ValueError when removing more than is in stock, and leave the stock unchanged.",
        {"inventory.py": '''class Inventory:
    def __init__(self):
        self.stock = {}

    def add(self, sku: str, qty: int) -> None:
        self.stock[sku] = self.stock.get(sku, 0) + qty

    def remove(self, sku: str, qty: int) -> None:
        self.stock[sku] = self.stock.get(sku, 0) - qty
'''},
        HEADER + "from inventory import Inventory\ninv = Inventory(); inv.add('a', 2)\ntry:\n    inv.remove('a', 3)\n    raise SystemExit('expected ValueError')\nexcept ValueError:\n    pass\nprint('ok')\n",
        HEADER + "from inventory import Inventory\ninv = Inventory(); inv.add('a', 2)\ntry:\n    inv.remove('a', 3)\nexcept ValueError:\n    pass\nassert inv.stock['a'] == 2\n"
        "inv.remove('a', 2)\nassert inv.stock['a'] == 0\ntry:\n    inv.remove('missing', 1)\n    raise SystemExit('expected ValueError for unknown sku')\nexcept ValueError:\n    pass\nprint('ok')\n",
    ),
    Task(
        "roman",
        "Add a function roman_to_int(s) to roman.py that converts a Roman numeral (I, V, X, L, C, D, M, with subtractive forms like IV and CM) to an integer.",
        {"roman.py": '"""Roman numeral helpers."""\n'},
        HEADER + "from roman import roman_to_int\nassert roman_to_int('XIV') == 14\nprint('ok')\n",
        HEADER + "from roman import roman_to_int\nassert roman_to_int('III') == 3\nassert roman_to_int('MCMXCIV') == 1994\nassert roman_to_int('CDXLIV') == 444\nassert roman_to_int('MMXXVI') == 2026\nprint('ok')\n",
    ),
    Task(
        "merge_intervals",
        "merge_intervals in intervals.py doesn't merge intervals that only touch (like [1,2] and [2,3]), and it assumes sorted input. Fix both.",
        {"intervals.py": '''def merge_intervals(intervals):
    """Merge overlapping or touching [start, end] intervals; return them sorted by start."""
    out = []
    for start, end in intervals:
        if out and start < out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return out
'''},
        HEADER + "from intervals import merge_intervals\nassert merge_intervals([[1, 2], [2, 3]]) == [[1, 3]]\nprint('ok')\n",
        HEADER + "from intervals import merge_intervals\nassert merge_intervals([[5, 6], [1, 3], [2, 4]]) == [[1, 4], [5, 6]]\nassert merge_intervals([]) == []\n"
        "assert merge_intervals([[1, 10], [2, 3]]) == [[1, 10]]\nassert merge_intervals([[1, 2], [3, 4]]) == [[1, 2], [3, 4]]\nprint('ok')\n",
    ),
    Task(
        "word_freq",
        "word_freq in words.py should count words case-insensitively and ignore punctuation, but 'The' and 'the.' are counted separately. Fix it.",
        {"words.py": '''from collections import Counter


def word_freq(text: str) -> dict:
    """Word counts, case-insensitive, ignoring punctuation. Apostrophes inside words are kept (don't)."""
    return dict(Counter(text.split()))
'''},
        HEADER + "from words import word_freq\nassert word_freq('The cat. the CAT!') == {'the': 2, 'cat': 2}\nprint('ok')\n",
        HEADER + "from words import word_freq\nassert word_freq(\"Don't stop, don't!\") == {\"don't\": 2, 'stop': 1}\nassert word_freq('') == {}\n"
        "assert word_freq('a-b a b') in ({'a': 2, 'b': 2}, {'a-b': 1, 'a': 1, 'b': 1})\nassert word_freq('Hello\\nhello\\tHELLO') == {'hello': 3}\nprint('ok')\n",
    ),
    Task(
        "regional_tax",
        "Orders from the EU are taxed at the US rate. price_with_tax in pricing.py should use the tax rate for the order's region from tax.py. Fix it.",
        {"tax.py": '''RATES = {"US": 0.07, "EU": 0.20, "UK": 0.20, "JP": 0.10}


def rate_for(region: str) -> float:
    if region not in RATES:
        raise KeyError(f"unknown region {region}")
    return RATES[region]
''', "pricing.py": '''from tax import RATES


def price_with_tax(net: float, region: str) -> float:
    """Gross price for a net price in a region, rounded to 2 decimals."""
    return round(net * (1 + RATES["US"]), 2)
'''},
        HEADER + "from pricing import price_with_tax\nassert price_with_tax(100, 'EU') == 120.0\nprint('ok')\n",
        HEADER + "from pricing import price_with_tax\nassert price_with_tax(100, 'US') == 107.0\nassert price_with_tax(19.99, 'JP') == 21.99\n"
        "try:\n    price_with_tax(10, 'XX')\n    raise SystemExit('expected KeyError')\nexcept KeyError:\n    pass\nprint('ok')\n",
    ),
]
