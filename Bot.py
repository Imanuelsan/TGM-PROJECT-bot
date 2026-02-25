import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
import os

# Konfigurasi - dari environment variable
TOKEN = os.environ.get("TOKEN")
BOT_NAME = "TEMAN GEO MIYANA"

# Setup intents
intents = discord.Intents.default()
intents.message_content = True

# Setup bot
bot = commands.Bot(command_prefix="!", intents=intents)
tree = app_commands.CommandTree(bot)

# Setup yt-dlp
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

# Kelas untuk menangani musik
class MusicPlayer:
    def __init__(self):
        self.queue = []
        self.current = None
        self.voice_client = None
        self.loop = False

players = {}

def get_player(guild_id):
    if guild_id not in players:
        players[guild_id] = MusicPlayer()
    return players[guild_id]

async def play_next(ctx):
    player = get_player(ctx.guild.id)
    
    if player.loop and player.current:
        source = player.current
        ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        return
    
    if len(player.queue) > 0:
        url = player.queue.pop(0)
        await play_song(ctx, url)
    else:
        player.current = None

async def play_song(ctx, url):
    player = get_player(ctx.guild.id)
    
    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        
        if 'entries' in data:
            data = data['entries'][0]
        
        title = data['title']
        thumbnail = data.get('thumbnail', '')
        url_audio = data['url']
        
        source = discord.FFmpegPCMAudio(url_audio, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
        source = discord.PCMVolumeTransformer(source)
        source.volume = 0.5
        
        player.current = source
        
        embed = discord.Embed(
            title="🎵 Sedang Diputar",
            description=f"**{title}**",
            color=discord.Color.blue()
        )
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=f"Bot: {BOT_NAME}")
        
        await ctx.send(embed=embed)
        
        ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.event
async def on_ready():
    await tree.sync()
    print(f"🤖 {BOT_NAME} sudah online!")
    print(f"Bot ID: {bot.user.id}")

@tree.command(name="join", description="Bergabung ke voice channel")
async def join(ctx):
    if ctx.user.voice is None:
        await ctx.send("❌ Kamu harus berada di voice channel dulu!")
        return
    
    channel = ctx.user.voice.channel
    await channel.connect()
    await ctx.send(f"✅ {BOT_NAME} bergabung ke {channel.name}!")

@tree.command(name="play", description="Mainkan musik dari YouTube")
async def play(ctx, *, query: str):
    if ctx.voice_client is None:
        if ctx.user.voice:
            await ctx.user.voice.channel.connect()
        else:
            await ctx.send("❌ Kamu harus di voice channel dulu!")
            return
    
    await ctx.send(f"🔍 Mencari: {query}...")
    
    player = get_player(ctx.guild.id)
    
    if ctx.voice_client.is_playing():
        player.queue.append(query)
        await ctx.send(f"📝 Ditambahkan ke queue! (Position: {len(player.queue)})")
        return
    
    await play_song(ctx, query)

@tree.command(name="pause", description="Jeda musik")
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Musik dijeda!")
    else:
        await ctx.send("❌ Tidak ada musik yang diputar!")

@tree.command(name="resume", description="Lanjutkan musik")
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Musik dilanjutkan!")
    else:
        await ctx.send("❌ Musik tidak dijeda!")

@tree.command(name="skip", description="Lewati lagu")
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Lagu dilewati!")
    else:
        await ctx.send("❌ Tidak ada musik yang diputar!")

@tree.command(name="stop", description="Hentikan musik dan keluar")
async def stop(ctx):
    player = get_player(ctx.guild.id)
    player.queue.clear()
    player.current = None
    
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    await ctx.send("⏹️ Musik dihentikan!")

@tree.command(name="queue", description="Lihat daftar lagu")
async def queue(ctx):
    player = get_player(ctx.guild.id)
    
    if len(player.queue) == 0:
        await ctx.send("📭 Queue kosong!")
        return
    
    embed = discord.Embed(title="📋 Daftar Lagu", color=discord.Color.green())
    for i, url in enumerate(player.queue, 1):
        embed.add_field(name=f"{i}.", value=url, inline=False)
    
    await ctx.send(embed=embed)

@tree.command(name="loop", description="Ulangi lagu saat ini")
async def loop(ctx, mode: str = "off"):
    player = get_player(ctx.guild.id)
    
    if mode.lower() == "on":
        player.loop = True
        await ctx.send("🔁 Loop diaktifkan!")
    else:
        player.loop = False
        await ctx.send("🔁 Loop dinonaktifkan!")

@tree.command(name="volume", description="Atur volume (0-100)")
async def volume(ctx, vol: int):
    if ctx.voice_client and ctx.voice_client.source:
        ctx.voice_client.source.volume = vol / 100
        await ctx.send(f"🔊 Volume diatur ke {vol}%!")
    else:
        await ctx.send("❌ Tidak ada musik yang diputar!")

@tree.command(name="help", description="Tampilkan semua command")
async def help(ctx):
    embed = discord.Embed(
        title=f"📖 Help - {BOT_NAME}",
        description="Daftar command yang tersedia:",
        color=discord.Color.orange()
    )
    embed.add_field(name="/join", value="Bergabung ke voice channel
