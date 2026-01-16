"""Heating and cooling degree day calculations.

These are pure functions with no external dependencies.
"""

from __future__ import annotations

__all__ = [
    "heating_degree_days",
    "cooling_degree_days",
]


def heating_degree_days(
    T: float,
    T_base: float = 291.483,  # 65°F = 18.33°C = 291.483 K
    truncate: bool = True
) -> float:
    """Calculate heating degree days (HDD).
    
    Heating degree days measure how much (in degrees), and for how long,
    the outside temperature was below a base temperature. Used for
    estimating heating energy requirements.
    
    Parameters
    ----------
    T : float
        Average outdoor temperature [K].
    T_base : float, default 291.483
        Base temperature [K]. Default is 65°F (18.33°C).
    truncate : bool, default True
        If True, negative values return 0.
    
    Returns
    -------
    float
        Heating degree days [K·day].
    
    Notes
    -----
    HDD = max(0, T_base - T) when truncate=True
    HDD = T_base - T when truncate=False
    
    Examples
    --------
    >>> heating_degree_days(280.0)  # Cold day
    11.483
    
    >>> heating_degree_days(300.0)  # Warm day
    0.0
    
    >>> heating_degree_days(300.0, truncate=False)
    -8.517
    """
    diff = T_base - T
    if truncate:
        return max(0.0, diff)
    return diff


def cooling_degree_days(
    T: float,
    T_base: float = 291.483,  # 65°F = 18.33°C = 291.483 K
    truncate: bool = True
) -> float:
    """Calculate cooling degree days (CDD).
    
    Cooling degree days measure how much (in degrees), and for how long,
    the outside temperature was above a base temperature. Used for
    estimating cooling energy requirements.
    
    Parameters
    ----------
    T : float
        Average outdoor temperature [K].
    T_base : float, default 291.483
        Base temperature [K]. Default is 65°F (18.33°C).
    truncate : bool, default True
        If True, negative values return 0.
    
    Returns
    -------
    float
        Cooling degree days [K·day].
    
    Notes
    -----
    CDD = max(0, T - T_base) when truncate=True
    CDD = T - T_base when truncate=False
    
    Examples
    --------
    >>> cooling_degree_days(300.0)  # Hot day
    8.517
    
    >>> cooling_degree_days(280.0)  # Cold day
    0.0
    
    >>> cooling_degree_days(280.0, truncate=False)
    -11.483
    """
    diff = T - T_base
    if truncate:
        return max(0.0, diff)
    return diff
