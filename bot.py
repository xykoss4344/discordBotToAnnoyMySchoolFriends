import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("🤖 Debate Bot is online and ready to argue!")
    await bot.load_extension("cogs.debater")
    await bot.load_extension("cogs.voice")


@bot.command(name="ping")
async def ping(ctx):
    """Simple health check."""
    await ctx.send(f"🏓 Pong! Latency: {round(bot.latency * 1000)}ms")


bot.run(TOKEN)
