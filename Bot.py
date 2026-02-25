"""
🎵 Discord Music Bot - Spotify + YouTube + Lavalink
"""

import discord
from discord.ext import commands
import lavalink
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
LAVALINK_HOST = os.environ.get('LAVALINK_HOST', 'lavalink')
LAVALINK_PASSWORD = os.environ.get('LAVALINK_PASSWORD', 'youshallnotpass')
LAVALINK_PORT = int(os.environ.get('LAVALINK_PORT', 2333))

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

# Add lava link extension
bot.add_lavalink_connection_nodes(
    host=LAVALINK_HOST,
    port=LAVALINK_PORT,
    password=LAVALINK_PASSWORD,
    resume_key='lavalink_resume_key'
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

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"❌ Error: {str(error)}")
    print(f"Error: {error}")

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_spotify_track_info(url):
    """Get track info from Spotify URL"""
    if not sp:
        return None
    try:
        track_id = url.split("/")[-1].split("?")[0]
        track = sp.track(track_id)
        return {
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "album": track["album"]["name"],
            "duration": track["duration_ms"] / 1000
        }
    except Exception as e:
        print(f"Spotify error: {e}")
        return None

def get_spotify_playlist_tracks(url):
    """Get all tracks from Spotify playlist"""
    if not sp:
        return []
    try:
        playlist_id = url.split("/")[-1].split("?")[0]
        results = sp.playlist_items(playlist_id)
        tracks = []
        for item in results['items']:
            if item['track']:
                name = item['track']['name']
                artist = item['track']['artists'][0]['name']
                tracks.append(f"{name} {artist}")
        return tracks[:25]  # Max 25 tracks
    except Exception as e:
        print(f"Playlist error: {e}")
        return []

# ============================================
# MUSIC COMMANDS
# ============================================

@bot.command(name="join", aliases=["masuk", "j"])
async def join(ctx):
    """Bot join voice channel"""
    if not ctx.author.voice:
        await ctx.send("❌ Kamu harus di voice channel dulu!")
        return
    
    try:
        player = bot.lavalink.player_manager.get(ctx.guild.id)
        if not player:
            player = await bot.lavalink.player_manager.create(
                ctx.guild.id,
                endpoint=str(ctx.author.voice.channel.region or 'uswest')
            )
        
        await ctx.author.voice.channel.connect()
        await ctx.send(f"✅ Joined **{ctx.author.voice.channel.name}**!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")
        print(f"Join error: {e}")

@bot.command(name="leave", aliases=["keluar", "dc"])
async def leave(ctx):
    """Bot leave voice channel"""
    try:
        player = bot.lavalink.player_manager.get(ctx.guild.id)
        if player:
            await player.disconnect()
            await ctx.send("👋 Left voice channel!")
        else:
            await ctx.send("❌ Bot tidak di voice channel!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="play", aliases=["p", "pl"])
async def play(ctx, *, query):
    """Mainkan musik dari YouTube/Spotify"""
    if not ctx.author.voice:
        await ctx.send("❌ Kamu harus di voice channel!")
        return
    
    try:
        # Connect to voice if not connected
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()
            await asyncio.sleep(1)
        
        player = bot.lavalink.player_manager.get(ctx.guild.id)
        
        # Handle Spotify
        is_spotify = "spotify.com" in query
        is_playlist = "playlist" in query
        
        if is_spotify and is_playlist:
            # Spotify Playlist
            tracks = get_spotify_playlist_tracks(query)
            if not tracks:
                await ctx.send("❌ Playlist tidak ditemukan!")
                return
            
            await ctx.send(f"📋 Menambahkan {len(tracks)} lagu ke queue...")
            
            for track_name in tracks:
                search_results = await player.get_tracks(f"ytsearch:{track_name}")
                if search_results:
                    await player.add(track=search_results[0])
            
            if not player.is_playing:
                await player.play()
            
            await ctx.send(f"✅ {len(tracks)} lagu ditambahkan!")
            
        elif is_spotify and "track" in query:
            # Spotify Track
            info = get_spotify_track_info(query)
            if info:
                search_query = f"{info['name']} {info['artist']}"
                await ctx.send(f"🔍 Mencari: {search_query}")
                query = search_query
            else:
                await ctx.send("❌ Spotify track tidak ditemukan!")
                return
        
        # YouTube Search
        if not query.startswith("http"):
            query = f"ytsearch:{query}"
        
        tracks = await player.get_tracks(query)
        
        if not tracks:
            await ctx.send("❌ Lagu tidak ditemukan!")
            return
        
        track = tracks[0]
        
        # Add to queue
        await player.add(track=track)
        
        if not player.is_playing:
            await player.play()
        
        await ctx.send(f"🎶 Playing: **{track.title}**")
        
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")
        print(f"Play error: {e}")

@bot.command(name="pause")
async def pause(ctx):
    """Jeda musik"""
    try:
        player = bot.lavalink.player_manager.get(ctx.guild.id)
        if player and player.is_playing:
            await player.pause()
            await ctx.send("⏸️ Paused!")
        else:
            await ctx.send("❌ Tidak ada musik!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="resume")
async def resume(ctx):
    """Lanjutkan musik"""
    try:
        player = bot.lavalink.player_manager.get(ctx.guild.id)
        if player and player.is_paused:
            await player.resume()
            await ctx.send("▶️ Resumed!")
        else:
            await ctx.send("❌ Musik tidak dijeda!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="stop")
async def stop(ctx):
    """Stop musik"""
    try:
        player = bot.lavalink.player_manager.get(ctx.guild.id)
        if player:
            await player.stop()
            await ctx.send("⏹️ Stopped!")
        else:
            await ctx.send("❌ Tidak ada musik!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="skip", aliases=["s"])
async def skip(ctx):
    """Lewati lagu"""
    try:
        player = bot.lavalink.player_manager.get(ctx.guild.id)
        if player and player.is_playing:
            await player.skip()
            await ctx.send("⏭️ Skipped!")
        else:
            await ctx.send("❌ Tidak ada musik!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="nowplaying", aliases=["np", "current"])
async def nowplaying(ctx):
    """Tampilkan lagu yang diputar"""
    try:
        player = bot.lavalink.player_manager.get(ctx.guild.id)
        if player and player.current:
            track = player.current
            embed = discord.Embed(
                title="🎵 Sedang Diputar",
                description=f"**{track.title}**",
                color=0x1DB954
            )
            embed.add_field(name="Duration", value=f"{int(track.duration // 60)}:{int(track.duration % 60):02d}", inline=True)
            embed.add_field(name="Author", value=track.author, inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Tidak ada lagu!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="queue", aliases=["q", "list"])
async def queue(ctx):
    """Tampilkan queue"""
    try:
        player = bot.lavalink.player_manager.get(ctx.guild.id)
        if player and player.queue:
            queue_list = [f"{i+1}. {t.title}" for i, t in enumerate(player.queue[:10])]
            embed = discord.Embed(
                title="📋 Queue",
                description="\n".join(queue_list),
                color=0x1DB954
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Queue kosong!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="volume", aliases=["vol"])
async def volume(ctx, value: int = None):
    """Atur volume"""
    try:
        player = bot.lavalink.player_manager.get(ctx.guild.id)
        if not player:
            await ctx.send("❌ Player tidak ada!")
            return
        
        if value is None:
            await ctx.send(f"🔊 Volume: {player.volume}%")
        elif 0 <= value <= 100:
            await player.set_volume(value)
            await ctx.send(f"🔊 Volume: {value}%")
        else:
            await ctx.send("❌ Volume harus 0-100!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="shuffle")
async def shuffle(ctx):
    """Acak queue"""
    try:
        player = bot.lavalink.player_manager.get(ctx.guild.id)
        if player and player.queue:
            import random
            random.shuffle(player.queue)
            await ctx.send("🔀 Shuffled!")
        else:
            await ctx.send("❌ Queue kosong!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

# ============================================
# UTILITY COMMANDS
# ============================================

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="🎵 Bot Music Help",
        description="Prefix: `!`\n\n**Music Commands:**",
        color=0x1DB954
    )
    embed.add_field(name="!play <lagu/link>", value="Mainkan musik (YT/Spotify)", inline=False)
    embed.add_field(name="!pause", value="Jeda", inline=False)
    embed.add_field(name="!resume", value="Lanjut    embed.add_field", inline=False)
(name="!skip", value="Skip", inline=False)
    embed.add_field(name="!stop", inline=False)
", value="Stop    embed.add_field(name="!np value="Lagu", sekarang", inline=False)
    embed.add_field(name="!queue", value="Queue", inline=False)
    embed.add_field(name="!volume <0-100>", value="Volume", inline=False)
    embed.add_field(name="!shuffle", value="Acak queue", inline=False)
    embed.add_field(name="!join", value="Bot masuk voice", inline=False)
    embed.add_field(name="!leave", value="Bot keluar", inline=False)
    embed.add_field(name="!ping", value="Ping", inline=False)
    embed.set_footer(text="🎵 Spotify + YouTube Music Bot")
    await ctx.send(embed=embed)

# ============================================
# RUN BOT
# ============================================

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ ERROR: DISCORD_TOKEN tidak ada!")
    else:
        print("🚀 Starting bot...")
        bot.run(DISCORD_TOKEN)
