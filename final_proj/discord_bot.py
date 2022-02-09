import os, requests, json, discord, sqlite3, traceback, sys
from dotenv import load_dotenv
from sqlite3 import Error 
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("TOKEN")

client = discord.Client()   # Create an instance of client, representing connection
                            # to the discord server
                            
# Instance bot
owners = [695849842244583455]  # ID for Machiavelli#9308
bot = commands.Bot(command_prefix=';;', owner_id = set(owners))       
                    
@client.event  # Registers an event
async def on_ready():
    print("Logged in as {0.user}".format(client))

# Catch error when initializing database tables
def catchError(error):
    print('SQLite error: %s' % (' '.join(error.args)))
    print("Exception class is: ", error.__class__)
    print('SQLite traceback: ')
    exc_type, exc_value, exc_tb = sys.exc_info()
    print(traceback.format_exception(exc_type, exc_value, exc_tb))
    pass   # Since the only error would probably be table already exist

# Create connection to a database file stored locally
try:
    con = sqlite3.connect('user.db')
    cur = con.cursor()   # create a cursor for the database
    print("Successfully established connection to database {0}.".format('user.db'))
except sqlite3.Error as error:
    print("Error while establishing connection to sqlite.", error)

# Called by ;;init command
# Should only execute once to create tables 
def create_table(con, db_file):
    createdTable = 0
    
    # Format for time strings is YYYYMMDD HHMMSS
    # Create table for users
    try: 
        cur.execute('''CREATE TABLE user(
                        user_id INTEGER PRIMARY KEY,
                        signup_date TEXT, 
                        last_seen_days INTEGER,  
                        pmdr_completed INTEGER,
                        pmdr_initiated INTEGER,
                        guild_role TEXT
                        )''')
        con.commmit()
        createdTable += 1
    except sqlite3.Error as er:
        catchError(er)
    
    # Create table for to-do lists created by users
    # User --> List --> To-do entry
    try:
        cur.execute('''CREATE TABLE list(
                        list_id NOT NULL,
                        owner_id PRIMARY KEY,
                        tracked TEXT,
                        creation_date TEXT,
                        FOREIGN KEY(list_id) REFERENCES user(user_id)
                        )''')
        con.commit()
        createdTable += 1
    except sqlite3.Error as er:
        catchError(er)
    
    # Create table for every to-do entry, by different users, in different lists
    try:
        cur.execute('''CREATE TABLE todo(
                        entry_id NOT NULL,
                        due TEXT,
                        content TEXT,
                        reminder TEXT,
                        is_done BOOLEAN,
                        FOREIGN KEY(entry_id) REFERENCES list(list_id)
                        )''')
        con.commit()
        createdTable += 1
    except sqlite3.Error as er:
        catchError(er)
    
    # Create table for every *active* breakout room, a.k.a channel
    # Deactivated/abandoned rooms are automatically removed after some time
    # Since details about a channel can be found in the audit log, 
    # the function of this table is kept to a minimum
    try:
        cur.execute('''CREATE TABLE room(
                        room_id TEXT PRIMARY KEY, 
                        owner_id NOT NULL,
                        member_id NOT NULL,
                        FOREIGN KEY(owner_id) REFERENCES user(user_id),
                        FOREIGN KEY(member_id) REFERENCES user(user_id)
                        )''')
        con.commit()
        createdTable += 1
    except sqlite3.Error as er:
        catchError(er)
    
    # Create table for PD point balance for each server member
    try:
        cur.execute('''CREATE TABLE balance(
                        account_id NOT NULL,
                        balance TEXT,
                        FOREIGN KEY(account_id) REFERENCES user(user_id)
                        )''')
        con.commit()
        createdTable += 1
    except sqlite3.Error as er:
        catchError(er)

    # Create table for recording all purchases made with PD points by a server member
    try:
        cur.execute('''CREATE TABLE transaction_history(
                        transaction_id NOT NULL,
                        item TEXT,
                        amount TEXT,
                        FOREIGN KEY(transaction_id) REFERENCES balance(account_id)
                        )''')
        con.commit()
        createdTable += 1
    except sqlite3.Error as er:
        catchError(er)
    
    # Create table for storing information of all available store items
    try:
        cur.execute('''CREATE TABLE catalogue(
                        item_id NOT NULL,
                        price TEXT,
                        is_discounted BOOLEAN,
                        discount TEXT,
                        sale_length TEXT,
                        is_limited BOOLEAN,
                        is_available BOOLEAN,
                        discontinue_date TEXT
                        )''')
        con.commit()
        createdTable += 1
    except sqlite3.Error as er:
        catchError(er)
    
    if createdTable > 1:
        print("{} new table(s) successfully created.".format(createdTable))
    else:
        print("No new table created. Tables already exist.")

# Initializes database, only invokabled by guild owner
@bot.command(name='init', description="Initializes database.")
@commands.is_owner()
async def init(ctx):
    await create_table(con, "db_file")
    # await ctx.message.author.send("Database has initialized.")

@bot.command(name='test_cmd')
@commands.is_owner()
async def hi(ctx):
    await ctx.
# How do I send a message to the channel?

client.run(TOKEN)