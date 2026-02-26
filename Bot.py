import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

TOKEN = os.getenv("TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Spotify
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

# YTDL
ytdl_format_options = {
    'format': 'bestaudio/best',
    'quiet': True,
    'noplaylist': True
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

# ================= MUSIC SYSTEM =================

class MusicPlayer:
    def __init__(self):
        self.queue = []
        self.is_playing = False
        self.vc = None

    async def play_next(self, ctx):
        if len(self.queue) > 0:
            self.is_playing = True
            url, title = self.queue.pop(0)

            source = await discord.FFmpegOpusAudio.from_probe(url, **ffmpeg_options)
            self.vc.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), bot.loop))

            await ctx.send(f"🎶 Now Playing: **{title}**")
        else:
            self.is_playing = False
            await asyncio.sleep(60)
            if not self.is_playing and self.vc:
                await self.vc.disconnect()

music = MusicPlayer()

async def get_song(query):
    if "spotify.com" in query:
        track = sp.track(query)
        query = f"{track['name']} {track['artists'][0]['name']}"

    info = ytdl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
    return info['url'], info['title']

@bot.command()
async def play(ctx, *, query):
    if not ctx.author.voice:
        return await ctx.send("Masuk voice channel dulu!")

    channel = ctx.author.voice.channel

    if music.vc is None or not music.vc.is_connected():
        music.vc = await channel.connect()

    url, title = await get_song(query)
    music.queue.append((url, title))

    await ctx.send(f"➕ Ditambahkan ke queue: **{title}**")

    if not music.is_playing:
        await music.play_next(ctx)

@bot.command()
async def skip(ctx):
    if music.vc and music.vc.is_playing():
        music.vc.stop()
        await ctx.send("⏭️ Lagu diskip")

@bot.command()
async def pause(ctx):
    if music.vc and music.vc.is_playing():
        music.vc.pause()
        await ctx.send("⏸️ Dipause")

@bot.command()
async def resume(ctx):
    if music.vc and music.vc.is_paused():
        music.vc.resume()
        await ctx.send("▶️ Dilanjutkan")

@bot.command()
async def queue(ctx):
    if len(music.queue) == 0:
        return await ctx.send("Queue kosong.")

    msg = ""
    for i, song in enumerate(music.queue):
        msg += f"{i+1}. {song[1]}\n"

    await ctx.send(f"📜 Queue:\n{msg}")

@bot.command()
async def stop(ctx):
    music.queue.clear()
    if music.vc:
        await music.vc.disconnect()
    await ctx.send("⏹️ Music dihentikan")

# ================= ERROR HANDLER =================

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"⚠️ Error: {str(error)}")

@bot.event
async def on_ready():
    print(f"Bot online sebagai {bot.user}")

bot.run(TOKEN)
