"""
🎵 Discord Music Bot - Voice Fix
"""

import discord
from discord.ext import commands
import wavelink
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import asyncio

# ============================================
# CONFIGURATION
# ============================================

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')

# Setup Spotify
sp = None
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    try:
        auth_manager = SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        print("✅ Spotify connected!")
    except Exception as e:
        print(f"⚠️ Spotify error: {e}")

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
    print(f'╔══════════════════════════════════════╗')
    print(f'║   🎵 Bot {bot.user.name} is online!       ║')
    print(f'║   Guilds: {len(bot.guilds)}                      ║')
    print(f'╚══════════════════════════════════════╝')
    
    # Initialize Wavelink
    try:
        nodes = wavelink.NodePool()
        await nodes.create_node(
            bot=bot,
            host="lavalinkinc.ml",
            port=443,
            password="youshallnotpass",
            secure=True,
            identifier="Main"
        )
        print("✅ Wavelink connected!")
    except Exception as e:
        print(f"⚠️ Wavelink error: {e}")
        print("⚠️ Music features may not work!")

@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f"🎵 Node {node.identifier} is ready!")

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"❌ Error: {str(error)}")
    print(f"Error: {error}")

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_spotify_track_info(url):
    if not sp:
        return None
    try:
        track_id = url.split("/")[-1].split("?")[0]
        track = sp.track(track_id)
        return {"name": track["name"], "artist": track["artists"][0]["name"]}
    except:
        return None

# ============================================
# MUSIC COMMANDS
# ============================================

@bot.command(name="join", aliases=["masuk"])
async def join(ctx):
    """Bot join voice channel"""
    if not ctx.author.voice:
        await ctx.send("❌ Kamu harus di voice channel dulu!")
        return
    
    try:
        vc = ctx.author.voice.channel
        player = await vc.connect()
        await ctx.send(f"✅ Joined **{vc.name}**!")
        print(f"Joined voice channel: {vc.name}")
    except Exception as e:
        await ctx.send(f"❌ Error join voice: {e}")
        print(f"Join error: {e}")

@bot.command(name="leave", aliases=["keluar"])
async def leave(ctx):
    """Bot leave voice channel"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left voice channel!")
    else:
        await ctx.send("❌ Bot tidak di voice channel!")

@bot.command(name="play", aliases=["p", "pl"])
async def play(ctx, *, query):
    """Mainkan musik"""
    if not ctx.author.voice:
        await ctx.send("❌ Kamu harus di voice channel!")
        return
    
    try:
        # Connect to voice
        if not ctx.voice_client:
            try:
                vc = ctx.author.voice.channel
                await vc.connect()
                await asyncio.sleep(1)  # Tunggu connect
            except Exception as e:
                await ctx.send(f"❌ Gagal connect: {e}")
                return
        
        vc = ctx.voice_client
        
        # Check Spotify
        if "spotify.com" in query and "track" in query:
            info = get_spotify_track_info(query)
            if info:
                query = f"{info['name']} {info['artist']}"
                await ctx.send(f"🔍 Mencari: {query}")
        
        # Search YouTube
        try:
            tracks = await wavelink.NodePool.get_node().get_tracks(
                wavelink.YouTubeTrack, f"ytsearch:{query}"
            )
        except Exception as e:
            await ctx.send(f"❌ Error cari lagu: {e}")
            return
        
        if not tracks:
            await ctx.send("❌ Lagu tidak ditemukan!")
            return
        
        track = tracks[0]
        
        try:
            await vc.play(track)
            await ctx.send(f"🎶 Playing: **{track.title}**")
            print(f"Playing: {track.title}")
        except Exception as e:
            await ctx.send(f"❌ Error play: {e}")
            print(f"Play error: {e}")
        
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")
        print(f"Overall error: {e}")

@bot.command(name="pause")
async def pause(ctx):
    if ctx.voice_client:
        await ctx.voice_client.pause()
        await ctx.send("⏸️ Paused!")

@bot.command(name="resume")
async def resume(ctx):
    if ctx.voice_client:
        await ctx.voice_client.resume()
        await ctx.send("▶️ Resumed!")

@bot.command(name="stop")
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.stop()
        await ctx.send("⏹️ Stopped!")

@bot.command(name="skip")
async def skip(ctx):
    if ctx.voice_client:
        await ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped!")

@bot.command(name="nowplaying", aliases=["np"])
async def nowplaying(ctx):
    if ctx.voice_client and ctx.voice_client.current:
        await ctx.send(f"🎵 **{ctx.voice_client.current.title}**")
    else:
        await ctx.send("❌ Tidak ada lagu!")

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")

@bot.command(name="help")
async def help_command(ctx):
    await ctx.send("""
🎵 **Commands:**

!join - Bot masuk voice
!play <lagu> - Mainkan musik
!pause - Jeda
!resume - Lanjut
!skip - Skip
!stop - Stop
!np - Lagu sekarang
!leave - Bot keluar
!ping - Ping
!help - Help
""")

# ============================================
# RUN BOT
# ============================================

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ ERROR: DISCORD_TOKEN tidak ada!")
    else:
        print("🚀 Starting bot...")
        bot.run(DISCORD_TOKEN)
