import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
import os

# ================= CONFIG =================
TOKEN = os.environ.get("TOKEN")
BOT_NAME = "TEMAN GEO MIYANA"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ================= YTDL =================
ytdl_format_options = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "auto"
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

# ================= MUSIC PLAYER =================
class MusicPlayer:
    def __init__(self):
        self.queue = []
        self.current = None
        self.loop = False

players = {}

def get_player(guild_id):
    if guild_id not in players:
        players[guild_id] = MusicPlayer()
    return players[guild_id]

async def play_song(interaction, url):
    player = get_player(interaction.guild.id)

    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

    if "entries" in data:
        data = data["entries"][0]

    url_audio = data["url"]
    title = data["title"]

    source = discord.FFmpegPCMAudio(url_audio)
    source = discord.PCMVolumeTransformer(source)
    source.volume = 0.5

    interaction.guild.voice_client.play(source)

    embed = discord.Embed(
        title="🎵 Sedang Diputar",
        description=title,
        color=discord.Color.blue()
    )
    await interaction.followup.send(embed=embed)

# ================= EVENTS =================
@bot.event
async def on_ready():
    await tree.sync()
    print(f"🤖 {BOT_NAME} sudah online!")

# ================= COMMANDS =================
@tree.command(name="join", description="Bergabung ke voice channel")
async def join(interaction: discord.Interaction):
    if interaction.user.voice is None:
        await interaction.response.send_message("❌ Masuk voice channel dulu!", ephemeral=True)
        return

    await interaction.user.voice.channel.connect()
    await interaction.response.send_message("✅ Bergabung ke voice channel!")

@tree.command(name="play", description="Mainkan musik dari YouTube")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()

    if interaction.guild.voice_client is None:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
        else:
            await interaction.followup.send("❌ Masuk voice channel dulu!")
            return

    await play_song(interaction, query)

@tree.command(name="stop", description="Hentikan dan keluar")
async def stop(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("⏹️ Dihentikan!")

@tree.command(name="help", description="Lihat semua command")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title=f"📖 Help - {BOT_NAME}",
        description="Daftar command:",
        color=discord.Color.orange()
    )
    embed.add_field(name="/join", value="Gabung voice", inline=False)
    embed.add_field(name="/play", value="Play musik", inline=False)
    embed.add_field(name="/stop", value="Stop & keluar", inline=False)

    await interaction.response.send_message(embed=embed)

# ================= RUN =================
if __name__ == "__main__":
    bot.run(TOKEN)
