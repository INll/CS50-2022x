import cs50

# Check for valid input
while True:
    height = cs50.get_int("Height: ")
    if height > 0 and height < 9:
        break

# Construct the pyramid
for i in range(height):

    # Make space
    for j in range(height - i - 1):
        print(" ", end="")

    # Build the left-hand side of the pyramid
    for k in range(i + 1):
        print("#", end="")

    # Make a gap
    for l in range(2):
        print(" ", end="")

    # Build the right-hand side of the pyramid
    for m in range(i):
        print("#", end="")

    print("#")