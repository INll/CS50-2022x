import os, dotenv, requests, json, discord, sqlite3
from dotenv import load_dotenv
from sqlite3 import Error

load_dotenv()
TOKEN = os.getenv("TOKEN")

client = discord.Client()   # create an instance of client, representing connection
                            # to the discord server


sad_words = ["sad"]

encourgement = ["It's okay!", "Hang in there!"]

def create_connection(db_file):
    con = None
    try:
        con = sqlite3.connect(db_file)
        return con
    except Error as error:
        print(error)
        
    return con


def create_table(con, db_file):
    cur = con.cursor() # create a cursor for the database
    
    # Create database for storing information on Kin's channel
    cur.execute('''CREATE TABLE IF NOT EXISTS upload_stats(
                    last_upload text,
                    link text, 
                    days_inactive integer, 
                    sub_count integer, 
                    
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