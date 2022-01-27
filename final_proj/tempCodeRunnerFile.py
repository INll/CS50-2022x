import os
import requests
import json
import discord

TOKEN = os.getenv("TOKEN")

client = discord.Client()   # create an instance of client, representing connection
                            # to the discord server

# Request a quote from the zenquotes API through HTTP, enabled by requests package
def get_quote():
    response = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(response.text)   # convert quote in text to .json
    quote = json_data[0]["q"]   # format: single dict inside a list
    return(quote)

@client.event 
async def on_ready():
    print("Logged in as {0.user}".format(client))
    
@client.event
async def on_message(message):
    if message.author == client.user: # if message comes from self, do nothing
        return 
    
    if message.content.startswith('$hello'):
        await message.channel.send("Hi there!")
            
client.run(TOKEN)