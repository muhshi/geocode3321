import json
import os
import threading

class CacheService:
    """Thread-safe JSON file cache for geocoding results."""
    
    def __init__(self, cache_file):
        self.cache_file = cache_file
        self.data = {}
        self.lock = threading.Lock()
        self._dirty_count = 0
        self.load()
    
    def load(self):
        """Load cache from JSON file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                print(f"Cache loaded: {len(self.data)} entries from {self.cache_file}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Cache file corrupted, starting fresh. ({e})")
                self.data = {}
        else:
            print("No cache file found. Starting fresh.")
            self.data = {}
    
    def save(self):
        """Save cache to JSON file."""
        with self.lock:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            try:
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
                self._dirty_count = 0
            except IOError as e:
                print(f"Error saving cache: {e}")
    
    def get(self, key):
        """Get cached result by key. Returns None if not found."""
        with self.lock:
            return self.data.get(str(key))
    
    def set(self, key, value, auto_save_interval=50):
        """Set a cache entry. Auto-saves every `auto_save_interval` entries."""
        with self.lock:
            self.data[str(key)] = value
            self._dirty_count += 1
        
        if self._dirty_count >= auto_save_interval:
            self.save()
    
    def has(self, key):
        """Check if key exists in cache."""
        with self.lock:
            return str(key) in self.data
    
    def __len__(self):
        return len(self.data)
    
    def __contains__(self, key):
        return self.has(key)
