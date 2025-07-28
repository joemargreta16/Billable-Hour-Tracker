from datetime import date, datetime, timedelta
from calendar import monthrange

def get_current_monthly_cycle():
    """
    Get the current monthly cycle dates (25th to 24th).
    Returns tuple of (start_date, end_date, cycle_name)
    """
    today = date.today()
    
    # If today is before the 25th, we're in the cycle that started last month
    if today.day < 25:
        # Cycle started on the 25th of the previous month
        if today.month == 1:
            start_year = today.year - 1
            start_month = 12
        else:
            start_year = today.year
            start_month = today.month - 1
        
        start_date = date(start_year, start_month, 25)
        end_date = date(today.year, today.month, 24)
        cycle_name = f"{start_date.strftime('%b %Y')} - {end_date.strftime('%b %Y')}"
    else:
        # Cycle starts on the 25th of this month
        start_date = date(today.year, today.month, 25)
        
        # End date is 24th of next month
        if today.month == 12:
            end_year = today.year + 1
            end_month = 1
        else:
            end_year = today.year
            end_month = today.month + 1
        
        end_date = date(end_year, end_month, 24)
        cycle_name = f"{start_date.strftime('%b %Y')} - {end_date.strftime('%b %Y')}"
    
    return start_date, end_date, cycle_name

def get_monthly_cycle_for_date(target_date):
    """
    Get the monthly cycle dates for a specific date.
    Returns tuple of (start_date, end_date, cycle_name)
    """
    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
    
    # If target date is before the 25th, cycle started last month
    if target_date.day < 25:
        if target_date.month == 1:
            start_year = target_date.year - 1
            start_month = 12
        else:
            start_year = target_date.year
            start_month = target_date.month - 1
        
        start_date = date(start_year, start_month, 25)
        end_date = date(target_date.year, target_date.month, 24)
    else:
        # Cycle starts on the 25th of this month
        start_date = date(target_date.year, target_date.month, 25)
        
        # End date is 24th of next month
        if target_date.month == 12:
            end_year = target_date.year + 1
            end_month = 1
        else:
            end_year = target_date.year
            end_month = target_date.month + 1
        
        end_date = date(end_year, end_month, 24)
    
    cycle_name = f"{start_date.strftime('%b %Y')} - {end_date.strftime('%b %Y')}"
    return start_date, end_date, cycle_name

def hours_to_decimal(hours_str):
    """
    Convert hours:minutes string to decimal hours.
    Accepts formats like "8", "8:30", "8.5"
    """
    if not hours_str:
        return 0.0
    
    hours_str = str(hours_str).strip()
    
    # Handle decimal format (e.g., "8.5")
    if '.' in hours_str and ':' not in hours_str:
        try:
            return float(hours_str)
        except ValueError:
            return 0.0
    
    # Handle hours:minutes format (e.g., "8:30")
    if ':' in hours_str:
        try:
            parts = hours_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return hours + (minutes / 60.0)
        except (ValueError, IndexError):
            return 0.0
    
    # Handle simple hours format (e.g., "8")
    try:
        return float(hours_str)
    except ValueError:
        return 0.0

def decimal_to_hours_minutes(decimal_hours):
    """
    Convert decimal hours to hours:minutes format.
    """
    if not decimal_hours:
        return "0:00"
    
    total_minutes = int(decimal_hours * 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}:{minutes:02d}"

def get_previous_cycles(num_cycles=12):
    """
    Get a list of previous monthly cycles for navigation.
    Returns list of objects with start_date, end_date, and name attributes
    """
    class Cycle:
        def __init__(self, start_date, end_date, name):
            self.start_date = start_date
            self.end_date = end_date
            self.name = name
    
    cycles = []
    current_start, current_end, current_name = get_current_monthly_cycle()
    
    # Add current cycle
    cycles.append(Cycle(current_start, current_end, current_name))
    
    # Add previous cycles
    for i in range(1, num_cycles):
        # Go back one cycle at a time
        prev_start = current_start - timedelta(days=1)  # Day before current start
        prev_start, prev_end, prev_name = get_monthly_cycle_for_date(prev_start)
        cycles.append(Cycle(prev_start, prev_end, prev_name))
        current_start = prev_start
    
    return cycles

def format_date_for_input(date_obj):
    """Format date for HTML date input (YYYY-MM-DD)"""
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime('%Y-%m-%d') if date_obj else ''

def parse_date_from_input(date_str):
    """Parse date from HTML date input"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None
