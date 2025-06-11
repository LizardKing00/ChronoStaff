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

try:
    from ttkthemes import ThemedStyle
    THEMES_AVAILABLE = True
except ImportError:
    THEMES_AVAILABLE = False

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
        self.dialog.geometry("350x320")  # Made wider to fit all 7 days
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Get the main app's style or create new one, this ensures compatibility with ttkthemes
        if hasattr(parent, 'style') and THEMES_AVAILABLE:
            self.style = parent.style
        else:
            self.style = ttk.Style()
        
        # Configure custom styles that work with themes
        self._configure_calendar_styles()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (320 // 2)
        self.dialog.geometry(f"350x320+{x}+{y}")
        
        self.create_calendar()
    
    def _configure_calendar_styles(self):
        """Configure calendar-specific styles that work with ttkthemes"""
        
        # Get current theme colors if available
        try:
            # Try to get theme-appropriate colors
            bg_color = self.style.lookup('TFrame', 'background') or 'white'
            fg_color = self.style.lookup('TLabel', 'foreground') or '#333333'
        except:
            bg_color = 'white'
            fg_color = '#333333'
        
        # Calendar frame styling
        self.style.configure('Calendar.TFrame', background=bg_color)
        
        # Header styling
        self.style.configure('Calendar.Header.TLabel', 
                           font=('Segoe UI', 9, 'bold'), 
                           foreground=fg_color,
                           background=bg_color)
        
        # Regular day button
        try:
            # Try to get theme's foreground color
            button_fg = self.style.lookup('TButton', 'foreground') or '#333333'
        except:
            button_fg = '#333333'
            
        self.style.configure('Calendar.Day.TButton', 
                           font=('Segoe UI', 8),
                           foreground=button_fg,
                           padding=(2, 2))
        
        # Navigation buttons
        self.style.configure('Calendar.Nav.TButton',
                           font=('Segoe UI', 9),
                           width=3)
        
        # Action buttons
        self.style.configure('Calendar.Action.TButton',
                           font=('Segoe UI', 9),
                           padding=5)
        
        # Create a custom button class for special days that bypasses theme styling
        self.create_custom_button_styles()
    
    def create_custom_button_styles(self):
        """Create custom button styles for special calendar days"""
        
        # Holiday/Sunday style (red)
        self.style.configure('Calendar.Holiday.TButton', 
                           font=('Segoe UI', 8, 'bold'),
                           foreground='white',
                           background='#e74c3c',
                           borderwidth=1,
                           relief='raised')
        self.style.map('Calendar.Holiday.TButton',
                      foreground=[('active', 'white'), ('pressed', 'white')],
                      background=[('active', '#c0392b'), ('pressed', '#a93226')])
        
        # Saturday style (orange)
        self.style.configure('Calendar.Saturday.TButton', 
                           font=('Segoe UI', 8, 'bold'),
                           foreground='white',
                           background='#f39c12',
                           borderwidth=1,
                           relief='raised')
        self.style.map('Calendar.Saturday.TButton',
                      foreground=[('active', 'white'), ('pressed', 'white')],
                      background=[('active', '#e67e22'), ('pressed', '#d68910')])
        
        # Today style (blue)
        self.style.configure('Calendar.Today.TButton', 
                           font=('Segoe UI', 8, 'bold'),
                           foreground='white',
                           background='#4a90e2',
                           borderwidth=1,
                           relief='raised')
        self.style.map('Calendar.Today.TButton',
                      foreground=[('active', 'white'), ('pressed', 'white')],
                      background=[('active', '#3a7bc8'), ('pressed', '#2e6aa3')])
        
        # Selected style (darker blue)
        self.style.configure('Calendar.Selected.TButton', 
                           font=('Segoe UI', 8, 'bold'),
                           foreground='white',
                           background='#3a7bc8',
                           borderwidth=1,
                           relief='raised')
        self.style.map('Calendar.Selected.TButton',
                      foreground=[('active', 'white'), ('pressed', 'white')],
                      background=[('active', '#2e6aa3'), ('pressed', '#255a8a')])
        
        # Today + Holiday combination (purple)
        self.style.configure('Calendar.TodayHoliday.TButton', 
                           font=('Segoe UI', 8, 'bold'),
                           foreground='white',
                           background='#8e44ad',
                           borderwidth=1,
                           relief='raised')
        self.style.map('Calendar.TodayHoliday.TButton',
                      foreground=[('active', 'white'), ('pressed', 'white')],
                      background=[('active', '#7d3c98'), ('pressed', '#6c3483')])
        
        # Today + Saturday combination (blue-orange)
        self.style.configure('Calendar.TodaySaturday.TButton', 
                           font=('Segoe UI', 8, 'bold'),
                           foreground='white',
                           background='#e67e22',
                           borderwidth=1,
                           relief='raised')
        self.style.map('Calendar.TodaySaturday.TButton',
                      foreground=[('active', 'white'), ('pressed', 'white')],
                      background=[('active', '#d68910'), ('pressed', '#ca7a00')])
        
        # Selected + Holiday combination (lighter purple)
        self.style.configure('Calendar.SelectedHoliday.TButton', 
                           font=('Segoe UI', 8, 'bold'),
                           foreground='white',
                           background='#9b59b6',
                           borderwidth=1,
                           relief='raised')
        self.style.map('Calendar.SelectedHoliday.TButton',
                      foreground=[('active', 'white'), ('pressed', 'white')],
                      background=[('active', '#8e44ad'), ('pressed', '#7d3c98')])
        
        # Selected + Saturday combination (darker orange)
        self.style.configure('Calendar.SelectedSaturday.TButton', 
                           font=('Segoe UI', 8, 'bold'),
                           foreground='white',
                           background='#d68910',
                           borderwidth=1,
                           relief='raised')
        self.style.map('Calendar.SelectedSaturday.TButton',
                      foreground=[('active', 'white'), ('pressed', 'white')],
                      background=[('active', '#ca7a00'), ('pressed', '#b8690a')])
    
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
    
    def is_saturday(self, date_obj):
        """Check if a date is Saturday (weekday 5)"""
        return date_obj.weekday() == 5
    
    def is_holiday(self, date_obj):
        """Check if a date is a German holiday"""
        return date_obj in self.german_holidays
    
    def is_sunday_or_holiday(self, date_obj):
        """Check if a date is Sunday or a German holiday"""
        return self.is_sunday(date_obj) or self.is_holiday(date_obj)
    
    def is_weekend_or_holiday(self, date_obj):
        """Check if a date is weekend (Saturday/Sunday) or a German holiday"""
        return self.is_saturday(date_obj) or self.is_sunday(date_obj) or self.is_holiday(date_obj)
        
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
                                   font=('Segoe UI', 10, 'bold'))
        self.month_label.pack(side=tk.LEFT, expand=True)
        
        ttk.Button(nav_frame, text="▶", style='Calendar.Nav.TButton',
                  command=self.next_month).pack(side=tk.RIGHT)
        
        # Calendar grid
        self.cal_frame = ttk.Frame(main_frame)
        self.cal_frame.pack(fill=tk.BOTH, expand=True)
        
        # Days header - highlight Saturday in orange and Sunday in red
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for i, day in enumerate(days):
            color = None
            if day == 'Sunday':
                color = '#e74c3c'  # Red
            elif day == 'Saturday':
                color = '#f39c12'  # Orange
                
            label = ttk.Label(self.cal_frame, 
                     text=day[:3].upper(), 
                     font=('Segoe UI', 9, 'bold'),
                     anchor='center')
            if color:
                label.configure(foreground=color)
            label.grid(row=0, column=i, padx=1, pady=2, sticky='ew')
            self.cal_frame.columnconfigure(i, weight=1, minsize=45)  # Ensure minimum column width
        
        for i in range(1, 7):  # Rows 1-6 for calendar weeks
            self.cal_frame.rowconfigure(i, weight=1)
        
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
                        row=week_num, column=day_num, padx=1, pady=2)
                    continue
                
                current_date = date(self.year_var.get(), self.month_var.get(), day)
                today = date.today()
                
                # Determine colors based on conditions
                is_today = current_date == today
                is_selected = current_date == self.selected_date
                is_holiday = self.is_holiday(current_date)
                is_sunday = self.is_sunday(current_date)
                is_saturday = self.is_saturday(current_date)
                
                # Default colors
                bg_color = None
                fg_color = '#333333'
                font_weight = 'normal'
                
                # Priority order: Selected > Weekend/Holiday colors > Today > Regular
                if is_selected and is_sunday:
                    bg_color = '#c0392b'  # Darker red for selected Sunday
                    fg_color = 'white'
                    font_weight = 'bold'
                elif is_selected and is_saturday:
                    bg_color = '#d68910'  # Darker orange for selected Saturday
                    fg_color = 'white'
                    font_weight = 'bold'
                elif is_selected and is_holiday:
                    bg_color = '#9b59b6'  # Purple for selected holiday
                    fg_color = 'white'
                    font_weight = 'bold'
                elif is_selected:
                    bg_color = '#3a7bc8'  # Dark blue for selected regular day
                    fg_color = 'white'
                    font_weight = 'bold'
                elif is_sunday:
                    bg_color = '#e74c3c'  # Red for all Sundays
                    fg_color = 'white'
                    font_weight = 'bold'
                elif is_saturday:
                    bg_color = '#f39c12'  # Orange for all Saturdays
                    fg_color = 'white'
                    font_weight = 'bold'
                elif is_holiday:
                    bg_color = '#e74c3c'  # Red for holidays (same as Sunday)
                    fg_color = 'white'
                    font_weight = 'bold'
                elif is_today:
                    bg_color = '#4a90e2'  # Blue for today (only if not weekend/holiday)
                    fg_color = 'white'
                    font_weight = 'bold'
                
                # Create the day widget
                if bg_color:
                    # Create a colored frame for special days
                    day_frame = tk.Frame(self.cal_frame, 
                                       bg=bg_color, 
                                       relief='raised',
                                       borderwidth=1,
                                       cursor='hand2')
                    day_frame.grid(row=week_num, column=day_num, padx=1, pady=2, sticky='nsew')
                    
                    # Add label inside frame
                    day_label = tk.Label(day_frame,
                                       text=str(day),
                                       bg=bg_color,
                                       fg=fg_color,
                                       font=('Segoe UI', 8, font_weight),
                                       cursor='hand2')
                    day_label.pack(expand=True, fill='both', padx=4, pady=4)
                    
                    # Bind click events to both frame and label
                    day_frame.bind('<Button-1>', lambda e, d=day: self.day_clicked(d))
                    day_label.bind('<Button-1>', lambda e, d=day: self.day_clicked(d))
                    
                    # Add tooltip for special days
                    if is_holiday:
                        holiday_name = self.german_holidays.get(current_date, "Holiday")
                        self.create_tooltip_for_widget(day_frame, holiday_name)
                        self.create_tooltip_for_widget(day_label, holiday_name)
                    elif is_sunday:
                        self.create_tooltip_for_widget(day_frame, "Sunday")
                        self.create_tooltip_for_widget(day_label, "Sunday")
                    elif is_saturday:
                        self.create_tooltip_for_widget(day_frame, "Saturday")
                        self.create_tooltip_for_widget(day_label, "Saturday")
                        
                else:
                    # Use regular button for normal days
                    btn = ttk.Button(self.cal_frame, 
                                    text=str(day), 
                                    style='Calendar.Day.TButton',
                                    command=lambda d=day: self.day_clicked(d))
                    btn.grid(row=week_num, column=day_num, padx=1, pady=2, sticky='nsew')
    
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
    
    def create_tooltip_for_widget(self, widget, text):
        """Create a simple tooltip for any widget"""
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