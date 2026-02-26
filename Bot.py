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

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

ytdl = yt_dlp.YoutubeDL({
    'format': 'bestaudio/best',
    'quiet': True,
    'noplaylist': True
})

ffmpeg_options = {'options': '-vn'}

# ================= MULTI SERVER MUSIC =================

class GuildMusic:
    def __init__(self):
        self.queue = []
        self.vc = None
        self.is_playing = False
        self.loop = False
        self.vote_skip = set()

music_players = {}

def get_player(guild_id):
    if guild_id not in music_players:
        music_players[guild_id] = GuildMusic()
    return music_players[guild_id]

async def get_song(query):
    if "spotify.com" in query:
        track = sp.track(query)
        query = f"{track['name']} {track['artists'][0]['name']}"

    info = ytdl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
    return info['url'], info['title']

async def play_next(ctx):
    player = get_player(ctx.guild.id)

    if len(player.queue) > 0:
        player.is_playing = True
        url, title = player.queue.pop(0)

        source = await discord.FFmpegOpusAudio.from_probe(url, **ffmpeg_options)

        def after_play(error):
            fut = asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
            try:
                fut.result()
            except:
                pass

        player.vc.play(source, after=after_play)

        embed = discord.Embed(
            title="🎶 Now Playing",
            description=title,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    else:
        player.is_playing = False
        await asyncio.sleep(120)
        if not player.is_playing and player.vc:
            await player.vc.disconnect()

# ================= MUSIC COMMAND =================

@bot.command()
async def play(ctx, *, query):
    if not ctx.author.voice:
        return await ctx.send("Masuk voice channel dulu!")

    player = get_player(ctx.guild.id)

    if not player.vc or not player.vc.is_connected():
        player.vc = await ctx.author.voice.channel.connect()

    url, title = await get_song(query)
    player.queue.append((url, title))

    await ctx.send(f"➕ Ditambahkan: **{title}**")

    if not player.is_playing:
        await play_next(ctx)

@bot.command()
async def skip(ctx):
    player = get_player(ctx.guild.id)

    if not player.vc or not player.vc.is_playing():
        return await ctx.send("Tidak ada lagu.")

    voice_channel = ctx.author.voice.channel
    required_votes = max(1, len(voice_channel.members) // 2)

    player.vote_skip.add(ctx.author.id)

    if len(player.vote_skip) >= required_votes:
        player.vote_skip.clear()
        player.vc.stop()
        await ctx.send("⏭️ Lagu diskip (Vote berhasil)")
    else:
        await ctx.send(f"Vote skip: {len(player.vote_skip)}/{required_votes}")

@bot.command()
async def stop(ctx):
    player = get_player(ctx.guild.id)
    player.queue.clear()
    if player.vc:
        await player.vc.disconnect()
    await ctx.send("⏹️ Music dihentikan")

@bot.command()
async def loop(ctx):
    player = get_player(ctx.guild.id)
    player.loop = not player.loop
    await ctx.send(f"Loop: {player.loop}")

@bot.command()
async def mode247(ctx):
    player = get_player(ctx.guild.id)
    if ctx.voice_client:
        await ctx.send("24/7 mode aktif.")
    else:
        await ctx.author.voice.channel.connect()
        await ctx.send("Bot masuk & 24/7 aktif.")

# ================= TICKET CLOSE BUTTON =================

class CloseTicket(discord.ui.View):
    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

@bot.command()
async def ticket(ctx):
    guild = ctx.guild
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True)
    }

    channel = await guild.create_text_channel(
        f"ticket-{ctx.author.name}",
        overwrites=overwrites
    )

    await channel.send("Support akan membantu kamu.", view=CloseTicket())
    await ctx.send("Ticket dibuat.")

# ================= READY =================

@bot.event
async def on_ready():
    print(f"Bot online sebagai {bot.user}")

bot.run(TOKEN)
