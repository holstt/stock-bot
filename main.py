from io import BytesIO
import logging

import discord
from discord.ext import commands
from table2ascii import Alignment, table2ascii

from src import config, utils
from src.models import StockPricePeriod

# from src.service import get_5d_summary, _create_plot
from src import service

utils.setup_logging()
# utils.setup_logging(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app_config = config.load_config()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="", intents=intents)


@bot.event
async def on_ready():
    await sync_commands()
    logger.info(f"Bot is online ({bot.user})")


async def sync_commands():
    try:
        logger.info(
            f"Syncing commands to target guild (id: {app_config.target_guild})..."
        )
        await bot.tree.sync(guild=discord.Object(app_config.target_guild))
        # await tree.sync()
        logger.info("Syncing commands to target guild succeeded")
    except discord.errors.Forbidden as e:
        exception_msg = f"Syncing commands to target guild failed. Access denied for guild with id: {app_config.target_guild}"
        raise Exception(exception_msg) from e


RED = 0xFF0000
GREEN = 0x00FF00


# Slash command for getting chart of a stock over the last year
@bot.tree.command(
    name="stock-chart",
    description="Returns a 1Y chart of the ticker",
    guild=discord.Object(app_config.target_guild),
)
async def chart(interaction: discord.Interaction, ticker: str):
    logger.info(f"Creating message for ticker: {ticker}")
    await interaction.response.defer()

    result = service.get_chart_message(ticker)

    if not result.buffer:
        logger.info(
            f"Creating message for ticker failed: {ticker}. Returning error message to user"
        )
        await interaction.followup.send(result.error_msg)
        return

    file = discord.File(result.buffer, filename=f"plot-{ticker}.png")

    logger.info(f"Sending message to user for ticker")
    await interaction.followup.send(embed=result.embed, file=file)  # type: ignore


# Slash command for getting weekly summary of stocks
@bot.tree.command(
    name="stock-summary",
    description="Weekly market summary of the stocks you follow",
    guild=discord.Object(app_config.target_guild),
)
async def summary(interaction: discord.Interaction):
    # Defer response, as fetching may take more than 3 seconds (interaction timeout)
    await interaction.response.defer()
    # Get tickers from config
    tickers = app_config.tickers
    logger.info(f"Getting stock summary for {len(tickers)} tickers: {tickers}")

    stock_price_periods = [service.get_5d_summary(ticker) for ticker in tickers]
    stock_price_periods.sort(key=lambda x: x.period_percent_change, reverse=True)

    table_ascii = create_table(stock_price_periods)

    # Set embed color based on whether the sum of all percent changes is positive or negative
    if sum([stock.period_percent_change for stock in stock_price_periods]) > 0:
        embed_color = GREEN
    else:
        embed_color = RED

    embed = create_embed(table_ascii, embed_color, stock_price_periods)
    await interaction.followup.send(embed=embed)


def create_table(stock_price_periods: list[StockPricePeriod]):
    msg_rows = [
        [
            stock.ticker,
            f"{stock.period_close:.2f}",
            f"{stock.period_percent_change:.2f} %",
        ]
        for stock in stock_price_periods
    ]
    table_ascii = table2ascii(
        header=["Ticker", "Last Close", "Weekly Change"],
        body=msg_rows,
        alignments=[Alignment.LEFT, Alignment.RIGHT, Alignment.CENTER],
    )

    return table_ascii


def create_embed(table_ascii, embed_color, stock_price_periods: list[StockPricePeriod]):
    embed = discord.Embed(
        title="📈 Weekly Stock Market Update",
        url="https://finance.yahoo.com/quote/",
        color=embed_color,
    )
    embed.description = f"```{table_ascii}```"

    period_start = stock_price_periods[0].price_entries[0].date
    period_end = stock_price_periods[0].price_entries[-1].date
    trading_days = len(stock_price_periods[0].price_entries)
    embed.set_footer(
        text=f"Data period: {period_start.strftime('%d/%m')} - {period_end.strftime('%d/%m')} ({trading_days} trading days)"
    )

    return embed


bot.run(app_config.bot_token, log_handler=None)
