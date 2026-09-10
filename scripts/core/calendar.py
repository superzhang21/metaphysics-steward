import math
from datetime import datetime, timedelta, timezone
from lunar_python import Solar, Lunar

SH_TZ = timezone(timedelta(hours=8))

def get_true_solar_time(dt: datetime, longitude: float) -> datetime:
    """
    Corrects civil time to True Solar Time based on longitude and Equation of Time.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=SH_TZ)

    # Equation of Time
    day_of_year = dt.timetuple().tm_yday
    b = 2 * math.pi * (day_of_year - 81) / 365
    eot = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)

    # Longitude offset (4 minutes per degree from 120E)
    lon_offset = 4 * (longitude - 120.0)

    total_offset = eot + lon_offset
    return dt + timedelta(minutes=total_offset)

def get_lunar(dt: datetime):
    solar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    return solar.getLunar()
