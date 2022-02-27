import sqlite3

con = sqlite3.connect('example.db')
# Calling method cursor(), under class connect (assigned as con)
# Method cursor() creates a cursor object, which is then assigned to cur
cur = con.cursor()

while(True):
    query = input()
    if query == 'exit':
        break
    else:
        try:
            # Calling the execute method of object cur
            for row in cur.execute(query):
                print(row)
        except sqlite3.Error as er:
            print(er)