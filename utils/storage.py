import sqlite3
import logging
import re  # Moved to top
from config import DB_PATH

logger = logging.getLogger(__name__)

class MagnetTracker:
    """Track processed magnet links to avoid duplicates"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()
    def _init_db(self):
        """Initialize the SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_magnets (
                    hash TEXT PRIMARY KEY,
                    magnet TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info(f"Initialized magnet tracker database at {self.db_path}")
            
        except Exception as e:
            logger.exception(f"Failed to initialize database: {e}")
    
    import re  # Add import if not already present
    
    def _extract_hash(self, magnet):
        """Extract the hash from a magnet link using regex"""
        try:
            # Pattern for urn:btih:HASH
            match = re.search(r'urn:btih:([a-fA-F0-9]+)', magnet)
            if match:
                return match.group(1)  # Return the hash
            return None
        except Exception as e:
            logger.error(f"Error extracting hash: {e}")
            return None
    
    def is_processed(self, magnet):
        """Check if a magnet link has been processed"""
        hash_value = self._extract_hash(magnet)
        if not hash_value:
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM processed_magnets WHERE hash = ?", (hash_value,))
            result = cursor.fetchone() is not None
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error checking if magnet is processed: {e}")
            return False
    
    def add_magnet(self, magnet):
        """Add a magnet link to the processed list"""
        hash_value = self._extract_hash(magnet)
        if not hash_value:
            logger.warning(f"Could not extract hash from magnet: {magnet[:60]}...")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO processed_magnets (hash, magnet) VALUES (?, ?)",
                (hash_value, magnet)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding magnet to database: {e}")
            return False
    
    def add_magnets(self, magnets):
        """Add multiple magnet links to the processed list"""
        for magnet in magnets:
            self.add_magnet(magnet)
    
    def filter_new_magnets(self, magnets):
        """Filter out already processed magnets"""
        return [magnet for magnet in magnets if not self.is_processed(magnet)]
