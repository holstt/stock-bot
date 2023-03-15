import discord
from discord import app_commands
import logging
import time
from pathlib import Path
import argparse
from dotenv import load_dotenv
from os import environ as env
# from tabulate import tabulate
from src.service import StockSummary, get_weekly_summary  
from table2ascii import table2ascii
from typing import TypedDict
from discord.abc import PrivateChannel
from tabulate import tabulate, SEPARATING_LINE
from table2ascii import table2ascii, Alignment

# Setup logging
logging.basicConfig(
    level=logging.NOTSET,
    format='[%(asctime)s] [%(levelname)s] %(name)-25s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logging.Formatter.converter = time.gmtime  # Use UTC
logger = logging.getLogger(__name__)

ap = argparse.ArgumentParser()
# Optional argument for .env file path
ap.add_argument("-e", "--env", required=False,
                help="Path of .env file", default=".env")
args = vars(ap.parse_args())

env_path = args["env"]
if not Path(env_path).exists():
    # print(f"WARNING: No .env file found (path was '{env_path}')")
    raise IOError(f"No .env file found (path was '{env_path}')")

# Load environment
load_dotenv(dotenv_path=args["env"])

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)  # For slash commands


TARGET_GUILD_ID = int(env['TARGET_GUILD_ID'])
DEV_CHANNEL_ID =  int(env['DEV_CHANNEL_ID'])

@client.event
async def on_ready():
    ready_msg = f'Bot is online ({client.user})'
    # await tree.sync()
    try:
        logger.info(f"Syncing commands to target guild (id: {TARGET_GUILD_ID})...")
        # await tree.sync(guild=TARGET_GUILD_ID)
        await tree.sync(guild=discord.Object(TARGET_GUILD_ID))
        logger.info("Syncing commands to target guild succeeded")
    except discord.errors.Forbidden as e:
        exception_msg = f"Syncing commands to target guild failed. Access denied for guild with id: {TARGET_GUILD_ID}"
        raise Exception(exception_msg) from e

    logging.info(ready_msg)
    channel = client.get_channel(DEV_CHANNEL_ID)
    if not channel or not isinstance(channel, discord.abc.Messageable):
        raise Exception(f"Dev channel not found or invalid (id: {DEV_CHANNEL_ID})")

    await channel.send(ready_msg)


# Use Color class
RED = 0xff0000
GREEN = 0x00ff00


# TODO: 

@tree.command(name='stocks-summary', description='Weekly market summary', guild=discord.Object(TARGET_GUILD_ID))
async def summary(interaction: discord.Interaction):
    global cache

    # TODO: User should define a portfolio of tickers they want to track
    symbols = ["^OMXC25", "^GSPC", "^DJI", "^IXIC", "^FTSE", "^GDAXI", "^N225", "^HSI"]
    # symbols = ["^OMXC25", "^GSPC", "^DJI"]
    # symbols = ["^OMXC25"]
    
    # iterate the list of indices and get the weekly summary then put in table ascii
    stockSummaries = [get_weekly_summary(symbol) for symbol in symbols]
    # sort by percent change
    stockSummaries.sort(key=lambda x: x.percent_change_5d, reverse=True)

    # if average of all percent changes is positive, print hello
    if sum([stock.percent_change_5d for stock in stockSummaries]) > 0:
        embed_color = GREEN
    else:
        embed_color = RED


    msg_rows = [[stock.symbol, f"{stock.latest_close:.2f}", f"{stock.percent_change_5d:.2f} %"] for stock in stockSummaries]
    cache = msg_rows


    # msg_rows[1] = SEPARATING_LINE
    table_ascii = table2ascii(
        header=["Symbol", "Price", "Weekly Change"],
        body=msg_rows, alignments=[Alignment.LEFT, Alignment.RIGHT, Alignment.RIGHT])
    
    # make table with left aligned columns
    # table_ascii = tabulate(msg_rows, headers=["Symbol", "Price", "Weekly Change"], tablefmt=table_type, stralign="right")
    # insert into table ascii
    # table_ascii = table2ascii( 
    #     header=["Symbol", "Price", "Weekly Change"],
    #     body=[
    #     [
    #         msg_rows.symbol,
    #         f"{msg_rows.latest_close:.2f}",
    #         f"{msg_rows.percent_change_5d:+.2f}%"]])

    embed = discord.Embed(title="📈 Weekly Stock Market Update", url="https://finance.yahoo.com/quote/", color=embed_color)
    embed.description = f"```{table_ascii}```"
    await interaction.response.send_message(embed=embed)


client.run(env['BOT_TOKEN'])