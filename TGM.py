import discord
from discord.ext import commands
from discord.player import Player, SpotifyProvider
import os

# ============================================
# CONFIGURATION
# ============================================

# Setup Intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# Initialize Bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize Player
player = Player(bot)

# Setup Spotify Provider
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')

if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    player.add_provider(
        SpotifyProvider,
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
    print("✅ Spotify Provider loaded!")
else:
    print("⚠️ Spotify credentials not found!")

# ============================================
# EVENTS
# ============================================

@bot.event
async def on_ready():
    print(f'╔══════════════════════════════════════╗')
    print(f'║   🎵 Bot {bot.user.name} is online!      ║')
    print(f'║   Guilds: {len(bot.guilds)}                      ║')
    print(f'╚══════════════════════════════════════╝')
    await bot.change_presence(activity=discord.Game(name="🎵 Music | !help"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command tidak ditemukan!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Args kurang! Contoh: `!play nama lagu`")
    else:
        await ctx.send(f"❌ Error: {error}")

# ============================================
# MUSIC COMMANDS
# ============================================

@bot.command(name="play", aliases=["p", "pl"])
async def play(ctx, *, query):
    """Main command untuk memutar musik"""
    try:
        await player.play(ctx, query)
        await ctx.send(f"🎶 Playing: {query}")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="pause")
async def pause(ctx):
    """Jeda musik"""
    try:
        await player.pause(ctx)
        await ctx.send("⏸️ Paused!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="resume")
async def resume(ctx):
    """Lanjutkan musik"""
    try:
        await player.resume(ctx)
        await ctx.send("▶️ Resumed!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="skip", aliases=["s", "next"])
async def skip(ctx):
    """Lewati lagu"""
    try:
        await player.skip(ctx)
        await ctx.send("⏭️ Skipped!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="stop")
async def stop(ctx):
    """Stop musik dan keluar voice"""
    try:
        await player.stop(ctx)
        await ctx.send("⏹️ Stopped!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="queue", aliases=["q", "list"])
async def queue(ctx):
    """Tampilkan antrian lagu"""
    try:
        await player.show_queue(ctx)
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="nowplaying", aliases=["np", "current"])
async def nowplaying(ctx):
    """Tampilkan lagu yang sedang diputar"""
    try:
        current = player.current
        if current:
            embed = discord.Embed(
                title="🎵 Sedang Diputar",
                description=current.name,
                color=0x1DB954  # Spotify Green
            )
            embed.add_field(name="Duration", value=str(current.duration))
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Tidak ada lagu yang diputar!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="volume", aliases=["vol"])
async def volume(ctx, value: int = None):
    """Atur volume (0-100)"""
    try:
        if value is None:
            current_vol = player.volume
            await ctx.send(f"🔊 Volume saat ini: {current_vol}%")
        else:
            await player.set_volume(ctx, value)
            await ctx.send(f"🔊 Volume: {value}%")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="loop")
async def loop(ctx):
    """Ulangi lagu saat ini"""
    try:
        if player.is_looping:
            await player.set_loop(ctx, False)
            await ctx.send("🔁 Loop dimatikan!")
        else:
            await player.set_loop(ctx, True)
            await ctx.send("🔁 Loop diaktifkan!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

# ============================================
# UTILITY COMMANDS
# ============================================

@bot.command(name="help")
async def help_command(ctx):
    """Tampilkan bantuan"""
    embed = discord.Embed(
        title="🎵 Bot Music Help",
        description="Prefix: `!`",
        color=0x1DB954
    )
    embed.add_field(name="!play <lagu/link>", value="Mainkan musik", inline=False)
    embed.add_field(name="!pause", value="Jeda musik", inline=False)
    embed.add_field(name="!resume", value="Lanjutkan musik", inline=False)
    embed.add_field(name="!skip", value="Lewati lagu", inline=False)
    embed.add_field(name="!stop", value="Stop musik", inline=False)
    embed.add_field(name="!queue", value="Tampilkan antrian", inline=False)
    embed.add_field(name="!np / !nowplaying", value="Lagu yang diputar", inline=False)
    embed.add_field(name="!volume <0-100>", value="Atur volume", inline=False)
    embed.add_field(name="!loop", value="Ulangi lagu", inline=False)
    embed.add_field(name="!help", value="Tampilkan help ini", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="ping")
async def ping(ctx):
    """Cek latency bot"""
    await ctx.send(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")

@bot.command(name="join")
async def join(ctx):
    """Bot join voice channel"""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"✅ Joined {channel.name}!")
    else:
        await ctx.send("❌ Kamu harus di voice channel dulu!")

@bot.command(name="leave")
async def leave(ctx):
    """Bot keluar voice channel"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left voice channel!")
    else:
        await ctx.send("❌ Bot tidak di voice channel!")

# ============================================
# RUN BOT
# ============================================

TOKEN = os.environ.get('DISCORD_TOKEN')

if TOKEN is None:
    print("╔══════════════════════════════════════╗")
    print("║ ❌ ERROR: DISCORD_TOKEN tidak ada!   ║")
    print("╚══════════════════════════════════════╝")
else:
    print("🚀 Starting bot...")
    bot.run(TOKEN)
