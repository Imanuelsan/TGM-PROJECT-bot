"""
🎵 Discord Music Bot dengan Spotify
Deploy di Railway
"""

import discord
from discord.ext import commands
from discord.player import Player, SpotifyProvider
import os

# ============================================
# CONFIGURATION
# ============================================

# Get environment variables
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')

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

# Initialize Player
player = Player(bot)

# Setup Spotify Provider
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    player.add_provider(
        SpotifyProvider,
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
    print("✅ Spotify Provider loaded!")
else:
    print("⚠️ Spotify credentials not found!")

# ============================================
# EVENTS
# ============================================

@bot.event
async def on_ready():
    """Dipanggil saat bot siap"""
    print(f'╔══════════════════════════════════════╗')
    print(f'║   🎵 Bot {bot.user.name} is online!       ║')
    print(f'║   Guilds: {len
