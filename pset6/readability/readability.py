import cs50


def main():
    string = cs50.get_string("Text: ")  # Get text
    l = 0
    s = 0
    w = 1
    charCode = 0
    # Loop through the given text
    for i in range(len(string)):
        charCode = ord(string[i])
        if (charCode in range(97, 123)) or (charCode in range(65, 91)):
            l += 1
        elif (charCode == 32):
            w += 1
        elif (charCode in (33, 46, 63)):
            s += 1
    # Implement the Coleman-Liau formula
    avgl = round((l / w) * 100, 2)
    avgs = round((s / w) * 100, 2)
    lvl = round(((0.0588 * avgl) - (0.296 * avgs) - 15.8))
    # Determine grade level
    if lvl in range(1, 16):
        print(f"Grade {lvl}")
    elif lvl < 1:
        print("Before Grade 1")
    else:
        print("Grade 16+")


main()