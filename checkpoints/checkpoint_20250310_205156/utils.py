from datetime import datetime

def validate_date(date_str):
    """Validate date format DD/MM/YYYY"""
    try:
        return bool(datetime.strptime(date_str, "%d/%m/%Y"))
    except ValueError:
        return False

def validate_time(time_str):
    """Validate time format HH:MM"""
    try:
        return bool(datetime.strptime(time_str, "%H:%M"))
    except ValueError:
        return False

def validate_numeric(value):
    """Validate if string can be converted to float"""
    try:
        float(value)
        return True
    except ValueError:
        return False

def validate_range(value, min_val, max_val):
    """Validate if numeric value is within range"""
    try:
        num = float(value)
        return min_val <= num <= max_val
    except ValueError:
        return False
