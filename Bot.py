import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

TOKEN = os.environ.get("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= YTDLP CONFIG =================
ydl_opts = {
    "format": "bestaudio[ext=m4a]/bestaudio/best",
    "quiet": True,
    "noplaylist": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
    "extractor_args": {
        "youtube": {
            "player_client": ["android", "web"]
        }
    }
}

ffmpeg_options = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

# ================= MUSIC SYSTEM =================
class MusicPlayer:
    def __init__(self):
        self.queue = []
        self.is_playing = False

music = MusicPlayer()

# ================= READY =================
@bot.event
async def on_ready():
    print(f"{bot.user} ONLINE 🚀")

# ================= PLAY =================
@bot.command()
async def play(ctx, *, query):

    if not ctx.author.voice:
        await ctx.send("Masuk voice channel dulu!")
        return

    channel = ctx.author.voice.channel

    if not ctx.voice_client:
        await channel.connect()

    await ctx.send("🔎 Mencari lagu...")

    loop = asyncio.get_event_loop()

    def extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(query, download=False)

    try:
        info = await loop.run_in_executor(None, extract)

        if "entries" in info:
            info = info["entries"][0]

        url = info["url"]
        title = info.get("title", "Unknown")

        music.queue.append((url, title))
        await ctx.send(f"➕ Ditambahkan ke queue: **{title}**")

        if not music.is_playing:
            await play_next(ctx)

    except Exception as e:
        print("ERROR:", e)
        await ctx.send("❌ Gagal memutar lagu.")

# ================= PLAY NEXT =================
async def play_next(ctx):
    if len(music.queue) > 0:
        music.is_playing = True

        url, title = music.queue.pop(0)

        source = discord.FFmpegPCMAudio(url, **ffmpeg_options)

        vc = ctx.voice_client
        vc.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))

        await ctx.send(f"🎵 Now Playing: **{title}**")
    else:
        music.is_playing = False
        await asyncio.sleep(60)
        if not music.is_playing and ctx.voice_client:
            await ctx.voice_client.disconnect()

# ================= SKIP =================
@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Lagu dilewati.")
    else:
        await ctx.send("Tidak ada lagu yang diputar.")

# ================= PAUSE =================
@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Musik dipause.")

# ================= RESUME =================
@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Musik dilanjutkan.")

# ================= STOP =================
@bot.command()
async def stop(ctx):
    music.queue.clear()
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("⏹️ Musik dihentikan & queue dibersihkan.")

bot.run(TOKEN)
