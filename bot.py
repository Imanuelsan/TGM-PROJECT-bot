import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} online!")
    print(f"Guilds: {len(bot.guilds)}")

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency*1000)}ms")

@bot.command(name="help")
async def help_cmd(ctx):
    await ctx.send("✅ Bot Online! Ketik !ping untuk test.")

TOKEN = os.environ.get("DISCORD_TOKEN")

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ DISCORD_TOKEN tidak ada!")
