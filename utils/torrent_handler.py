import os
import asyncio
import hashlib
import logging
import httpx
import bencodepy
from urllib.parse import quote

from config import HTTP_PROXY, TORRENT_DIR

logger = logging.getLogger(__name__)

async def download_torrent_file(url, save_path):
    """Download a torrent file"""
    try:
        async with httpx.AsyncClient(proxy=HTTP_PROXY) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded torrent file: {url} -> {save_path}")
            return True
    except Exception as e:
        logger.exception(f"Failed to download torrent file {url}: {e}")
        return False

async def download_torrents(torrent_links):
    """Download multiple torrent files"""
    download_tasks = []
    result_paths = []
    
    for index, url in enumerate(torrent_links):
        filename = f"torrent_{index}_{int(asyncio.get_event_loop().time() * 1000)}.torrent"
        save_path = os.path.join(TORRENT_DIR, filename)
        download_tasks.append(download_torrent_file(url, save_path))
        result_paths.append((url, save_path))
    
    # Wait for all downloads to complete
    results = await asyncio.gather(*download_tasks)
    
    # Filter out failed downloads
    successful_downloads = []
    for i, success in enumerate(results):
        if success:
            successful_downloads.append(result_paths[i])
    
    logger.info(f"Successfully downloaded {len(successful_downloads)} of {len(torrent_links)} torrent files")
    return successful_downloads

def torrent_to_magnet(torrent_path):
    """Convert a torrent file to a magnet link"""
    try:
        if not os.path.exists(torrent_path):
            logger.error(f"Torrent file does not exist: {torrent_path}")
            return None
        
        with open(torrent_path, 'rb') as f:
            torrent_data = f.read()
        
        decoded_data = bencodepy.decode(torrent_data)
        info = decoded_data.get(b'info', {})
        
        if not info:
            logger.error(f"No info dict in torrent file: {torrent_path}")
            return None
        
        # Calculate info hash
        info_bencoded = bencodepy.encode(info)
        info_hash = hashlib.sha1(info_bencoded).hexdigest()
        
        # Get name
        name = info.get(b'name', b'unknown').decode('utf-8', errors='ignore')
        
        # Build magnet link
        magnet = f"magnet:?xt=urn:btih:{info_hash}"
        magnet += f"&dn={quote(name)}"
        
        # Add trackers
        if b'announce' in decoded_data:
            tracker = decoded_data[b'announce'].decode('utf-8', errors='ignore')
            magnet += f"&tr={quote(tracker)}"
        
        if b'announce-list' in decoded_data:
            for tracker_list in decoded_data[b'announce-list']:
                for tracker in tracker_list:
                    tracker_str = tracker.decode('utf-8', errors='ignore')
                    magnet += f"&tr={quote(tracker_str)}"
        
        logger.info(f"Generated magnet link for {os.path.basename(torrent_path)}")
        return magnet
    
    except Exception as e:
        logger.exception(f"Error generating magnet link for {torrent_path}: {e}")
        return None

def torrents_to_magnets(downloaded_torrents):
    """Convert multiple torrent files to magnet links"""
    magnet_links = []
    
    for url, torrent_path in downloaded_torrents:
        magnet = torrent_to_magnet(torrent_path)
        if magnet:
            magnet_links.append(magnet)
    
    logger.info(f"Generated {len(magnet_links)} magnet links from {len(downloaded_torrents)} torrents")
    return magnet_links

async def cleanup_torrents(torrent_paths):
    """Remove torrent files after processing"""
    for path in torrent_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"Removed torrent file: {path}")
        except Exception as e:
            logger.error(f"Failed to remove torrent file {path}: {e}")