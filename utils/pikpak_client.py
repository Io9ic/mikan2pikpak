import logging
import httpx
from pikpakapi import PikPakApi

from config import PIKPAK_USERNAME, PIKPAK_PASSWORD, HTTP_PROXY

logger = logging.getLogger(__name__)

async def pikpak_offline_download(magnet_links):
    """Add magnet links to PikPak for offline download"""
    try:
        logger.info(f"Connecting to PikPak with username: {PIKPAK_USERNAME}")
        
        client = PikPakApi(
            username=PIKPAK_USERNAME,
            password=PIKPAK_PASSWORD,
            httpx_client_args={
                "proxy": HTTP_PROXY,
                "transport": httpx.AsyncHTTPTransport(retries=3),
            }
        )
        
        # Login and refresh token
        await client.login()
        await client.refresh_access_token()
        
        logger.info("Successfully logged in to PikPak")
        
        # Add each magnet link
        success_count = 0
        for magnet in magnet_links:
            try:
                truncated_magnet = magnet[:60] + "..." if len(magnet) > 60 else magnet
                logger.info(f"Adding to PikPak: {truncated_magnet}")
                
                await client.offline_download(magnet)
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to add magnet to PikPak: {e}")
        
        logger.info(f"Successfully added {success_count} of {len(magnet_links)} magnets to PikPak")
        return success_count > 0
        
    except Exception as e:
        logger.exception(f"Error in PikPak processing: {e}")
        return False