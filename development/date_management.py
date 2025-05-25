from datetime import datetime, date, timedelta
# =============================================================================
# DATE MANAGER
# =============================================================================
class DateManager:
    """Centralized date management for the application"""
    
    def __init__(self):
        self.reset_to_today()
    
    def reset_to_today(self):
        """Reset all dates to today's date"""
        today = date.today()
        self._selected_date = today
        self._view_month = today.month
        self._view_year = today.year
    
    @property
    def selected_date(self):
        """Get the currently selected date for time entry"""
        return self._selected_date
    
    @selected_date.setter
    def selected_date(self, new_date):
        """Set the selected date and validate it"""
        if isinstance(new_date, date):
            self._selected_date = new_date
        elif isinstance(new_date, str):
            try:
                self._selected_date = datetime.strptime(new_date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid date format: {new_date}")
        else:
            raise TypeError("Date must be a date object or YYYY-MM-DD string")
    
    @property
    def view_month(self):
        """Get the current month being viewed"""
        return self._view_month
    
    @property
    def view_year(self):
        """Get the current year being viewed"""
        return self._view_year
    
    def set_view_period(self, month, year):
        """Set the month/year being viewed for time records"""
        if not (1 <= month <= 12):
            raise ValueError(f"Invalid month: {month}")
        if not (2020 <= year <= 2030):
            raise ValueError(f"Invalid year: {year}")
        
        self._view_month = month
        self._view_year = year
    
    def set_date_components(self, day, month, year):
        """Set date from individual components with validation"""
        try:
            # Validate the date by creating it
            new_date = date(year, month, day)
            self._selected_date = new_date
            return True, ""
        except ValueError as e:
            return False, str(e)
    
    def get_date_components(self):
        """Get the selected date as (day, month, year) tuple"""
        return (self._selected_date.day, self._selected_date.month, self._selected_date.year)
    
    def get_formatted_date(self, format_str="%Y-%m-%d"):
        """Get the selected date in specified format"""
        return self._selected_date.strftime(format_str)
    
    def get_display_date(self):
        """Get a user-friendly display of the selected date"""
        return self._selected_date.strftime("%A, %B %d, %Y")