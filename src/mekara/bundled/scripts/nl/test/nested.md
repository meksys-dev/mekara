0. First, run /test/random. Make sure to get both numbers back.
1. Save the absolute difference between the two numbers. For example, if the /test/random result was 95 and the user guessed 91, mark this difference down as 4.
2. Then, run /test/double-or-nothing **inside /tmp** on that absolute difference. For example, if the difference was 4, then we may get back either 0 or 8 as output. We will call this the "owed" number.
3. Read the "owed" number from /tmp/resulting-number.txt.
4. Run /test/imagine-object to get a description of an imaginary object. For example, we may get back "blue dogs."
5. Tell the user that they owe the "owed" number of imagined objects. For example, if that number were doubled, and we imagined blue dogs, then tell the user "You owe 8 blue dogs."