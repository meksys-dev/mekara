Run a nested sequence of test sub-scripts and report what the user owes.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Run /test/random

Run /test/random. Make sure to get both numbers back.

### Step 1: Compute the absolute difference

Save the absolute difference between the two numbers. For example, if the /test/random result was 95 and the user guessed 91, mark this difference down as 4.

### Step 2: Run /test/double-or-nothing

Run /test/double-or-nothing **inside /tmp** on that absolute difference. For example, if the difference was 4, then we may get back either 0 or 8 as output. We will call this the "owed" number.

### Step 3: Read the result

Read the "owed" number from /tmp/resulting-number.txt.

### Step 4: Run /test/imagine-object

Run /test/imagine-object to get a description of an imaginary object. For example, we may get back "blue dogs."

### Step 5: Tell the user what they owe

Tell the user that they owe the "owed" number of imagined objects. For example, if that number were doubled, and we imagined blue dogs, then tell the user "You owe 8 blue dogs."

## Key Principles

This is a relatively straightforward script that does not require key guiding principles at this time.
