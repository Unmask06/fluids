"""Weather data retrieval using meteostat.

Provides functions to fetch daily, hourly, monthly data and climate normals.
Uses meteostat's built-in SI unit conversion.
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
    "get_daily_data",
    "get_monthly_data", 
    "get_hourly_data",
    "get_climate_normals",
    "month_average_temperature",
    "month_average_windspeed",
    "coldest_month",
    "warmest_month",
]

_METEOSTAT_MISSING_MSG = """meteostat is required for this functionality.
Install with: pip install meteostat"""


def _check_meteostat() -> None:
    if not _METEOSTAT_AVAILABLE:
        raise ImportError(_METEOSTAT_MISSING_MSG)


def get_daily_data(
    station_id: str,
    start: datetime | str,
    end: datetime | str,
    si_units: bool = True,
) -> pd.DataFrame | None:
    """Retrieve daily weather data for a station.
    
    Parameters
    ----------
    station_id : str
        Meteostat station ID.
    start : datetime or str
        Start date (YYYY-MM-DD string or datetime).
    end : datetime or str
        End date (YYYY-MM-DD string or datetime).
    si_units : bool, optional
        If True (default), return SI units (K, m/s, Pa, m).
        If False, return metric units (°C, km/h, hPa, mm).
    
    Returns
    -------
    pd.DataFrame or None
        Daily weather data with columns:
        - temp: Average temperature
        - tmin/tmax: Min/max temperature
        - rhum: Relative humidity (%)
        - prcp: Precipitation
        - snwd: Snow depth
        - wspd/wpgt: Wind speed / peak gust
        - pres: Sea level pressure
        - tsun: Sunshine duration (min)
        - cldc: Cloud cover (oktas)
    
    Examples
    --------
    >>> df = get_daily_data("72243", "2023-01-01", "2023-12-31")
    >>> df['temp'].mean()  # Annual mean temp in Kelvin
    """
    _check_meteostat()
    
    if isinstance(start, str):
        start = datetime.fromisoformat(start)
    if isinstance(end, str):
        end = datetime.fromisoformat(end)
    
    ts = ms.daily(station_id, start, end)
    units = ms.UnitSystem.SI if si_units else ms.UnitSystem.METRIC
    return ts.fetch(units=units)


def get_monthly_data(
    station_id: str,
    start: datetime | str,
    end: datetime | str,
    si_units: bool = True,
) -> pd.DataFrame | None:
    """Retrieve monthly aggregated weather data.
    
    Parameters
    ----------
    station_id : str
        Meteostat station ID.
    start : datetime or str
        Start date.
    end : datetime or str
        End date.
    si_units : bool, optional
        If True (default), return SI units.
    
    Returns
    -------
    pd.DataFrame or None
        Monthly weather data.
    
    Examples
    --------
    >>> df = get_monthly_data("72243", "2020-01-01", "2023-12-31")
    """
    _check_meteostat()
    
    if isinstance(start, str):
        start = datetime.fromisoformat(start)
    if isinstance(end, str):
        end = datetime.fromisoformat(end)
    
    ts = ms.monthly(station_id, start, end)
    units = ms.UnitSystem.SI if si_units else ms.UnitSystem.METRIC
    return ts.fetch(units=units)


def get_hourly_data(
    station_id: str,
    start: datetime | str,
    end: datetime | str,
    si_units: bool = True,
) -> pd.DataFrame | None:
    """Retrieve hourly weather data.
    
    Parameters
    ----------
    station_id : str
        Meteostat station ID.
    start : datetime or str
        Start datetime.
    end : datetime or str
        End datetime.
    si_units : bool, optional
        If True (default), return SI units.
    
    Returns
    -------
    pd.DataFrame or None
        Hourly weather data with additional columns:
        - dwpt: Dew point
        - coco: Weather condition code
    
    Examples
    --------
    >>> df = get_hourly_data("72243", "2023-07-01", "2023-07-31")
    """
    _check_meteostat()
    
    if isinstance(start, str):
        start = datetime.fromisoformat(start)
    if isinstance(end, str):
        end = datetime.fromisoformat(end)
    
    ts = ms.hourly(station_id, start, end)
    units = ms.UnitSystem.SI if si_units else ms.UnitSystem.METRIC
    return ts.fetch(units=units)


def get_climate_normals(
    station_id: str,
    si_units: bool = True,
) -> pd.DataFrame | None:
    """Retrieve 30-year climate normals (1991-2020).
    
    Parameters
    ----------
    station_id : str
        Meteostat station ID.
    si_units : bool, optional
        If True (default), return SI units.
    
    Returns
    -------
    pd.DataFrame or None
        Monthly climate normals (12 rows).
    
    Examples
    --------
    >>> normals = get_climate_normals("72243")
    >>> normals['temp']  # Monthly normal temperatures
    """
    _check_meteostat()
    
    ts = ms.normals(station_id)
    units = ms.UnitSystem.SI if si_units else ms.UnitSystem.METRIC
    return ts.fetch(units=units)


def month_average_temperature(
    station_id: str,
    start_year: int,
    end_year: int,
    min_days: int = 23,
    si_units: bool = True,
) -> list[float | None]:
    """Calculate monthly average temperatures over a year range.
    
    Parameters
    ----------
    station_id : str
        Meteostat station ID.
    start_year : int
        Start year (inclusive).
    end_year : int
        End year (inclusive).
    min_days : int, optional
        Minimum days required for valid monthly average. Default 23.
    si_units : bool, optional
        If True (default), return SI units (Kelvin).
    
    Returns
    -------
    list[float | None]
        12 monthly average temperatures (index 0 = January).
    
    Examples
    --------
    >>> temps = month_average_temperature("72243", 2015, 2020)
    >>> temps[6]  # July average
    """
    _check_meteostat()
    
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    
    df = get_daily_data(station_id, start, end, si_units=si_units)
    
    if df is None or df.empty:
        return [None] * 12
    
    df = df.reset_index()
    df['month'] = df['time'].dt.month
    df['year'] = df['time'].dt.year
    
    # Group by year and month, filter by min_days
    grouped = df.groupby(['year', 'month']).agg(
        temp_mean=('temp', 'mean'),
        count=('temp', 'count')
    ).reset_index()
    
    grouped.loc[grouped['count'] < min_days, 'temp_mean'] = pd.NA
    
    # Average across years for each month
    monthly = grouped.groupby('month')['temp_mean'].mean()
    
    return [monthly.get(m) for m in range(1, 13)]


def month_average_windspeed(
    station_id: str,
    start_year: int,
    end_year: int,
    min_days: int = 23,
    si_units: bool = True,
) -> list[float | None]:
    """Calculate monthly average wind speeds over a year range.
    
    Parameters
    ----------
    station_id : str
        Meteostat station ID.
    start_year : int
        Start year (inclusive).
    end_year : int
        End year (inclusive).
    min_days : int, optional
        Minimum days required for valid monthly average. Default 23.
    si_units : bool, optional
        If True (default), return SI units (m/s).
    
    Returns
    -------
    list[float | None]
        12 monthly average wind speeds (index 0 = January).
    """
    _check_meteostat()
    
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    
    df = get_daily_data(station_id, start, end, si_units=si_units)
    
    if df is None or df.empty:
        return [None] * 12
    
    df = df.reset_index()
    df['month'] = df['time'].dt.month
    df['year'] = df['time'].dt.year
    
    grouped = df.groupby(['year', 'month']).agg(
        wspd_mean=('wspd', 'mean'),
        count=('wspd', 'count')
    ).reset_index()
    
    grouped.loc[grouped['count'] < min_days, 'wspd_mean'] = pd.NA
    
    monthly = grouped.groupby('month')['wspd_mean'].mean()
    
    return [monthly.get(m) for m in range(1, 13)]


def coldest_month(
    station_id: str,
    start_year: int,
    end_year: int | None = None,
    min_days: int = 23,
    si_units: bool = True,
) -> tuple[int, float]:
    """Find the coldest month and its temperature.
    
    Parameters
    ----------
    station_id : str
        Meteostat station ID.
    start_year : int
        Start year (if end_year is None, uses only this year).
    end_year : int, optional
        End year (inclusive). If None, uses start_year only.
    min_days : int, optional
        Minimum days required for valid monthly average.
    si_units : bool, optional
        If True (default), return temperature in Kelvin.
    
    Returns
    -------
    tuple[int, float]
        (month_index, temperature) where month_index is 0-11.
    
    Examples
    --------
    >>> coldest_month("72243", 2023)
    (0, 283.5)  # January at 283.5 K
    """
    if end_year is None:
        end_year = start_year
    
    temps = month_average_temperature(station_id, start_year, end_year, min_days, si_units)
    valid = [(i, t) for i, t in enumerate(temps) if t is not None]
    
    if not valid:
        raise ValueError("No valid temperature data")
    
    return min(valid, key=lambda x: x[1])


def warmest_month(
    station_id: str,
    start_year: int,
    end_year: int | None = None,
    min_days: int = 23,
    si_units: bool = True,
) -> tuple[int, float]:
    """Find the warmest month and its temperature.
    
    Parameters
    ----------
    station_id : str
        Meteostat station ID.
    start_year : int
        Start year (if end_year is None, uses only this year).
    end_year : int, optional
        End year (inclusive). If None, uses start_year only.
    min_days : int, optional
        Minimum days required for valid monthly average.
    si_units : bool, optional
        If True (default), return temperature in Kelvin.
    
    Returns
    -------
    tuple[int, float]
        (month_index, temperature) where month_index is 0-11.
    
    Examples
    --------
    >>> warmest_month("72243", 2023)
    (7, 303.2)  # August at 303.2 K
    """
    if end_year is None:
        end_year = start_year
    
    temps = month_average_temperature(station_id, start_year, end_year, min_days, si_units)
    valid = [(i, t) for i, t in enumerate(temps) if t is not None]
    
    if not valid:
        raise ValueError("No valid temperature data")
    
    return max(valid, key=lambda x: x[1])
