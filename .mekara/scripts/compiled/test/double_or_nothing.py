"""Auto-generated script. Source: .claude/commands/test/double-or-nothing.md"""

import random

from mekara.scripting.runtime import auto, llm


def _double_or_nothing(number: float) -> float:
    """Randomly either double the number or return zero."""
    if random.choice([True, False]):
        return number * 2
    return 0


def _try_parse_number(text: str) -> float | None:
    """Try to parse a number from text. Returns None if not a valid number."""
    try:
        return float(text.strip())
    except (ValueError, AttributeError):
        return None


def execute(request: str):
    """Script entry point."""
    # Step 0: Get a number from the user if one wasn't already provided.
    parsed_number = _try_parse_number(request)
    if parsed_number is not None:
        number = parsed_number
    else:
        result = yield llm(
            "Get a number from the user if one wasn't already provided.",
            expects={"number": "the number provided by the user (as a float)"},
        )
        number = float(result.outputs["number"])

    # Step 1: Decide randomly to either double this number or return zero.
    calc_result = yield auto(
        _double_or_nothing,
        {"number": number},
        context="Decide randomly to either double this number or return zero.",
    )
    final_number = calc_result.value

    # Step 2: Write the result to a file called `resulting-number.txt` in the current directory.
    yield auto(
        f"echo {final_number} > resulting-number.txt",
        context=(
            "Write the result to a file called `resulting-number.txt` in the current directory."
        ),
    )
