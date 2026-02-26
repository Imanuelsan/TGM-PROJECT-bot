import discord
from discord.ext import commands
import yt_dlp
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ytdl_format_options = {
    'format': 'bestaudio/best',
    'quiet': True,
    'noplaylist': True,
    'default_search': 'ytsearch',
    'http_headers': {
        'User-Agent': 'Mozilla/5.0'
    },
    'extractor_args': {
        'youtube': {
            'player_client': ['web']
        }
    }
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


@bot.command()
async def play(ctx, *, url):
    if not ctx.author.voice:
        await ctx.send("Kamu harus masuk voice channel dulu.")
        return

    channel = ctx.author.voice.channel
    if not ctx.voice_client:
        await channel.connect()

    loop = asyncio.get_event_loop()

    try:
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=False)
        )

        if 'entries' in data:
            data = data['entries'][0]

        url2 = data['url']
        source = await discord.FFmpegOpusAudio.from_probe(
            url2, **ffmpeg_options
        )

        ctx.voice_client.play(source)
        await ctx.send(f"🎵 Memutar: {data['title']}")

    except Exception as e:
        await ctx.send("❌ Gagal memutar lagu.")
        print(e)


bot.run("TOKEN_KAMU")
