# Perform DNA profiling

import csv
import sys

# Ensure correct usage
if len(sys.argv) != 3:
    print("Usage: python dna.py data.csv sequence.txt")
    sys.exit(0)

# Load STR sequence into memory
strsq = []
str_list = []
file = open(sys.argv[1], "r")
reader_str = csv.DictReader(file)
for row in reader_str:
    strsq.append(row)
file.close()

# Generate a list of Target STRs from .csv header
file = open(sys.argv[1], "r")
reader_str_rec = csv.reader(file)
for row2 in reader_str_rec:
    row2.pop(0)
    str_list = row2
    break
# Dictionary for DNA info
dna_list = {}
for row3 in reader_str_rec:
    person = row3.pop(0)
    dna_list[person] = row3
file.close()

# Load DNA sequence into memory
file = open(sys.argv[2], "r")
reader_dna = csv.reader(file)
for row2 in reader_dna:
    dnasq = row2

global_max = [0] * len(str_list)

# Loop through the whole DNA sequence, each time looking for one
# STR candidate
for i in range(len(str_list)):
    curr_nuc = 0
    count = 0
    curr_max = 0
    str_len = len(str_list[i])
    dna_len = len(dnasq[0])

    while True:
        if dnasq[0][curr_nuc] == str_list[i][0]:
            if dnasq[0][curr_nuc:curr_nuc + str_len] == str_list[i]:
                count += 1
                if curr_nuc + 1 > dna_len - str_len:
                    break
                curr_nuc += len(str_list[i])
                continue
        if count > global_max[i]:
            global_max[i] = count
        if curr_nuc + 1 > dna_len - str_len:
            break
        curr_nuc += 1
        count = 0

results = []
for k in global_max:
    results.append(str(k))
for key, value in dna_list.items():
    if results == value:
        print(f"{key}")
        sys.exit(0)
print("No match")