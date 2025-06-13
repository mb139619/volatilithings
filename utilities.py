from datetime import date

def days_in_year(year):
    """
    Returns the number of days in a given year, accounting for leap years.

    Parameters:
        year (int): The year to check.

    Returns:
        int: 365 for regular years, 366 for leap years.
    """
    # A leap year occurs every 4 years, except for years that are divisible by 100,
    # unless they are also divisible by 400.
    if (year % 4 == 0) and ((year % 100 != 0) or (year % 400 == 0)):
        return 366
    else:
        return 365

def compute_year_fraction(d1, d2) -> float:
    """
    Computes the year fraction between two dates using actual/actual (ISDA) convention.

    Parameters:
        d1 (datetime.date or datetime.datetime): Start date.
        d2 (datetime.date or datetime.datetime): End date.

    Returns:
        float: The time between d1 and d2 expressed in years, accounting for leap years.
    """
    # Convert datetime to date if needed
    d1 = d1.date() if hasattr(d1, "date") else d1
    d2 = d2.date() if hasattr(d2, "date") else d2

    # Ensure d1 <= d2 by swapping if needed
    if d1 > d2:
        d1, d2 = d2, d1

    year_fraction = 0.0
    current = d1

    # Loop through full calendar years between d1 and d2
    while current.year < d2.year:
        end_of_year = date(current.year, 12, 31)                  # Last day of current year
        days_in_current_year = days_in_year(current.year)        # 365 or 366
        days_remaining = (end_of_year - current).days + 1        # Remaining days in that year (inclusive)
        year_fraction += days_remaining / days_in_current_year   # Add fractional year part
        current = date(current.year + 1, 1, 1)                    # Move to next year's Jan 1

    # Handle final (possibly partial) year
    days_in_current_year = days_in_year(current.year)
    days_remaining = (d2 - current).days + 1
    year_fraction += days_remaining / days_in_current_year

    return year_fraction

