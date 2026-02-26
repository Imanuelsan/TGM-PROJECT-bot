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

# =========================
# YTDLP CONFIG (STABIL)
# =========================
ydl_opts = {
    "format": "bestaudio/best",
    "quiet": True,
    "noplaylist": True,
    "extractor_args": {
        "youtube": {
            "player_client": ["android"]
        }
    }
}

ffmpeg_options = {
    "options": "-vn -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
}


# =========================
# READY EVENT
# =========================
@bot.event
async def on_ready():
    print(f"{bot.user} sudah online 🚀")


# =========================
# PLAY COMMAND
# =========================
@bot.command()
async def play(ctx, url: str):

    if not ctx.author.voice:
        await ctx.send("Masuk voice channel dulu!")
        return

    channel = ctx.author.voice.channel

    if not ctx.voice_client:
        await channel.connect()

    await ctx.send("🔎 Mengambil data lagu...")

    try:
        loop = asyncio.get_event_loop()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(
                None,
                lambda: ydl.extract_info(url, download=False)
            )

            audio_url = info["url"]
            title = info.get("title", "Unknown Title")

        source = await discord.FFmpegOpusAudio.from_probe(
            audio_url,
            **ffmpeg_options
        )

        ctx.voice_client.stop()
        ctx.voice_client.play(source)

        await ctx.send(f"🎵 Sekarang memutar: **{title}**")

    except Exception as e:
        print(e)
        await ctx.send("❌ Gagal memutar lagu.")


# =========================
# STOP COMMAND
# =========================
@bot.command()
async def stop(ctx):

    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("⏹️ Musik dihentikan.")
    else:
        await ctx.send("Bot tidak ada di voice channel.")


# =========================
# RUN BOT
# =========================
bot.run(TOKEN)
