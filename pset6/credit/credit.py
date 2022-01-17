import cs50

string = cs50.get_string("Number: ")


def main():

    # Ensure correct format
    if len(string) not in (13, 15, 16, 19):
        print("INVALID")
        return

    # Calculate product of every other digits
		# starting from second-to-left to the first
    digits = list()
    for i in range(len(string) - 2, -1, -2):
        digits.append(str(int(string[i]) * 2))

    # Summation of every products in digits
    total = 0
    for j in range(len(digits)):
        for k in range(len(digits[j])):
            total += int(digits[j][k])

    # Add digits that were left out
    for k in range(len(string) - 1, -1, -2):
        total += int(string[k])

    # Check if last digit in sum equal zero
    total = str(total)
    if total[len(total) - 1] != '0':
        print("INVALID")
        return

    # Identify payment network processor
    if int(string[0] + string[1]) in (34, 37):
        print("AMEX")
    elif int(string[0]) == 4:
        print("VISA")
    else:
        print("MASTERCARD")


main()