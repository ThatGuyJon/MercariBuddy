#!/usr/bin/env python3

import os
import database
import time
import discord
import mercari
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
USER = os.getenv('USERNAME')
DATABASE = os.getenv('DATABASE')
PASSWORD = os.getenv('PASSWORD')
HOST = os.getenv('HOST')
PORT = os.getenv('PORT')

connection = database.connect_to_database(USER, DATABASE, PASSWORD, HOST, PORT)
cursor = connection.cursor() # get database cursor
# connect to discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', help_command=None, case_insensitive=True, intents=intents)

class ListingView(discord.ui.View):
    def __init__(self, mercari_url: str, buyee_url: str):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="View on Mercari Japan", url=mercari_url, style=discord.ButtonStyle.link))
        self.add_item(discord.ui.Button(label="View on Buyee", url=buyee_url, style=discord.ButtonStyle.link))

conditions_map = {
    "1": "New, unused.",
    "2": "Like new.",
    "3": "Used - No noticable scratches or dirt.",
    "4": "Used - there are some scratches and dirt.",
    "5": "Used - There are scratches and dirt.",
    "6": "Used - Poor condition."
}

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_message(ctx):
    channel = bot.get_channel(ctx.channel.id)
    messages = [message async for message in ctx.channel.history(limit=5)]

    # this means they are a new user, add to db
    if len(messages) == 1:
        database.add_new_user(connection, cursor)
    await bot.process_commands(ctx)


# help command
@bot.command(name="help", aliases=["h", "?", "commands"])
async def help(ctx):
    if not ctx.guild:
        help_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "help.txt")
        file = open(help_path, "r", encoding="utf-8")
        line = file.read()
        file.close()
        await ctx.send(line)

# add new listing to database
@bot.command(name="add", aliases=["set"])
async def add(ctx, *search):
    if not ctx.guild:
        # checking lengths of input strings
        total = 0
        for word in search:
            total += len(word)

        if total >= 256:
            await ctx.send("**Error:** Search term should be under 256 characters")
            return

        if len(search) == 0:
            await ctx.send("Incorrect usage of command, make sure it is formatted like this: " +
                    "`!add (search term)`")
            return
        
        mercari_search = " ".join(search)

        current_time = int(time.time())

        result = database.add_to_database(connection, cursor, ctx.message.author.id, mercari_search, current_time)

        if result == True:
            database.add_listing(connection, cursor)
            await ctx.send("Now tracking all new posts with the keyword **{}**.".format(mercari_search))
            await set_status()
        elif result == False:
            await ctx.send("You have already set that keyword. Check your keywords with **!list**.")

@bot.command(name="delete", aliases=["remove"])
async def delete(ctx, *search):
    if not ctx.guild:
        # checking if command was input correctly
        if len(search) == 0:
            await ctx.send("Incorrect usage of command, make sure it is formatted like this: " +
                    "`!delete (search term)`")
            return

        mercari_search = " ".join(search)
        user_id = ctx.message.author.id

        result = database.remove_from_database(connection, cursor, user_id, mercari_search)
        if result == True:
            await ctx.send("No longer tracking posts with the keyword **{}**.".format(mercari_search))
            await set_status()
        elif result == False:
            await ctx.send("The keyword **{}** does not exist in the database.".format(mercari_search))

@bot.command()
async def deleteall(ctx):
    if not ctx.guild:
        user_id = ctx.message.author.id
        result = database.delete_all_user_entries(connection, cursor, user_id)
        if result == True:
            await ctx.send("All entries have been deleted.")
            await set_status()
        elif result == False:
            await ctx.send("An error occured while while deleting your entries. Please try again.")

@bot.command()
async def list(ctx):
    if not ctx.guild:
        entries = database.get_user_entries(connection, cursor, ctx.message.author.id)
        num_entries = len(entries)
        message = "**You currently have {} search terms:**\n".format(str(num_entries))
        for search, found in entries:
            message += "{} - {} listings found.\n".format(search, found)

        await ctx.send(message)

@bot.event
async def on_command_error(ctx, error):
    if ctx.command == add:
        print(error)
        await ctx.send("Incorrect usage of command, make sure it is formatted like this: " +
                "`!add (search term)`")
    elif ctx.command == delete:
        print(error)
        await ctx.send("Incorrect usage of command, make sure it is formatted like this: " +
                "`!delete (search term)`")
    elif ctx.command == list:
        print(error)
    elif ctx.command == None:
        await ctx.send("The message sent is not a command, the available commands are: (!help, !add, !delete, !list)\n" + 
                        "If you need further help on how to use these commands type !help")


def create_embed(listing):
    url = "https://jp.mercari.com/item/" + listing['id']
    title = listing['name']
    price = "¥" + listing['price']
    thumbnail = listing['thumbnails'][0]
    condition = conditions_map[listing['itemConditionId']]
    embed=discord.Embed(title=title, url=url, color=0xda5e22)
    embed.add_field(name="Price", value=price, inline=False)
    embed.add_field(name="Condition", value=condition, inline=False)
    embed.set_image(url=thumbnail)
    return embed


@tasks.loop(seconds=30.0)
async def search_loop():
    global connection
    global cursor
    # check for database connection
    result = database.verify_db_connection(connection, cursor)

    # if not connected, reconnect before continuing loop
    if (result == -1):
        connection = database.connect_to_database(USER, DATABASE, PASSWORD, HOST, PORT)
        cursor = connection.cursor() # get database cursor

    entries = database.get_all_entries(connection, cursor)
    if not entries:
        return

    # get a list containing all of the found listings
    for entry in entries:
        user_id = entry[1]
        keyword = entry[2]
        time_checked = entry[3]

        # get listings matching keyword from mercari
        listings = await mercari.get_item_list(keyword)
        if not listings:
            continue

        max_time = 0
        try:
            found_listings = 0
            items = listings.get('items', [])
            for l in items:
                post_created = int(l.get('created', 0))
                if post_created > time_checked:
                    found_listings += 1
                    max_time = max(max_time, post_created)
                    user = await bot.fetch_user(user_id)
                    if user:
                        embed = create_embed(l)
                        item_id = l['id']
                        mercari_url = f"https://jp.mercari.com/item/{item_id}"
                        buyee_url = f"https://buyee.jp/mercari/item/{item_id}"
                        view = ListingView(mercari_url, buyee_url)
                        await user.send("New search result for keyword **{}**.".format(keyword), embed=embed, view=view)

            if found_listings > 0:
                database.add_found_listings(connection, cursor, found_listings)
        except Exception as e:
            print("Error parsing listings:", e)
        
        if max_time > time_checked:
            database.update_entry(connection, cursor, user_id, keyword, max_time)

@search_loop.before_loop
async def before_search():
    await bot.wait_until_ready()

async def set_status():
    num_users = database.get_number_of_unique_users(connection, cursor)[0][0]
    num_entries = database.get_number_of_entries(connection, cursor)[0][0]
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="{} terms for {} users".format(num_entries, num_users)))

def escape_chars(string):
    new_string = string
    chars = ['*','_','|','`','~','>','\\']
    for ch in chars:
        if ch in new_string:
            # replacing ch with escaped version of ch (ex. '*' -> '\*')
            new_string = new_string.replace(ch, "\\" + ch)
    return new_string

async def setup_hook():
    search_loop.start()

bot.setup_hook = setup_hook

if __name__ == "__main__":
    if database.database_setup(connection, cursor):
        # starting bot on main thread
        bot.run(TOKEN)
