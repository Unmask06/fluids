"""Weather station lookup using meteostat.

Uses meteostat's built-in station database for global weather station access.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

try:
    import meteostat as ms
    _METEOSTAT_AVAILABLE = True
except ImportError:
    ms = None  # type: ignore[assignment]
    _METEOSTAT_AVAILABLE = False

__all__ = [
    "get_closest_station",
    "get_stations_nearby",
    "get_station_by_id",
    "get_all_stations",
]

_METEOSTAT_MISSING_MSG = """meteostat is required for this functionality.
Install with: pip install meteostat"""


def _check_meteostat() -> None:
    if not _METEOSTAT_AVAILABLE:
        raise ImportError(_METEOSTAT_MISSING_MSG)


def get_closest_station(
    latitude: float,
    longitude: float,
    min_date: datetime | str | None = None,
) -> pd.DataFrame:
    """Find the nearest weather station to a location.
    
    Parameters
    ----------
    latitude : float
        Latitude in degrees.
    longitude : float
        Longitude in degrees.
    min_date : datetime or str, optional
        If specified, prefer stations with data after this date.
    
    Returns
    -------
    pd.Series
        Station metadata with fields: name, country, region, latitude,
        longitude, elevation, timezone, distance. Index is station ID.
    
    Examples
    --------
    >>> station = get_closest_station(29.76, -95.37)  # Houston
    >>> station.name
    'John Dunn Helistop'
    >>> station.name  # Access the station ID
    """
    _check_meteostat()
    
    point = ms.Point(latitude, longitude)
    df = ms.stations.nearby(point,limit=1)
    
    if df.empty:
        raise ValueError(f"No station found near ({latitude}, {longitude})")
    
    # Return first (nearest) station as Series
    return df


def get_stations_nearby(
    latitude: float,
    longitude: float,
    limit: int = 10,
    max_distance_km: float | None = None,
) -> pd.DataFrame:
    """Find multiple weather stations near a location.
    
    Parameters
    ----------
    latitude : float
        Latitude in degrees.
    longitude : float
        Longitude in degrees.
    limit : int, optional
        Maximum stations to return. Default 10.
    max_distance_km : float, optional
        Maximum distance in kilometers.
    
    Returns
    -------
    pd.DataFrame
        DataFrame of nearby stations sorted by distance.
    
    Examples
    --------
    >>> stations = get_stations_nearby(40.71, -74.01, limit=5)  # NYC
    >>> stations[['name', 'distance']]
    """
    _check_meteostat()
    
    point = ms.Point(latitude, longitude)
    df = ms.stations.nearby(point)
    
    # TODO: Is it required ?
    if max_distance_km is not None:
        df = df[df['distance'] <= max_distance_km * 1000]
    
    return df


def get_station_by_id(station_id: str) -> pd.Series:
    """Get station metadata by ID.
    
    Parameters
    ----------
    station_id : str
        Meteostat station ID (WMO format).
    
    Returns
    -------
    pd.Series
        Station metadata.
    
    Examples
    --------
    >>> station = get_station_by_id("72243")  # Houston Intercontinental
    >>> station.name
    """
    _check_meteostat()
    
    df = ms.stations.meta()
    
    if station_id not in df.index:
        raise ValueError(f"Station '{station_id}' not found")
    
    return df.loc[station_id]


def get_all_stations(
    country: str | None = None,
    region: str | None = None,
) -> pd.DataFrame:
    """Get all stations, optionally filtered by location.
    
    Parameters
    ----------
    country : str, optional
        ISO 3166-1 alpha-2 country code (e.g., 'US', 'CA').
    region : str, optional
        ISO 3166-2 region code (e.g., 'TX', 'ON').
    
    Returns
    -------
    pd.DataFrame
        All matching stations.
    
    Examples
    --------
    >>> texas = get_all_stations(country='US', region='TX')
    >>> len(texas)
    """
    _check_meteostat()
    
    df = ms.stations.meta()
    
    if country is not None:
        df = df[df['country'] == country]
    if region is not None:
        df = df[df['region'] == region]
    
    return df
