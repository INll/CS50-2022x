import os, requests, json, discord, sqlite3
from dotenv import load_dotenv
from sqlite3 import Error

load_dotenv()
TOKEN = os.getenv("TOKEN")

client = discord.Client()   # create an instance of client, representing connection
                            # to the discord server
                            
@client.event  # Registers an event
async def on_ready():
    print("Logged in as {0.user}".format(client))

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
                    guild_role TEXT
                    );''')
    
    # Create table for to-do lists created by users
    # User --> List --> To-do entry
    cur.execute('''CREATE TABLE IF NOT EXISTS list(
                    list_id NOT NULL,
                    owner_id PRIMARY KEY,
                    tracked TEXT,
                    creation_date TEXT,
                    FOREIGN KEY(list_id) REFERENCES user(user_id)
                    );''')
    
    # Create table for every to-do entry, by different users, in different lists
    cur.execute('''CREATE TABLE IF NOT EXISTS todo(
                    entry_id NOT NULL,
                    due TEXT,
                    content TEXT,
                    reminder TEXT,
                    is_done BOOLEAN,
                    FOREIGN KEY(entry_id) REFERENCES list(list_id)
                    );''')
    
    # Create table for every *active* breakout room, a.k.a channel
    # Deactivated/abandoned rooms are automatically removed after some time
    # Since details about a channel can be found in the audit log, 
    # the function of this table is kept to a minimum
    cur.execute('''CREATE TABLE IF NOT EXISTS room(
                    room_id TEXT PRIMARY KEY, 
                    owner_id NOT NULL,
                    member_id NOT NULL,
                    FOREIGN KEY(owner_id) REFERENCES user(user_id),
                    FOREIGN KEY(member_id) REFERENCES user(user_id)
                    );''')
    
    # Create table for PD point balance for each server member
    cur.execute('''CREATE TABLE IF NOT EXISTS balance(
                    account_id NOT NULL,
                    balance TEXT,
                    FOREIGN KEY(account_id) REFERENCES user(user_id)
                    );''')

    # Create table for recording all purchases made with PD points by a server member
    cur.execute('''CREATE TABLE IF NOT EXISTS transaction_history(
                    transaction_id NOT NULL,
                    item TEXT,
                    amount TEXT,
                    FOREIGN KEY(transaction_id) REFERENCES balance(account_id)
                    );''')
    
    # Create table for storing information of all available store items
    cur.execute('''CREATE TABLE IF NOT EXISTS catalogue(
                    item_id NOT NULL,
                    price TEXT,
                    is_discounted BOOLEAN,
                    discount TEXT CHECK(is_discounted == 1),
                    sale_length TEXT CHECK(is_discounted == 1),
                    is_limited BOOLEAN,
                    is_available BOOLEAN,
                    discontinue_date TEXT CHECK(is_limited == 1)
                    );''')


# Example code from code a Discord bot on YouTube 

# # Request a quote from the zenquotes API through HTTP, enabled by requests package
# def get_quote():
#     response = requests.get("https://zenquotes.io/api/random")
#     json_data = json.loads(response.text)   # convert quote in TEXTto .json
#     quote = json_data[0]["q"]   # format: single dict inside a list
#     quote = quote + " -" + json_data[0]["a"]
#     return(quote)

# End of example function

    
@client.event
async def on_message(message):
    if message.author == client.user: # if message comes from the bot, do nothing
        return 
    
    # if message.content.startswith('$inspire'):
    #     quote = get_quote()
    #     await message.channel.send(quote)

    if message.content.startswith(';;init'):
        

    if message.content.startswith(';;help'):
        await message.channel.send("")
        
        
    
    if any(word in message.content for word in sad_words):
        await message.channel.send(encourgement)
               

client.run(TOKEN)