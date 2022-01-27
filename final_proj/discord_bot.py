import os, dotenv, requests, json, discord, sqlite3
from dotenv import load_dotenv
from sqlite3 import Error

load_dotenv()
TOKEN = os.getenv("TOKEN")

client = discord.Client()   # create an instance of client, representing connection
                            # to the discord server

try:
    con = sqlite3.connect('user.db')
    cur = con.cursor()   # create a cursor for the database
    print("Successfully established connection to database {0}.".format('user.db'))
except sqlite3.Error as error:
    print("Error while establishing connection to sqlite.", error)

# Called by ;;init command
# Should only execute once to create tables 
def create_table(con, db_file):
    
    # Format for time strings is YYYYMMDD HHMMSS
    # Create table for users
    cur.execute('''CREATE TABLE IF NOT EXISTS user(
                    user_id INTEGER PRIMARY KEY,
                    signup_date TEXT, 
                    last_seen_days INTEGER,  
                    pmdr_completed INTEGER,
                    pmdr_initiated INTEGER,
                    guild_role text,                    
                    ))''')
    
    # Create table for to-do lists created by users
    # User --> List --> To-do entry
    cur.execute('''CREATE TABLE IF NOT EXISTS list(
                    FOREIGN KEY(list_id) REFERENCES user(user_id),
                    creation_date TEXT,
                    ))''')
    
    # Create table for every to-do entry, by different users, in different lists
    cur.execute('''CREATE TABLE IF NOT EXISTS todo(
                    FOREIGN KEY(entry_id) REFERENCES list(list_id)
                    due TEXT,
                    content TEXT,
                    reminder TEXT,
                    is_done BOOLEAN,
                    ))''')
    
    # Create table for every *active* breakout room, a.k.a channel
    # Deactivated/abandoned rooms are automatically removed after some time
    # Since details about a channel can be found in the audit log, 
    # the function of this table is kept to a minimum
    cur.execute('''CREATE TABLE IF NOT EXISTS room(
                    FOREIGN KEY(owner_id) REFERENCES user(user_id),
                    FOREIGN KEY(member_id) REFERENCES user(user_id),
                    room_id TEXT PRIMARY KEY,                  
                    ))''')
    
    # Create table for PD point balance for each server member
    cur.execute('''CREATE TABLE IF NOT EXISTS balance(
                    FOREIGN KEY(account_id) REFERENCES user(user_id),
                    balance text,
                    ))''')

    # Create table for recording all purchases made with PD points by a server member
    cur.execute('''CREATE TABLE IF NOT EXISTS transaction_history(
                    FOREIGN KEY(transaction_id) REFERENCES user(user_id),
                    item text,
                    amount text,
                    ))''')

# Request a quote from the zenquotes API through HTTP, enabled by requests package
def get_quote():
    response = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(response.text)   # convert quote in text to .json
    quote = json_data[0]["q"]   # format: single dict inside a list
    quote = quote + " -" + json_data[0]["a"]
    return(quote)

@client.event 
async def on_ready():
    print("Logged in as {0.user}".format(client))
    
@client.event
async def on_message(message):
    if message.author == client.user: # if message comes from self, do nothing
        return 
    
    if message.content.startswith('$inspire'):
        quote = get_quote()
        await message.channel.send(quote)

    if message.content.startswith(';;init'):


    if message.content.startswith(';;help'):
        await message.channel.send("")
        
        
    
    if any(word in message.content for word in sad_words):
        await message.channel.send(encourgement)
        
@client.event
        

client.run(TOKEN)