"""Auto-generated script. Source: .claude/commands/test/nested.md"""

from pathlib import Path

from mekara.scripting.runtime import auto, call_script, llm


def execute(request: str):
    """Script entry point."""
    # Step 0: Run /test/random and get both numbers back
    yield call_script(
        "test/random",
        request=request,
    )

    # Step 1: Calculate absolute difference between the two numbers
    # The LLM needs to extract the random number and user guess from the conversation
    result = yield llm(
        "Save the absolute difference between the two numbers. For example, if the "
        "/test/random result was 95 and the user guessed 91, mark this difference down as 4.",
        expects={
            "difference": "absolute difference between the random number and user's guess (integer)"
        },
    )
    difference = result.outputs["difference"]

    # Step 2: Run /test/double-or-nothing inside /tmp on the difference
    yield call_script(
        "test/double-or-nothing",
        request=str(difference),
        working_dir=Path("/tmp"),
    )

    # Step 3: Read the "owed" number from /tmp/resulting-number.txt
    yield auto(
        "cat /tmp/resulting-number.txt",
        context='Read the "owed" number from /tmp/resulting-number.txt.',
    )

    # Step 4: Run /test/imagine-object to get a description of an imaginary object
    yield call_script(
        "test/imagine-object",
        request=request,
    )

    # Step 5: Tell the user they owe the "owed" number of imagined objects
    yield llm(
        'Tell the user that they owe the "owed" number of imagined objects. For example, '
        "if that number were doubled, and we imagined blue dogs, then tell the user "
        '"You owe 8 blue dogs."'
    )
