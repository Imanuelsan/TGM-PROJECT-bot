"""
🎵 Discord Music Bot dengan Spotify Support
Deploy di Railway
"""

import discord
from discord.ext import commands
import wavelink
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

# ============================================
# CONFIGURATION
# ============================================

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')

# Setup Spotify
sp = None
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    auth_manager = SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    print("✅ Spotify connected!")

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
# HELPER FUNCTIONS
# ============================================

def get_spotify_track_info(url):
    """Ambil info dari Spotify track URL"""
    try:
        track_id = url.split("/")[-1].split("?")[0]
        track = sp.track(track_id)
        return {
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "duration": track["duration_ms"] / 1000,
            "url": url
        }
    except Exception as e:
        print(f"Spotify error: {e}")
        return None

def get_spotify_playlist_info(url):
    """Ambil info dari Spotify playlist URL"""
    try:
        playlist_id = url.split("/")[-1].split("?")[0]
        results = sp.playlist_items(playlist_id)
        tracks = results["items"]
        return [item["track"]["external_urls"]["spotify"] for item in tracks if item["track"]]
    except Exception as e:
        print(f"Spotify playlist error: {e}")
        return []

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

@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f"🎵 Node {node.identifier} is ready!")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command tidak ditemukan!")
    else:
        await ctx.send(f"❌ Error: {str(error)}")
        print(f"Error: {error}")

# ============================================
# MUSIC COMMANDS
# ============================================

@bot.command(name="play", aliases=["p", "pl"])
async def play(ctx, *, query):
    """Mainkan musik dari YouTube atau Spotify"""
    if not ctx.author.voice:
        await ctx.send("❌ Kamu harus di voice channel!")
        return
    
    try:
        # Connect to voice
        if not ctx.voice_client:
            vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc = ctx.voice_client
        
        # Check if Spotify URL
        if "spotify.com" in query:
            if "track" in query:
                # Single track
                info = get_spotify_track_info(query)
                if info:
                    search_query = f"{info['name']} {info['artist']}"
                    tracks = await vc.node.get_tracks(wavelink.YouTubeTrack, f"ytsearch:{search_query}")
                    if tracks:
                        track = tracks[0]
                        await vc.play(track)
                        await ctx.send(f"🎶 Playing: **{track.title}**")
                    else:
                        await ctx.send("❌ Lagu tidak ditemukan!")
                else:
                    await ctx.send("❌ Invalid Spotify URL!")
            elif "playlist" in query:
                # Playlist
                tracks = get_spotify_playlist_info(query)
                for track_url in tracks[:10]:  # Max 10 tracks
                    info = get_spotify_track_info(track_url)
                    if info:
                        search_query = f"{info['name']} {info['artist']}"
                        tracks_search = await vc.node.get_tracks(wavelink.YouTubeTrack, f"ytsearch:{search_query}")
                        if tracks_search:
                            await vc.play(tracks_search[0])
                await ctx.send(f"🎶 Added {len(tracks[:10])} tracks to queue!")
            else:
                await ctx.send("❌ Invalid Spotify URL!")
        else:
            # YouTube search
            tracks = await vc.node.get_tracks(wavelink.YouTubeTrack, f"ytsearch:{query}")
            if not tracks:
                await ctx.send("❌ Lagu tidak ditemukan!")
                return
            
            track = tracks[0]
            await vc.play(track)
            await ctx.send(f"🎶 Playing: **{track.title}**")
        
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")
        print(f"Play error: {e}")

@bot.command(name="pause")
async def pause(ctx):
    """Jeda musik"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        await ctx.voice_client.pause()
        await ctx.send("⏸️ Paused!")
    else:
        await ctx.send("❌ Tidak ada musik!")

@bot.command(name="resume")
async def resume(ctx):
    """Lanjutkan musik"""
    if ctx.voice_client and ctx.voice_client.is_paused():
        await ctx.voice_client.resume()
        await ctx.send("▶️ Resumed!")
    else:
        await ctx.send("❌ Musik tidak dijeda!")

@bot.command(name="stop")
async def stop(ctx):
    """Stop musik"""
    if ctx.voice_client:
        await ctx.voice_client.stop()
        await ctx.send("⏹️ Stopped!")
    else:
        await ctx.send("❌ Tidak ada musik!")

@bot.command(name="skip", aliases=["s", "next"])
async def skip(ctx):
    """Lewati lagu"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        await ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped!")
    else:
        await ctx.send("❌ Tidak ada musik!")

@bot.command(name="nowplaying", aliases=["np", "current"])
async def nowplaying(ctx):
    """Tampilkan lagu yang diputar"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        track = ctx.voice_client.current
        embed = discord.Embed(
            title="🎵 Sedang Diputar",
            description=f"**{track.title}**",
            color=0x1DB954
        )
        embed.add_field(name="Duration", value=f"{int(track.duration // 60)}:{int(track.duration % 60):02d}", inline=True)
        embed.add_field(name="Source", value=track.source, inline=True)
        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Tidak ada lagu yang diputar!")

@bot.command(name="volume", aliases=["vol"])
async def volume(ctx, value: int = None):
    """Atur volume (0-100)"""
    if ctx.voice_client:
        if value is None:
            await ctx.send(f"🔊 Volume saat ini: {ctx.voice_client.volume * 100}%")
        elif 0 <= value <= 100:
            await ctx.voice_client.set_volume(value / 100)
            await ctx.send(f"🔊 Volume: {value}%")
        else:
            await ctx.send("❌ Volume harus 0-100!")
    else:
        await ctx.send("❌ Bot tidak di voice channel!")

@bot.command(name="queue", aliases=["q"])
async def queue(ctx):
    """Tampilkan queue (placeholder)"""
    await ctx.send("📋 Queue feature coming soon!")

# ============================================
# UTILITY COMMANDS
# ============================================

@bot.command(name="join", aliases=["masuk"])
async def join(ctx):
    """Bot join voice channel"""
    if ctx.author.voice:
        await ctx.author.voice.channel.connect(cls=wavelink.Player)
        await ctx.send(f"✅ Joined **{ctx.author.voice.channel.name}**!")
    else:
        await ctx.send("❌ Kamu harus di voice channel!")

@bot.command(name="leave", aliases=["keluar"])
async def leave(ctx):
    """Bot keluar voice channel"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left voice channel!")
    else:
        await ctx.send("❌ Bot tidak di voice channel!")

@bot.command(name="ping")
async def ping(ctx):
    """Cek latency"""
    await ctx.send(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")

@bot.command(name="help")
async def help_command(ctx):
    """Tampilkan help"""
    embed = discord.Embed(
        title="🎵 Bot Music Help",
        description="Prefix: `!`\n\n**Music Commands:**",
        color=0x1DB954
    )
    embed.add_field(name="!play <lagu/link>", value="Mainkan musik (YouTube/Spotify)", inline=False)
    embed.add_field(name="!pause", value="Jeda musik", inline=False)
    embed.add_field(name="!resume", value="Lanjutkan musik", inline=False)
    embed.add_field(name="!skip", value="Lewati lagu", inline=False)
    embed.add_field(name="!stop", value="Stop musik", inline=False)
    embed.add_field(name="!np", value="Lagu yang diputar", inline=False)
    embed.add_field(name="!volume <0-100>", value="Atur volume", inline=False)
    embed.add_field(name="!join", value="Bot masuk voice", inline=False)
    embed.add_field(name="!leave", value="Bot keluar voice", inline=False)
    embed.add_field(name="!ping", value="Cek latency", inline=False)
    embed.add_field(name="!help", value="Tampilkan help", inline=False)
    embed.set_footer(text="🎵 Spotify Music Bot")
    await ctx.send(embed=embed)

# ============================================
# RUN BOT
# ============================================

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("╔══════════════════════════════════════╗")
        print("║ ❌ ERROR: DISCORD_TOKEN tidak ada!   ║")
        print("╚══════════════════════════════════════╝")
    else:
        print("🚀 Starting bot...")
        bot.run(DISCORD_TOKEN)
