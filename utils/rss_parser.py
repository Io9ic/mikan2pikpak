import feedparser
import logging
from config import RSS_URL

logger = logging.getLogger(__name__)

def extract_torrent_links():
    """Extract torrent links from RSS feed
    
    Returns:
        list: List of torrent URLs
    """
    try:
        logger.info(f"Parsing RSS feed: {RSS_URL}")
        feed = feedparser.parse(RSS_URL)
        
        if hasattr(feed, 'bozo_exception'):
            logger.warning(f"RSS feed parsing warning: {feed.bozo_exception}")
        
        torrent_links = []
        for entry in feed.entries:
            if hasattr(entry, 'links'):
                for link in entry.links:
                    if link.get('href', '').endswith('.torrent'):
                        torrent_links.append(link['href'])
        
        logger.info(f"Found {len(torrent_links)} torrent links in RSS feed")
        return torrent_links
        
    except Exception as e:
        logger.exception(f"Error parsing RSS feed: {e}")
        return []