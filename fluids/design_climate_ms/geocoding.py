"""Geocoding using geopy with SQLite caching.

Provides address-to-coordinates conversion with on-disk caching.
"""

from __future__ import annotations

import os
import sqlite3

try:
    from appdirs import user_config_dir
    _data_dir = user_config_dir("fluids")
except ImportError:
    _data_dir = ""

try:
    import geopy
    from geopy.geocoders import Nominatim
    _GEOPY_AVAILABLE = True
except ImportError:
    geopy = None  # type: ignore[assignment]
    Nominatim = None  # type: ignore[assignment, misc]
    _GEOPY_AVAILABLE = False

__all__ = [
    "geocode",
    "geopy_geolocator",
    "geopy_cache",
    "SimpleGeolocatorCache",
]

# Module-level singletons
_geolocator = None
_geopy_cache: SimpleGeolocatorCache | None = None

# Configuration
GEOLOCATOR_USER_AGENT = "fluids"
GEOLOCATOR_CACHE_FILENAME = "simple_geolocator_cache.sqlite3"
GEOLOCATOR_CACHE_PATH = os.path.join(_data_dir, GEOLOCATOR_CACHE_FILENAME)

_GEOPY_MISSING_MSG = """geopy is required for geocoding.
Install with: pip install geopy"""


class SimpleGeolocatorCache:
    """SQLite-based address-to-coordinates cache.
    
    Parameters
    ----------
    file_path : str
        Path to SQLite database file.
    
    Examples
    --------
    >>> cache = SimpleGeolocatorCache("cache.sqlite3")
    >>> cache.cache_address("Houston, TX", 29.76, -95.37)
    >>> cache.cached_address("Houston, TX")
    (29.76, -95.37)
    """
    
    def __init__(self, file_path: str) -> None:
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        
        self.file_path = file_path
        self.connection = sqlite3.connect(file_path)
        self._init_schema()
    
    def _init_schema(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS geopy (
                address TEXT PRIMARY KEY,
                latitude REAL,
                longitude REAL
            )
        """)
        self.connection.commit()
    
    def cached_address(self, address: str) -> tuple[float, float] | None:
        """Get cached coordinates for an address."""
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT latitude, longitude FROM geopy WHERE address = ?",
            (address,)
        )
        return cursor.fetchone()
    
    def cache_address(self, address: str, latitude: float, longitude: float) -> None:
        """Store coordinates for an address."""
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO geopy (address, latitude, longitude) VALUES (?, ?, ?)",
            (address, latitude, longitude)
        )
        self.connection.commit()
    
    def clear(self) -> None:
        """Clear all cached entries."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM geopy")
        self.connection.commit()
    
    def __len__(self) -> int:
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM geopy")
        return cursor.fetchone()[0]
    
    def close(self) -> None:
        self.connection.close()
    
    def __enter__(self) -> SimpleGeolocatorCache:
        return self
    
    def __exit__(self, *args) -> None:
        self.close()


def geopy_geolocator():
    """Get or create singleton Nominatim geocoder."""
    global _geolocator
    
    if not _GEOPY_AVAILABLE:
        return None
    
    if _geolocator is None:
        _geolocator = Nominatim(user_agent=GEOLOCATOR_USER_AGENT)
    
    return _geolocator


def geopy_cache() -> SimpleGeolocatorCache:
    """Get or create singleton geocoding cache."""
    global _geopy_cache
    
    if _geopy_cache is None:
        _geopy_cache = SimpleGeolocatorCache(GEOLOCATOR_CACHE_PATH)
    
    return _geopy_cache


def geocode(address: str) -> tuple[float, float]:
    """Convert address to (latitude, longitude).
    
    Uses geopy Nominatim with SQLite caching.
    
    Parameters
    ----------
    address : str
        Location string (city, address, etc.).
    
    Returns
    -------
    tuple[float, float]
        (latitude, longitude) in degrees.
    
    Raises
    ------
    ImportError
        If geopy not installed.
    ValueError
        If address cannot be geocoded.
    
    Examples
    --------
    >>> geocode("Houston, TX")
    (29.7589382, -95.3676974)
    
    >>> geocode("Fredericton, NB")
    (45.966425, -66.645813)
    """
    if not _GEOPY_AVAILABLE:
        raise ImportError(_GEOPY_MISSING_MSG)
    
    # Try cache first
    try:
        cache = geopy_cache()
        result = cache.cached_address(address)
        if result is not None:
            return result
    except Exception:
        cache = None
    
    # Online lookup
    geocoder = geopy_geolocator()
    if geocoder is None:
        raise ImportError(_GEOPY_MISSING_MSG)
    
    location = geocoder.geocode(address)
    if location is None:
        raise ValueError(f"Could not geocode: {address}")
    
    result = (location.latitude, location.longitude)
    
    # Cache result
    try:
        if cache is not None:
            cache.cache_address(address, location.latitude, location.longitude)
    except Exception:
        pass
    
    return result
