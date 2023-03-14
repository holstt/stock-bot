import discord
from discord import app_commands
import logging
import time
from pathlib import Path
import argparse
from dotenv import load_dotenv
from os import environ as env
from tabulate import tabulate
from src.service import StockSummary, get_weekly_summary  
from table2ascii import table2ascii


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

TARGET_GUILD_ID = discord.Object(int(env.get('TARGET_GUILD_ID')))
DEV_CHANNEL_ID =  discord.Object(int(env.get('DEV_CHANNEL_ID')))

@client.event
async def on_ready():
    # await tree.sync()
    try:
        logger.info(f"Syncing commands to target guild (id: {TARGET_GUILD_ID})...")
        await tree.sync(guild=TARGET_GUILD_ID)
        logger.info("Syncing commands to target guild succeeded")
    except discord.errors.Forbidden as e:
        exception_msg = f"Syncing commands to target guild failed. Access denied for guild with id: {TARGET_GUILD_ID}"
        raise Exception(exception_msg) from e

    ready_msg = f'Bot is online ({client.user})'
    logging.info(ready_msg)
    channel = client.get_channel(DEV_CHANNEL_ID)
    if not channel:
        raise Exception(f"Dev channel not found (id: {DEV_CHANNEL_ID})")

    await channel.send(ready_msg)


# Use Color class
RED = 0xff0000
GREEN = 0x00ff00


@tree.command(name='test', description='Get market summary', guild=TARGET_GUILD_ID)
async def summary(interaction: discord.Interaction):
    # TODO: User should define a portfolio of tickers they want to track
    symbols = ["^OMXC25", "^GSPC", "^DJI", "^IXIC", "^FTSE", "^GDAXI", "^N225", "^HSI"]
     
    # iterate the list of indices and get the weekly summary then put in table ascii
    stocks = [get_weekly_summary(symbol) for symbol in symbols]

    msg = [[stock.symbol, f"{stock.latest_close:.2f}",f"{stock.percent_change_5d:+.2f}%" ] for stock in stocks]

    # insert into table ascii
    table_ascii = table2ascii( 
        header=[f"Symbol", "Price", "Weekly Change"],
        body=msg)

    embed = discord.Embed(title="📈 Weekly Stock Market Update", url="https://finance.yahoo.com/quote/", color=0x00ff00)
    embed.description = f"{table_ascii}"
    await interaction.response.send_message(embed=embed)


client.run(env.get('BOT_TOKEN'))