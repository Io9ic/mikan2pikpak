import asyncio
import logging
import os
import time
import schedule
from datetime import datetime

from utils.rss_parser import extract_torrent_links
from utils.torrent_handler import download_torrents, torrents_to_magnets, cleanup_torrents
from utils.pikpak_client import pikpak_offline_download
from utils.storage import MagnetTracker
from config import TORRENT_DIR, CHECK_INTERVAL_HOURS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        "logs", 
                                        f"{datetime.now().strftime('%Y-%m-%d')}.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Make sure directories exist
os.makedirs(TORRENT_DIR, exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"), exist_ok=True)

async def process_rss():
    """Main workflow to process RSS feed and handle downloads"""
    try:
        logger.info("Starting RSS processing job")
        
        # Initialize magnet tracker
        magnet_tracker = MagnetTracker()
        
        # 1. Extract torrent links from RSS
        torrent_links = extract_torrent_links()
        
        if not torrent_links:
            logger.info("No torrent links found in RSS feed")
            return
        
        # 2. Download torrent files
        downloaded_torrents = await download_torrents(torrent_links)
        
        if not downloaded_torrents:
            logger.info("No torrents were successfully downloaded")
            return
        
        # 3. Convert torrents to magnet links and filter out already processed ones
        magnet_links = torrents_to_magnets(downloaded_torrents)
        new_magnets = magnet_tracker.filter_new_magnets(magnet_links)
        
        if not new_magnets:
            logger.info("No new magnet links to process")
            # Clean up torrents since we don't need them anymore
            await cleanup_torrents([t[1] for t in downloaded_torrents])
            return
        
        logger.info(f"Found {len(new_magnets)} new magnet links to process")
        
        # 4. Add magnet links to PikPak
        success = await pikpak_offline_download(new_magnets)
        
        if success:
            # 5. Mark these magnets as processed
            magnet_tracker.add_magnets(new_magnets)
            
            # 6. Clean up torrent files
            await cleanup_torrents([t[1] for t in downloaded_torrents])
            
            logger.info(f"Successfully processed {len(new_magnets)} magnet links")
        else:
            logger.error("Failed to process magnet links with PikPak")
    
    except Exception as e:
        logger.exception(f"Error in process_rss job: {e}")

def run_async_job():
    """Helper function to run the async job in the scheduler"""
    asyncio.run(process_rss())

def main():
    """Main entry point with scheduling"""
    logger.info("Starting PikPak RSS Downloader")
    
    # Run once at startup
    run_async_job()
    
    # Schedule to run every hour
    schedule.every(CHECK_INTERVAL_HOURS).hours.do(run_async_job)
    
    logger.info(f"Scheduled to run every {CHECK_INTERVAL_HOURS} hour(s)")
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute if there's a job to run

if __name__ == "__main__":
    main()