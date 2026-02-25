"""
🎵 Discord Music Bot dengan Spotify - Pakai Wavelink
"""

import discord
from discord.ext import commands
import wavelink
import os

# ============================================
# CONFIGURATION
# ============================================

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')

# Setup Intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# Initialize Bot
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# ============================================
# EVENTS
# ============================================

@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user.name} is online!')
    print(f'Guilds: {len(bot.guilds)}')
    
    # Initialize Wavelink nodes
    await wavelink.NodePool.create_node(
        bot=bot,
        host="lavalinkinc.ml",
        port=443,
        password="youshallnotpass",
        https=True,
        identifier="Main Node"
    )
    print("✅ Wavelink Node connected!")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command tidak ditemukan!")
    else:
        await ctx.send(f"❌ Error: {str(error)}")

# ============================================
# MUSIC COMMANDS
# ============================================

@bot.command(name="play", aliases=["p", "pl"])
async def play(ctx, *, query):
    if not ctx.author.voice:
        await ctx.send("❌ Kamu harus di voice channel!")
        return
    
    try:
        # Get or create player
        player = ctx.voice_client
        if not player:
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        
        # Search for track
        query = f"ytsearch:{query}"
        tracks = await wavelink.NodePool.get_node().get_tracks(wavelink.YouTubeTrack, query)
        
        if not tracks:
            await ctx.send("❌ Lagu tidak ditemukan!")
            return
        
        track = tracks[0]
        await player.play(track)
        await ctx.send(f"🎶 Playing: **{track.title}**")
        
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")
        print(f"Error: {e}")

@bot.command(name="pause")
async def pause(ctx):
    player = ctx.voice_client
    if player:
        await player.pause()
        await ctx.send("⏸️ Paused!")
    else:
        await ctx.send("❌ Tidak ada musik!")

@bot.command(name="resume")
async def resume(ctx):
    player = ctx.voice_client
    if player:
        await player.resume()
        await ctx.send("▶️ Resumed!")
    else:
        await ctx.send("❌ Tidak ada musik!")

@bot.command(name="stop")
async def stop(ctx):
    player = ctx.voice_client
    if player:
        await player.stop()
        await ctx.send("⏹️ Stopped!")
    else:
        await ctx.send("❌ Tidak ada musik!")

@bot.command(name="skip")
async def skip(ctx):
    player = ctx.voice_client
    if player:
        await player.stop()
        await ctx.send("⏭️ Skipped!")
    else:
        await ctx.send("❌ Tidak ada musik!")

@bot.command(name="nowplaying", aliases=["np"])
async def nowplaying(ctx):
    player = ctx.voice_client
    if player and player.current:
        track = player.current
        await ctx.send(f"🎵 Sedang diputar: **{track.title}**")
    else:
        await ctx.send("❌ Tidak ada lagu!")

@bot.command(name="join", aliases=["masuk"])
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect(cls=wavelink.Player)
        await ctx.send(f"✅ Joined {ctx.author.voice.channel.name}!")
    else:
        await ctx.send("❌ Kamu harus di voice channel!")

@bot.command(name="leave", aliases=["keluar"])
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left!")
    else:
        await ctx.send("❌ Bot tidak di voice!")

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency*1000)}ms")

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(title="🎵 Bot Help", color=0x1DB954)
    embed.add_field(name="!play <lagu>", value="Mainkan musik", inline=False)
    embed.add_field(name="!pause", value="Jeda", inline=False)
    embed.add_field(name="!resume", value="Lanjut", inline=False)
    embed.add_field(name="!stop", value="Stop", inline=False)
    embed.add_field(name="!skip", value="Skip", inline=False)
    embed.add_field(name="!np", value="Lagu sekarang", inline=False)
    embed.add_field(name="!join", value="Bot masuk voice", inline=False)
    embed.add_field(name="!leave", value="Bot keluar voice", inline=False)
    embed.add_field(name="!ping", value="Cek ping", inline=False)
    await ctx.send(embed=embed)

# ============================================
# RUN BOT
# ============================================

if __name__ == "__main__":
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("❌ DISCORD_TOKEN tidak ada!")
