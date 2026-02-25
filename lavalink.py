"""
Lavalink Server for Railway
"""

import asyncio
import logging
import os
from lavalink import Lavalink

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PASSWORD = os.environ.get('LAVALINK_PASSWORD', 'youshallnotpass')
PORT = int(os.environ.get('PORT', 2333))

# Initialize Lavalink
lavalink = Lavalink(
    host='0.0.0.0',
    port=PORT,
    password=PASSWORD,
    resume_key='lavalink_resume_key',
    resume_timeout=60,
    log_level='INFO'
)

# Event handlers
@lavalink.listen()
async def on_track_start(event):
    logger.info(f"Track started: {event.track.title}")

@lavalink.listen()
async def on_track_end(event):
    logger.info(f"Track ended: {event.track.title}")

@lavalink.listen()
async def on_track_exception(event):
    logger.error(f"Track exception: {event.exception}")

# Run Lavalink
async def main():
    logger.info(f"Starting Lavalink on port {PORT} with password {PASSWORD}")
    await lavalink.start()

if __name__ == "__main__":
    asyncio.run(main())
