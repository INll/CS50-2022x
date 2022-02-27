import os, requests, json, discord, sqlite3, traceback, sys
from dotenv import load_dotenv
from discord.ext import commands
from datetime import date

load_dotenv()
TOKEN = os.getenv("TOKEN")

# Path of .db
dbPath = "/user.db"  # Make sure user.db is in working dir!
print("\nCurrent path: {}\n".format(os.getcwd()))

guildID = '699678814376034314'

# Instance bot
owners = ['695849842244583455']  # ID for Machiavelli#9308
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix = ';;', intents=intents)

# Check if its me the owner
def check_if_its_me(ctx):
    for i in range(len(owners)):
        if str(ctx.message.author.id) == owners[i]:
            return True
        else:
            return False
        
# Catch error when executing SQL query
def catchError(error, context):
    print('\nSQLite error: %s' % (' '.join(error.args)))
    print("Exception class is: ", error.__class__)
    print('SQLite traceback: ')
    exc_type, exc_value, exc_tb = sys.exc_info()
    print(traceback.format_exception(exc_type, exc_value, exc_tb))
    if context == 1:   # DM sql querying, does not return counter
        return traceback.format_exception(exc_type, exc_value, exc_tb)
    if context == 2:   # Init user table for new users
        print(traceback.format_exception(exc_type, exc_value, exc_tb))
    else:
        pass   # Since the only error would probably be table already exist

# Check if a command comes from an authorised channel
def checkChannelValidity(activeChannelID, validChannelID):
    if str(activeChannelID) != validChannelID:
        return True   # True if channel is invalid
    else:
        return False

# When bot is ready
@bot.event
async def on_ready():
    print("Logged in as {0.user}".format(bot))

#Initialize user table row for new users
@bot.event
async def on_member_join(member):
    try:            
        con = sqlite3.connect(dbPath)
        cur = con.cursor()
    except sqlite3.Error as er:
        print('Connection to `{}` failed.'.format(dbPath[1:]))
    # Initialize entry for a new member
    try:
        cur.execute("INSERT INTO user VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
            member.id, 0, 0, 0, 0, 0, 0, False
        ))
    except sqlite3.Error as er:
        catchError(er, 0)
        
    con.commit()
    con.close()
    
    
# A dict that stores query status and userID. If an authorised user wants to access
# .db the dictionary is then updated with key = userID, value = queryStatus
queryStat = {}

# Identifying text channels
ChannelIDs = {
    'admin':'946600435878354964',
    'todo': '946723733756858388'
}

# Grants authorised users access to ADMINISTRATIVE commands
class Administration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Initialize database, only invokabled by guild owner
    @commands.command(name='init', description="Initializes database.")
    async def init(self, ctx):
        if checkChannelValidity(ctx.channel.id, ChannelIDs['admin']):
            return
        dbStatus = -1
        if check_if_its_me(ctx):
            dbStatus = await create_table(con, dbStatus)
            if dbStatus[1] == 0:
                await ctx.message.author.send("`{}` new table(s) created.".format(dbStatus[2]))
            else: 
                if dbStatus[1] == 1:
                    await ctx.message.author.send("Error encountered. No table created.")

    @commands.command(description="Note user to type sql queries")
    async def sql(self, ctx):
        if checkChannelValidity(ctx.channel.id, ChannelIDs['admin']):
            return
        global queryStat
        try:
            value = queryStat[ctx.author.id]   # First time 
        except KeyError:
            queryStat[ctx.author.id] = 1
        else:
            if value == 0:
                queryStat[ctx.author.id] = 1   # Previous connection was closed
            else:
                return   # User already in querying mode or spamming ;;sql
        await ctx.author.send("Connected to `{}`. Type `exit` to quit.".format(dbPath[1:]))

    # Bot reactions when DM'd
    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if this is DM
        if isinstance(message.channel, discord.DMChannel) and message.author != bot.user:
            global queryStat
            # If user is on queryStat list and querying mode is toggled (1)
            if queryStat[message.author.id] == 1:
                try:            
                    con = sqlite3.connect(dbPath)
                    cur = con.cursor()
                except sqlite3.Error as er:
                    await message.author.send('Connection to `{}` failed.'.format(dbPath[1:]))
                    
                if message.content == 'exit':   # Exit querying
                    await message.author.send("Closed connection to `{}`.".format(dbPath[1:]))
                    queryStat[message.author.id] = 0
                    return
                try: 
                    cur.execute(message.content)
                    await message.author.send("```{}```".format(cur.fetchall()))
                except sqlite3.Error as er:
                    await message.author.send("```{}```".format(catchError(er, 1)))
    
    # Refresh existing user statistics
    @commands.command(description="Verify and update user statistics")
    async def refresh(self, ctx, target = None):
        try:            
            con = sqlite3.connect(dbPath)
            cur = con.cursor()
        except sqlite3.Error as er:
            await ctx.author.send('Connection to `{}` failed.'.format(dbPath[1:]))

        if target == None:   # If users wish to refresh themselves
            target = ctx.author.id
        guild = bot.get_guild(int(guildID))
        
        if guild.get_member(target) is not None:   # If target user is a member of the server
            cur.execute("SELECT user_id FROM user WHERE user_id = ?", (target,))
            result = cur.fetchone()
            if result == None:
                try:
                    cur.execute("INSERT INTO user VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
                        target, 0, 0, 0, 0, 0, 0, False
                    ))
                    con.commit()
                    await ctx.author.send("Successfully updated user statistics.")
                except sqlite3.Error as er:
                    catchError(er, 0)
            else:
                await ctx.author.send("User statistics present. No action needed.")
        else:
            await ctx.author.send("User is not in the server.")
    
# Grants server users access to TODO commands
class ToDo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        
    # # TODO
    # # Create todo items for the day
    # @commands.command()
    # async def todo(self, ctx, *args.split(';')):
    #     print(args)
            
    
    
    

# Add cogs
bot.add_cog(Administration(bot))
#bot.add_cog()

    

# @commands.command(description="Configure pomodoro work and break session")
# try:
#     async def doro(ctx, *args):
        
    
# except:
    



# Create connection to a database file stored locally
try:
    con = sqlite3.connect(dbPath)
    cur = con.cursor()   # create a cursor for the database
    print("Successfully established connection to database {}.".format('user.db'))
    #tableNum = cur.execute('''SELECT count(*) FROM user. WHERE type = 'table';''')
    #print("{} table(s) found.".format(tableNum))
except sqlite3.Error as error:
    print("Error while establishing connection to sqlite.", error)
    raise
    

# Take SQL query from DM
async def sql(query):
    try:
        cur.execute(query)
        return cur.fetchall()
    except sqlite3.Error as er:
        return er

# Create tables in bot's database.
async def create_table(con, dbStatus):
    status = []
    createdTable = 0
    errorCount = 0
    status.append(createdTable)
    
    # Create table for users
    try: 
        cur.execute('''CREATE TABLE user(
            user_id INTEGER PRIMARY KEY,
            pmdr_completed INTEGER,
            pmdr_initiated INTEGER,
            todo_invoked INTEGER,
            todo_completed INTEGER,
            pmdr_canceled INTEGER,
            todo_canceled INTEGER,
            is_focusing BOOLEAN
            )''')
        con.commit()
        createdTable += 1
    except sqlite3.Error as er:
        catchError(er, 0)
        
    # Create table for to-dos created by users
    # Date format: YYYY-MM-DD HH:MM:SS.SSS
    # Todo status: 0: in-progress/postponed; 1: completed; 2: canceled; 3: overdue
    try:
        cur.execute('''CREATE TABLE todo(
            entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER NOT NULL,
            due TEXT,
            content TEXT,
            reminder TEXT,
            todo_status INTEGER,
            FOREIGN KEY(creator_id) REFERENCES user(user_id)
            )''')
        con.commit()
        createdTable += 1
    except sqlite3.Error as er:
        catchError(er, 0)
        
    # Create table for storing following activities
    # Example: A -> B; A -> C; C -> A
    # When B does an action, a check is performed to see if anyone's following B, if there is,
    # send notifications
    try:
        cur.execute('''CREATE TABLE follower(
            following_id INTEGER PRIMARY KEY AUTOINCREMENT,
            follower_id INTEGER NOT NULL,
            followed_owner_id INTEGER NOT NULL,
            FOREIGN KEY(follower_id) REFERENCES user(user_id)
            FOREIGN KEY(followed_owner_id) REFERENCES list(list_id)
            )''')
        con.commit()
        createdTable += 1
    except sqlite3.Error as er:
        catchError(er, 0)
        
    # Create table for every pomodoro sessions
    try:
        cur.execute('''CREATE TABLE pomodoro(
            entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            pmdr_length INTEGER,
            break_length INTEGER,
            pmdr_streak INTEGER,
            pmdr_status INTEGER,
            FOREIGN KEY(entry_id) REFERENCES list(list_id)
            )''')
        con.commit()
        createdTable += 1
    except sqlite3.Error as er:
        catchError(er, 0)
    
    if createdTable >= 1:
        print("{} new table(s) successfully created.".format(createdTable))
        if errorCount > 0:
            print()
        dbStatus = 0   # Successful creation
    else:
        print("WARNING:\n\nError encountered. No new table created.")
        dbStatus = 1   # Tables already exist
    
    status.extend([dbStatus, createdTable])
    return status  # Determine DM output, assigned to dbStatus

bot.run(TOKEN)