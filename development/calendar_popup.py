import tkinter as tk
from tkinter import ttk
from datetime import date
import calendar

try:
    import holidays
    HOLIDAYS_AVAILABLE = True
except ImportError:
    HOLIDAYS_AVAILABLE = False
    print("Warning: 'holidays' package not found. Install with: pip install holidays")

# =============================================================================
# CALENDAR POPUP WIDGET WITH GERMAN HOLIDAYS
# =============================================================================

class CalendarDialog:
    def __init__(self, parent, initial_date=None):
        self.parent = parent
        self.selected_date = initial_date or date.today()
        self.result = None
        
        # Initialize German holidays
        if HOLIDAYS_AVAILABLE:
            self.german_holidays = holidays.Germany()
        else:
            # Fallback: manual list of major German holidays for current year
            self.german_holidays = self._get_fallback_holidays()
        
        # Create popup window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Date")
        self.dialog.geometry("300x320")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Modern styling
        self.style = ttk.Style()
        self.style.configure('Calendar.TFrame', background='white')
        self.style.configure('Calendar.Header.TLabel', 
                           font=('Segoe UI', 9, 'bold'), 
                           foreground='#333333',
                           background='white')
        self.style.configure('Calendar.Day.TButton', 
                           font=('Segoe UI', 8), 
                           foreground='#333333',
                           borderwidth=1)
        self.style.map('Calendar.Day.TButton',
                      foreground=[('active', 'white'), ('pressed', 'white')],
                      background=[('active', '#4a90e2'), ('pressed', '#3a7bc8')])
        
        # Red styling for Sundays and holidays
        self.style.configure('Calendar.Holiday.TButton', 
                           font=('Segoe UI', 8, 'bold'), 
                           foreground='white',
                           background='#e74c3c')
        self.style.map('Calendar.Holiday.TButton',
                      foreground=[('active', 'white'), ('pressed', 'white')],
                      background=[('active', '#c0392b'), ('pressed', '#a93226')])
        
        self.style.configure('Calendar.Today.TButton', 
                           font=('Segoe UI', 8, 'bold'), 
                           foreground='white',
                           background='#4a90e2')
        self.style.configure('Calendar.Selected.TButton', 
                           font=('Segoe UI', 8, 'bold'), 
                           foreground='white',
                           background='#3a7bc8')
        
        # Today + Holiday combination
        self.style.configure('Calendar.TodayHoliday.TButton', 
                           font=('Segoe UI', 8, 'bold'), 
                           foreground='white',
                           background='#8e44ad')
        
        # Selected + Holiday combination
        self.style.configure('Calendar.SelectedHoliday.TButton', 
                           font=('Segoe UI', 8, 'bold'), 
                           foreground='white',
                           background='#9b59b6')
        
        self.style.configure('Calendar.Nav.TButton',
                           font=('Segoe UI', 9),
                           width=3)
        self.style.configure('Calendar.Action.TButton',
                           font=('Segoe UI', 9),
                           padding=5)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (320 // 2)
        self.dialog.geometry(f"300x320+{x}+{y}")
        
        self.create_calendar()
    
    def _get_fallback_holidays(self):
        """Fallback German holidays if holidays package is not available"""
        current_year = date.today().year
        fallback_holidays = {}
        
        # Fixed date holidays
        fallback_holidays[date(current_year, 1, 1)] = "Neujahr"
        fallback_holidays[date(current_year, 5, 1)] = "Tag der Arbeit"
        fallback_holidays[date(current_year, 10, 3)] = "Tag der Deutschen Einheit"
        fallback_holidays[date(current_year, 12, 25)] = "1. Weihnachtsfeiertag"
        fallback_holidays[date(current_year, 12, 26)] = "2. Weihnachtsfeiertag"
        
        # Add previous and next year for navigation
        for year in [current_year - 1, current_year + 1]:
            fallback_holidays[date(year, 1, 1)] = "Neujahr"
            fallback_holidays[date(year, 5, 1)] = "Tag der Arbeit"
            fallback_holidays[date(year, 10, 3)] = "Tag der Deutsche Einheit"
            fallback_holidays[date(year, 12, 25)] = "1. Weihnachtsfeiertag"
            fallback_holidays[date(year, 12, 26)] = "2. Weihnachtsfeiertag"
        
        return fallback_holidays
    
    def is_sunday(self, date_obj):
        """Check if a date is Sunday (weekday 6)"""
        return date_obj.weekday() == 6
    
    def is_holiday(self, date_obj):
        """Check if a date is a German holiday"""
        return date_obj in self.german_holidays
    
    def is_sunday_or_holiday(self, date_obj):
        """Check if a date is Sunday or a German holiday"""
        return self.is_sunday(date_obj) or self.is_holiday(date_obj)
        
    def create_calendar(self):
        # Main container
        main_frame = ttk.Frame(self.dialog, style='Calendar.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Month/Year navigation
        nav_frame = ttk.Frame(main_frame)
        nav_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.month_var = tk.IntVar(value=self.selected_date.month)
        self.year_var = tk.IntVar(value=self.selected_date.year)
        
        ttk.Button(nav_frame, text="◀", style='Calendar.Nav.TButton',
                  command=self.prev_month).pack(side=tk.LEFT)
        
        self.month_label = ttk.Label(nav_frame, 
                                   text=f"{calendar.month_name[self.month_var.get()]} {self.year_var.get()}",
                                   font=('Segoe UI', 10, 'bold'),
                                   foreground='#333333')
        self.month_label.pack(side=tk.LEFT, expand=True)
        
        ttk.Button(nav_frame, text="▶", style='Calendar.Nav.TButton',
                  command=self.next_month).pack(side=tk.RIGHT)
        
        # Calendar grid
        self.cal_frame = ttk.Frame(main_frame)
        self.cal_frame.pack(fill=tk.BOTH, expand=True)
        
        # Days header - highlight Sunday in red
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for i, day in enumerate(days):
            color = '#e74c3c' if day == 'Sunday' else '#333333'
            ttk.Label(self.cal_frame, 
                     text=day[:3].upper(), 
                     font=('Segoe UI', 9, 'bold'),
                     foreground=color,
                     background='white',
                     anchor='center').grid(
                row=0, column=i, padx=2, pady=2, sticky='ew')
            self.cal_frame.columnconfigure(i, weight=1)
        
        self.draw_calendar()
        
        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Today", style='Calendar.Action.TButton',
                  command=self.select_today).pack(side=tk.LEFT)
        
        ttk.Button(btn_frame, text="Select Date", style='Calendar.Action.TButton',
                  command=self.ok_clicked).pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, text="Cancel", style='Calendar.Action.TButton',
                  command=self.cancel_clicked).pack(side=tk.RIGHT, padx=5)
    
    def draw_calendar(self):
        # Clear existing calendar days
        for widget in self.cal_frame.winfo_children():
            if widget.grid_info()['row'] > 0:  # Keep header row
                widget.destroy()
        
        # Calendar days
        cal = calendar.monthcalendar(self.year_var.get(), self.month_var.get())
        
        for week_num, week in enumerate(cal, 1):
            for day_num, day in enumerate(week):
                if day == 0:
                    # Empty space for days not in current month
                    ttk.Label(self.cal_frame, text="").grid(
                        row=week_num, column=day_num, padx=2, pady=2)
                    continue
                
                current_date = date(self.year_var.get(), self.month_var.get(), day)
                today = date.today()
                
                # Determine button style based on conditions
                style = 'Calendar.Day.TButton'
                
                is_today = current_date == today
                is_selected = current_date == self.selected_date
                is_holiday_or_sunday = self.is_sunday_or_holiday(current_date)
                
                # Priority order: Selected > Today > Holiday/Sunday > Regular
                if is_selected and is_holiday_or_sunday:
                    style = 'Calendar.SelectedHoliday.TButton'
                elif is_selected:
                    style = 'Calendar.Selected.TButton'
                elif is_today and is_holiday_or_sunday:
                    style = 'Calendar.TodayHoliday.TButton'
                elif is_today:
                    style = 'Calendar.Today.TButton'
                elif is_holiday_or_sunday:
                    style = 'Calendar.Holiday.TButton'
                
                btn = ttk.Button(self.cal_frame, 
                                text=str(day), 
                                style=style,
                                command=lambda d=day: self.day_clicked(d))
                
                # Add tooltip for holidays
                if self.is_holiday(current_date):
                    holiday_name = self.german_holidays.get(current_date, "Holiday")
                    self.create_tooltip(btn, holiday_name)
                elif self.is_sunday(current_date):
                    self.create_tooltip(btn, "Sonntag")
                
                btn.grid(row=week_num, column=day_num, padx=2, pady=2, sticky='nsew')
    
    def create_tooltip(self, widget, text):
        """Create a simple tooltip for holidays"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, 
                           background='#333333', foreground='white',
                           font=('Segoe UI', 8), padx=5, pady=2)
            label.pack()
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    def prev_month(self):
        if self.month_var.get() == 1:
            self.month_var.set(12)
            self.year_var.set(self.year_var.get() - 1)
        else:
            self.month_var.set(self.month_var.get() - 1)
        self.update_display()
    
    def next_month(self):
        if self.month_var.get() == 12:
            self.month_var.set(1)
            self.year_var.set(self.year_var.get() + 1)
        else:
            self.month_var.set(self.month_var.get() + 1)
        self.update_display()
    
    def update_display(self):
        # Update month/year label
        self.month_label.config(text=f"{calendar.month_name[self.month_var.get()]} {self.year_var.get()}")
        self.draw_calendar()
    
    def day_clicked(self, day):
        self.selected_date = date(self.year_var.get(), self.month_var.get(), day)
        self.draw_calendar()
    
    def select_today(self):
        today = date.today()
        self.selected_date = today
        self.month_var.set(today.month)
        self.year_var.set(today.year)
        self.update_display()
    
    def ok_clicked(self):
        self.result = self.selected_date
        self.dialog.destroy()
    
    def cancel_clicked(self):
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        self.dialog.wait_window()
        return self.result
