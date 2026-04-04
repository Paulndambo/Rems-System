from datetime import date
import calendar

def get_due_date(month_name: str, year: int = None):
    if year is None:
        year = date.today().year  # default to current year

    # Normalize month name (handles "march", "March", etc.)
    month_name = month_name.capitalize()

    # Convert month name → month number
    month_number = list(calendar.month_name).index(month_name)

    if month_number == 0:
        raise ValueError(f"Invalid month name: {month_name}")

    # Construct due date (always 5th)
    due_date = date(year, month_number, 5)

    return due_date