import tkinter as tk
from tkinter import ttk
from datetime import date
import calendar

# =============================================================================
# CALENDAR POPUP WIDGET
# =============================================================================

class CalendarDialog:
    def __init__(self, parent, initial_date=None):
        self.parent = parent
        self.selected_date = initial_date or date.today()
        self.result = None
        
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
        self.style.configure('Calendar.Today.TButton', 
                           font=('Segoe UI', 8, 'bold'), 
                           foreground='white',
                           background='#4a90e2')
        self.style.configure('Calendar.Selected.TButton', 
                           font=('Segoe UI', 8, 'bold'), 
                           foreground='white',
                           background='#3a7bc8')
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
        
        # Days header
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for i, day in enumerate(days):
            ttk.Label(self.cal_frame, 
                     text=day[:3].upper(), 
                     style='Calendar.Header.TLabel',
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
                
                btn = ttk.Button(self.cal_frame, 
                                text=str(day), 
                                style='Calendar.Day.TButton',
                                command=lambda d=day: self.day_clicked(d))
                
                # Highlight selected date
                if (day == self.selected_date.day and 
                    self.month_var.get() == self.selected_date.month and
                    self.year_var.get() == self.selected_date.year):
                    btn.configure(style='Calendar.Selected.TButton')
                
                # Highlight today
                today = date.today()
                if (day == today.day and 
                    self.month_var.get() == today.month and
                    self.year_var.get() == today.year):
                    btn.configure(style='Calendar.Today.TButton')
                
                btn.grid(row=week_num, column=day_num, padx=2, pady=2, sticky='nsew')
    
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
