from asyncio.windows_events import NULL
import os, discord, sqlite3, traceback, sys, time, math, copy
from dotenv import load_dotenv
from discord.ext import commands, tasks

load_dotenv()
TOKEN = os.getenv("TOKEN")

# Path of .db
dbPath = "/Coding/CS50/final_proj/user.db"  # This is the FULL path, i.e.: D:/user.db
print("\nCurrent path: {}\n".format(os.getcwd()))

# Instance bot
owners = ['695849842244583455']  # ID for Machiavelli#9308
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix = ';;', intents=intents)

# Some constants
guildID = '699678814376034314'
ToDoThreadActive = {}   # True if there a thread counting time since last todo


# Text channel identifications
ChannelIDs = {
    'admin': '946600435878354964',
    'todo': '946723733756858388',
    'follow': '948515104520044584'
}

# All DM contexts, used as value for each member key in DMStat
DMContexts = {
    'following': False,
    'unfollowing': False,
    'updateToDo': False
}

# All the lists/dicts here are initialized after the bot is ready except for queryStat

# Members that have just published todos are toggled as True
# Structure: {"ID1": True; "ID2": False, "ID3": True}
# True members are checked whether their todos have existed for a period of time before announcing to followers
ToDoBufferingCheckList = {}

# A dict that stores query status and userID. If an authorised user wants to access
# .db the dictionary is then updated with key = userID, value = queryStatus
queryStat = {}
# Unless absolutely necessary, futher applications should adopt DMStat (see below)

# Improved version of queryStat that stores DM status for more applications
# Struture: {"UserID": {"following": True, "Unfollowing": False}}
# Above shows an user in "want to follow an user" context in DM w/ bot
# Only when this is True that commands related to following an user can be invoked
DMStat = {}

# Store todo items awaiting being DM'd to followers
# Structure: {"ownerID": {"todoContent": "creationTime", "todo2": "time2"}}
# Once notifications have been sent value of ownerID is cleared
ToDoBuffer = {}

# Store members and their respective userName#0000
# Structure: {"695849842244583455": "Sillycon#0078"}
userNameToID = {}


# Fill a dict with all members as keys and values as defaultValue
def populateDict(dict, defaultValue):
    for guild in bot.guilds:
        if guild.id == int(guildID):   # This bot is for private use only
            for member in guild.members:
                if isinstance(defaultValue, type(dict)):   # A dict can't be directly copied
                    dictTemp = copy.deepcopy(defaultValue)
                    dict[member.id] = dictTemp
                    continue
                dict[member.id] = defaultValue

# Check if it's me the owner
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

# Check if a command is invoked in an authorised channel
def checkChannelValidity(activeChannelID, validChannelID):
    for channelID in validChannelID:
        if str(activeChannelID) == channelID:
            return False   # False if sent channel is VALID
    return True   # True if sent channel is NOT VALID
    
# Return True if given list is NOT empty
def checkNotEmptyList(list):
    return not not list

# Get userID from username#0000
def getID(username):
    for attempt in range(3):
        global keepLooping
        keepLooping = True
        try:
            for key, val in userNameToID.items():   # Dict, key is ID, val is username#0000
                if val == username:
                    followingID = key
                    keepLooping = False   # This is only False if a valid user is found!
                    break
            if keepLooping == False:
                return followingID
            raise KeyError   # If every key val is exhausted and no user is found
        
        except RuntimeError:   # If a new user just joined, new key val pair will be added
            time.sleep(1)      # to userNameToID causing dict size changed error
        except KeyError:
            return 1
    if keepLooping:
        return 2   # If for some reason the entire userNameToID{} was looped thrice and still no match

# Toggle DM context and optionally verify channel
# Invoked when a DM session is to be opened for taking further commands
# Fourth argument: 0 toggles OFF; 1 toggles ON
def toggleDM(userID, context, onOff, channelID=NULL, validChannels=NULL):
    if (channelID != NULL) or (validChannels != NULL):   # Channel verification 
        if checkChannelValidity(channelID, validChannels):
            return False   # False if channel is NOT VALID
    contextName = str(context)
    if onOff == 1:
        # Toggle every other context off
        for k, v in DMStat[userID].items():
            if v == True:
                DMStat[userID][k] = False
        try:
            _ = DMStat[userID][contextName]
        # When a context is new
        except KeyError:
            pass   # Doesn't matter since next line adds a new context regardless
        DMStat[userID][contextName] = True  # Toggle on context
    else:
        DMStat[userID][contextName] = False
    return True

# Convert seconds to hh:mm
def convertSecTohhmm(value):
    if value < 0:
        return NULL   # Ignore invalid time values
    inHour = value/3600
    hh = math.trunc(inHour)
    mm = math.trunc((inHour - hh) * 60)
    ss = math.trunc((((inHour - hh) * 60) - mm) * 60)
    return f"{hh}:{mm}:{ss}"

# Compare currentTime with input and return True if some condition is met
# Used mainly in checking if a certain amount of time has passed since someone
# last made a todo item
async def compareTime(difference):
    endThread = False
    global ToDoThreadActive, ToDoBuffer, ToDoBufferingCheckList
    
    # In ToDoBufferingCheckList members who published todos recently are set to True
    for attempt in range(5):   # 5 attempts for runtimeError
        try:
            while True in list(ToDoBufferingCheckList.values()):
                # Get all items in the form of (ID, status)
                for pos, (authorID, publishStatus) in enumerate(ToDoBufferingCheckList.items()):
                    if publishStatus:
                        author = str(authorID)
                        # Check if ToDoBuffer has todo items, since new todos might be added or
                        # deleted as a result of expired buffering todos
                        # If there is none this author can be safely skipped
                        if ToDoBuffer.get(author) != None:
                            try:   # Get creation time of latest todo item
                                lastToDoTime = next(reversed(ToDoBuffer[author].values()))
                                diff = time.time() - float(lastToDoTime)  # Compare to current time
                                if diff > difference:
                                    print(f"It has been {difference} seconds since last todo.")
                                    notificationResult = await notifyFollowers(author)
                                    if notificationResult == 1:
                                        raise RuntimeError
                                    ToDoBuffer[author].clear()
                            except StopIteration as e:
                                ToDoBufferingCheckList[authorID] = False
                                print(e)
                            continue   # Check next author since current todos haven't expired
                        
                        # If no buffering todos left this author is not checked next time
                        elif ToDoBuffer.get(author) == None:
                            ToDoBufferingCheckList[authorID] = False

                    continue   # Next author
            # Terminate thread 
            ToDoThreadActive = False
            endThread = True
            break
        except RuntimeError:   # Caused by new user joining -> Dict size changed during iteration
            time.sleep(1)      # Otherwise there might be a problem with database connection (see notifyFollowers())
        if endThread:   # Confirm thread termination
            break
        
    if not endThread:
        print("`compareTime()`: RuntimeError encountered after 5 attempts.")
        ToDoThreadActive = False

# DM followers about an update on todo items from following users
async def notifyFollowers(author):
    try:            
        con = sqlite3.connect(dbPath)
        cur = con.cursor()
    except sqlite3.Error as er:
        print('Connection to `{}` failed.'.format(dbPath[1:]))
        return 1   # This raises RuntimeError
        
    cur.execute('''SELECT follower_id, followed_owner_id FROM follower WHERE
                followed_owner_id = ?''', (author,))
    for er, ed in cur.fetchall():
        try:
            ToDos = ""
            follower = bot.get_user(int(er))
            followed = bot.get_user(int(ed))
            followedName = followed.display_name
            for k, v in ToDoBuffer[author].items():
                currToDo = f"{k}\n"
                ToDos += currToDo
            await follower.send(f"`{followedName}` has started working on the following:\n```\n{ToDos}\n```")
        except Exception as e:
            print(e)
        return 0

# When bot is ready
@bot.event
async def on_ready():
    print("Logged in as {0.user}".format(bot))

    # Initialize some lists, dicts that require server info
    global DMStat, ToDoBufferingCheckList, DMContexts
    populateDict(DMStat, DMContexts)
    populateDict(ToDoBufferingCheckList, False)
    
    # Populate userNameToID
    for guild in bot.guilds:
        if guild.id == int(guildID):   # This bot is for private use only
            for member in guild.members:
                id = member.id
                name = str(member.name)
                disc = str(member.discriminator)
                userNameToID[f"{id}"] = f"{name}" + "#" + f"{disc}"

# Initialize user table row for new users
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

    # Add new user key val pairs into dicts
    name = str(member.username)
    disc = str(member.discriminator)
    userNameToID[member.id] = f"{name}" + "#" + f"{disc}"
    
    DMStat[member.id] = DMContexts
    ToDoBufferingCheckList[member.id] = False

# Grant authorised users access to ADMINISTRATIVE commands
class Administration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Initialize database, only invokabled by guild owner
    @commands.command(name='init', description="Initializes database.")
    async def init(self, ctx):
        validChannels = [ChannelIDs['admin']]
        if checkChannelValidity(ctx.channel.id, validChannels):
            return
        dbStatus = -1
        if check_if_its_me(ctx):
            dbStatus = await create_table(con, dbStatus)
            if dbStatus[1] == 0:
                await ctx.message.author.send("`{}` new table(s) created.".format(dbStatus[2]))
            else: 
                if dbStatus[1] == 1:
                    await ctx.message.author.send("Error encountered. No table created.")
        
    # Prompt for a sql query
    @commands.command(description="Note user to type sql queries")
    async def sql(self, ctx):
        validChannels = [ChannelIDs['admin']]
        if checkChannelValidity(ctx.channel.id, validChannels):
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
            try:
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
                        con.commit()
                        try:
                            await message.author.send("```{}```".format(cur.fetchall()))
                        except discord.errors.HTTPException as er:
                            await message.author.send(f"{er}")
                            for row in cur:
                                print(row)
                    except sqlite3.Error as er:
                        await message.author.send("```{}```".format(catchError(er, 1)))
            except KeyError:
                pass   # User never queried activated other contexts
    
            # 'following' context
            if DMStat[message.author.id].get('following'):
                caller = message.author.display_name
                global isCommand
                isCommand = False
                
                try:            
                    con = sqlite3.connect(dbPath)
                    cur = con.cursor()
                except sqlite3.Error as er:
                    await message.author.send('Connection to `{}` failed.'.format(dbPath[1:]))
                    
                # Exit context
                if message.content == ';nvm':
                    DMStat[message.author.id]['following'] = False
                    isCommand = True
                    return
                
                # See all active subscriptions
                if message.content == ';list':
                    caller = str(message.author.id)
                    cur.execute('''SELECT follower_id, followed_owner_id FROM follower WHERE 
                                follower_id = ?''', (caller, ))
                    subscriptions = cur.fetchall()
                    sub = ""
                    for follower, followering in subscriptions:
                        # Convert to usernames
                        userName = userNameToID[str(followering)]
                        currSub = f"{userName}\n"
                        sub += currSub
                    await message.author.send(f"```\n{sub}\n```")
                    isCommand = True
                    return
                
                # Unsub from a user
                if message.content[:6] == ';unsub' and message.content[:9] != ';unsuball':
                    if len(message.content) < 7:
                        await message.author.send(f"Error: Missing `username#0000`. Please try again.")
                        isCommand = True
                        return
                    unsubID = str(getID(message.content[7:]))
                    if unsubID == 1:   # If user does not exist
                        await message.author.send(f"`{message.content[8:]}`: No such user.")
                        isCommand = True
                        return
                    caller = str(message.author.id)
                    
                    # Check if user is being followed by caller
                    unsubName = str(message.content[7:])
                    cur.execute('''SELECT follower_id, followed_owner_id FROM follower WHERE
                            follower_id = ? AND  followed_owner_id = ?''', (caller, unsubID))
                    if cur.fetchone() == None:
                        await message.author.send(f"You are currently not following `{unsubName}`.")
                        isCommand = True
                        return    
                    
                    # Delete a following
                    cur.execute('''DELETE FROM follower WHERE follower_id = ? AND followed_owner_id = ?''',
                                (caller, unsubID))
                    con.commit()
                    await message.author.send(f"Successfully unfollowed `{unsubName}`.")
                    isCommand = True
                
                # Delete all subscriptions
                if message.content[:9] == ';unsuball':
                    if len(message.content) < 10:
                        await message.author.send(f"Error: Missing `username#0000`.")
                        isCommand = True
                        return
                    
                    # Confirm deletion
                    callerUserName = message.author.display_name + "#" + message.author.discriminator
                    if callerUserName == str(message.content[10:]):
                        cur.execute('''DELETE FROM follower WHERE follower_id = ?''',
                                    (caller, ))
                        con.commit()
                        await message.author.send(f"Successfully cleared all subscriptions.")
                        isCommand = True
                    else:
                        await message.author.send(f"Incorrect `username#0000`.")
                        isCommand = True
                
                # Get userID from username#0000
                if not isCommand:  # Skip if the message was a command
                    followingID = getID(message.content)
                    if followingID == 1:
                        await message.author.send(f"`{message.content}`: No such user. Please try again.")
                    elif followingID == 2:
                        print(f"`{caller} called ;;sub: Unknown error occurred. Conversion failed after 3 attempts.`")
                    else:                           
                    # Check if following row exists
                        cur.execute('''SELECT follower_id, followed_owner_id FROM follower WHERE
                                    follower_id = ? AND followed_owner_id = ?''', (message.author.id, followingID))
                        if cur.fetchone() == None:   # Add to database if it does not exist
                            try:
                                cur.execute("INSERT INTO follower VALUES (NULL, ?, ?)", (
                                    message.author.id, followingID
                                ))
                                con.commit()
                                await message.author.send(f"Successfully subscribed to `{message.content}`.\nType another `Username#0000` or `;nvm` to quit.")
                            except sqlite3.Error as er:
                                catchError(er, 0)
                                await message.author.send(f"`{message.content}`: Subscribing failed. Please try again later.")
                        else:
                            await message.author.send(f"`{message.content}`: You have already subscribed to this user.")
    
            # 'updateToDo' context
            if DMStat[message.author.id].get('updateToDo'):
                caller = message.author.display_name   # Caller memberID in string
                isCommand = False
                
                try:            
                    con = sqlite3.connect(dbPath)
                    cur = con.cursor()
                except sqlite3.Error as er:
                    await message.author.send('Connection to `{}` failed.'.format(dbPath[1:]))
                    
                # Exit context
                if message.content == ';nvm':
                    DMStat[message.author.id]['updateToDo'] = False
                    isCommand = True
                    return
                    
                # Complete a todo
                if message.content == ';done':
                    pass
                
                
    
    # Refresh existing user statistics
    @commands.command(description="Verify and update user statistics")
    async def refresh(self, ctx, target = None):
        validChannels = [ChannelIDs['admin']]
        if checkChannelValidity(ctx.channel.id, validChannels):
            return
        try:            
            con = sqlite3.connect(dbPath)
            cur = con.cursor()
        except sqlite3.Error as er:
            await ctx.author.send('Connection to `{}` failed.'.format(dbPath[1:]))

        # If users wish to refresh themselves
        if target == None:
            target = ctx.author.id
        guild = bot.get_guild(int(guildID))
        
        if guild.get_member(target) is not None:   # If target user is a member of the server
            cur.execute("SELECT user_id FROM user WHERE user_id = ?", (target,))
            result = cur.fetchone()

            # Check if user has entry in table 'user'
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
    
# Grant server users access to TODO commands
class ToDo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Create a todo item
    @commands.command(description="Create a todo")
    async def todo(self, ctx, *, content):
        validChannels = [ChannelIDs['admin'], ChannelIDs['todo']]
        if checkChannelValidity(ctx.channel.id, validChannels):
            return
        try:            
            con = sqlite3.connect(dbPath)
            cur = con.cursor()
        except sqlite3.Error as er:
            await ctx.author.send('Connection to `{}` failed.'.format(dbPath[1:]))
        
        # Create an in-progress todo entry in table 'todo'
        try:
            createdTime = time.time()
            cur.execute("INSERT INTO todo VALUES (NULL, ?, ?, ?, ?)", (
                ctx.author.id, content, 0, createdTime
            ))
            con.commit()
            con.close()
        except sqlite3.Error as er:
            await ctx.author.send('Connection to `{}` failed.'.format(dbPath[1:]))
        
        # Add todo items to buffer waiting to be DM'd
        author = ctx.author.id
        todo = content
        currTime = time.time()
        if ToDoBuffer.get(f"{author}") == None:
            ToDoBuffer[f"{author}"] = {}
        ToDoBuffer[f"{author}"][f"{todo}"] = f"{currTime}"
        
        # Toggle author to True so published todos are looped to compare time
        global ToDoThreadActive, ToDoBufferingCheckList
        ToDoBufferingCheckList[author] = True            
        
        # Invoke a looping background task that checks for todo notification expiry
        expiryTime = 3
        self.compareTime.start(expiryTime)
        
    # Manage todos
    @commands.command(description="Edit or complete published todos")
    async def update(self, ctx):
        validChannels = [ChannelIDs['todo']]
        if toggleDM(ctx.author.id, 'updateToDo', 1, ctx.channel.id, validChannels):
            cmd = ''';done     <item>         |  Complete a todo and notify followers.\n;edit     <item>         |  Edit todo content.\n;delete   <item>         |  Delete a todo and notify followers.'''
            await ctx.author.send(f"Here you can edit, delete or complete a todo item. Type `;nvm` to quit, or try the following commands:```\n{cmd}\n```")
            
            # Return a list of todos with remaining time displayed in hh:mm:ss
            try:
                con = sqlite3.connect(dbPath)
                cur = con.cursor()
            except sqlite3.Error as er:
                print('Connection to `{}` failed.'.format(dbPath[1:]))
            cur.execute("SELECT content, creation_time FROM todo WHERE creator_id = ?", 
                        (str(ctx.author.id), ))
            results = cur.fetchall()
            todo = ""
            
            # Loop through each todo and its creation time
            for content, creationTime in results:
                if creationTime == None:   #DEBUG
                    continue   # DEBUG
                remainingTime = (float(creationTime) + 86400) - time.time()
                convertedTime = convertSecTohhmm(remainingTime)
                if convertedTime == NULL:
                    continue   # Invalid remainingTime
                currTask = content + f"  ({convertedTime})\n"
                todo += currTask
            await ctx.author.send(f"See below for all currently active items with remaining time in (`hh:mm:ss`):```\n{todo}\n```")
    
    # Executed every 0.1 second to check if some buffering ToDos are ready to be DM'd
    @tasks.loop(seconds=0.1)
    async def compareTime(self, difference):
        global endTask
        endTask = False
        global ToDoBuffer, ToDoBufferingCheckList
        
        # In ToDoBufferingCheckList members who published todos recently are set to True
        for attempt in range(3):   # 3 attempts for runtimeError
            try:
                # Get all items in the form of (ID, status)
                for pos, (authorID, publishStatus) in enumerate(ToDoBufferingCheckList.items()):
                    if publishStatus:
                        author = str(authorID)
                        # Check if ToDoBuffer has todo items, since new todos might be added or
                        # deleted as a result of expired buffering todos
                        # If there is none this author can be safely skipped
                        if ToDoBuffer.get(author) != None:
                            try:   # Get creation time of latest todo item
                                lastToDoTime = next(reversed(ToDoBuffer[author].values()))
                                diff = time.time() - float(lastToDoTime)  # Compare to current time
                                if diff > difference:
                                    print(f"It has been {difference} seconds since last todo.")
                                    notificationResult = await notifyFollowers(author)
                                    if notificationResult == 1:
                                        raise RuntimeError
                                    ToDoBuffer[author].clear()
                            except:
                                ToDoBufferingCheckList[authorID] = False
                            continue   # Check next author since current todos haven't expired
                        
                        # If no buffering todos left this author is not checked next time
                        elif ToDoBuffer.get(author) == None:
                            ToDoBufferingCheckList[authorID] = False

                    continue   # Next author
                # Terminate task early if the entire checklist has been looped
                endTask = True
                
            except RuntimeError:   # Caused by new user joining -> Dict size changed during iteration
                time.sleep(1)      # Otherwise there might be a problem with database connection (see notifyFollowers())
            if endTask:
                break
        if endTask:
            return
        else:
            # If there is still a problem with looping the for loop    
            print("`compareTime()`: RuntimeError encountered after 3 attempts.")
            return

    # Follow an user
    @commands.command(description="Follow an user")
    async def sub(self, ctx):
        validChannels = [ChannelIDs['follow']]
        if toggleDM(ctx.author.id, 'following', 1, ctx.channel.id, validChannels):
            # Code blocks are defined as ```\n{text}\n```
            # Inside {text} \n is interpreted as normal
            cmd = ''';list                   |  See all active subscriptions.\n;unsub <username#0000>  |  Unsubscribe from an user.\n;unsuball <Your UserName>  |  Clear all subscriptions.'''
            await ctx.author.send(f"Who do you wish to subscribe?\nEnter a `Username#0000`, or `;nvm` to quit. Or you can try the following:```\n{cmd}\n```")

# Add cogs
bot.add_cog(Administration(bot))
bot.add_cog(ToDo(bot))

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
            content TEXT,
            creation_time TEXT,
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