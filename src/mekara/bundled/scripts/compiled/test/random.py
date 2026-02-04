"""Auto-generated script. Source: .claude/commands/test/random.md"""

from mekara.scripting.runtime import auto, llm


def _print_message(message: str) -> None:
    """Print a message to the user."""
    print(message)


def execute(request: str):
    """Script entry point."""
    # Step 1: Generate a random number between 1 and 100
    result = yield auto(
        "shuf -i 1-100 -n 1", context="Use `shuf` to generate a random number between 1 and 100"
    )
    secret_number = int(result.output.strip())

    # Step 2: Have user guess the number
    guess_result = yield llm(
        "Have user guess the number. Do **NOT** guess a number on behalf of the user; "
        "you **MUST** ask the user for this number.",
        expects={"guess": "the user's guessed number as an integer"},
    )
    user_guess = int(guess_result.outputs["guess"])

    # Step 3: Check if the user guessed correctly and print result
    won = user_guess == secret_number
    if won:
        yield auto(
            _print_message,
            {"message": "You got it right!"},
            context='If the user guessed the right number, print out "You got it right!"',
        )
    else:
        yield auto(
            _print_message,
            {"message": "You got it wrong!"},
            context='If the user guessed the wrong number, print out "You got it wrong!"',
        )

    # Step 4: Give personalized feedback based on result
    if won:
        yield llm("If the user won, congratulate them on being such a prescient user")
    else:
        yield llm("If they lost, give them a choice insult")
