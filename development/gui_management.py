# Employee Time Management Desktop App - Enhanced GUI

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font
import sqlite3
from datetime import datetime, date, timedelta
import calendar
import json
from calendar_popup import CalendarDialog
from database_management import DatabaseManager, EmployeeManager, TimeTracker, SettingsManager
from date_management import DateManager
import os
import base64

# =============================================================================
# MAIN APPLICATION GUI
# =============================================================================

class EmployeeTimeApp:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Chrono Staff")
        self.root.geometry("1200x800")
        self.date_manager = DateManager()
        self.setup_ui_variables()
        self.date_var = tk.StringVar() #TODO remove?
        self.date_display_var = tk.StringVar()        

        # Initialize database and managers
        self.db_manager = DatabaseManager()
        self.employee_manager = EmployeeManager(self.db_manager)
        self.time_tracker = TimeTracker(self.db_manager)
        self.settings_manager = SettingsManager(self.db_manager)

        # Current selections
        self.selected_employee = None
        self.selected_employee_id = None
        self.current_month = datetime.now().month
        self.current_year = datetime.now().year
        
        # Style configuration
        self.configure_styles()
        self.create_widgets()

        self.start_times = None
        self.end_times = None

    def setup_ui_variables(self):
        """Initialize all UI variables"""
        # Date component variables
        day, month, year = self.date_manager.get_date_components()
        self.day_var = tk.IntVar(value=day)
        self.month_var = tk.IntVar(value=month)
        self.year_var = tk.IntVar(value=year)
        
        # Display variables
        self.date_display_var = tk.StringVar()
        self.period_display_var = tk.StringVar()
        
        # Entry variables
        self.emp_var = tk.StringVar()
        self.hours_var = tk.DoubleVar()
        self.type_var = tk.StringVar(value="work")
        self.notes_var = tk.StringVar()
        
        # Bind variable changes to update methods
        self.day_var.trace('w', self.on_date_component_change)
        self.month_var.trace('w', self.on_date_component_change)
        self.year_var.trace('w', self.on_date_component_change)

  # =============================================================================
  # WINDOWS, TABS ETC...
  # =============================================================================

    def configure_styles(self):
        """Configure custom styles for the application"""
        style = ttk.Style()
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Info.TLabel', font=('Arial', 10), foreground='blue')
        style.configure('Error.TLabel', font=('Arial', 10), foreground='red')
    
    def create_widgets(self):
        """Create main GUI widgets"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_employees_tab()
        self.create_time_tracking_tab()
        self.create_reports_tab()
        self.create_export_tab()
        self.create_settings_tab()
        self.create_employee_details_tab()
    
    def create_employees_tab(self):
        """Create employee management tab"""
        emp_frame = ttk.Frame(self.notebook)
        self.notebook.add(emp_frame, text="Employees")
        
        # Main container
        main_container = ttk.Frame(emp_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Employee Management", style='Title.TLabel').pack(side=tk.LEFT)
        
        # Show inactive employees checkbox
        self.show_inactive_var = tk.BooleanVar()
        ttk.Checkbutton(header_frame, text="Show Inactive Employees", 
                       variable=self.show_inactive_var,
                       command=self.refresh_employee_list).pack(side=tk.RIGHT)
        
        # Employee list frame
        list_frame = ttk.Frame(main_container)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for employee list
        columns = ('ID', 'Name', 'Position', 'Hourly Rate', 'Hours/Week', 'Vacation Days', 'Email', 'Status')
        self.emp_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        # Configure columns
        column_widths = {
            'ID': 80, 'Name': 150, 'Position': 120, 'Hourly Rate': 100,
            'Hours/Week': 100, 'Vacation Days': 100, 'Email': 180, 'Status': 80
        }
        
        for col in columns:
            self.emp_tree.heading(col, text=col)
            self.emp_tree.column(col, width=column_widths.get(col, 120))
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.emp_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.emp_tree.xview)
        self.emp_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.emp_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Buttons frame
        btn_frame = ttk.Frame(main_container)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Left side buttons
        left_btn_frame = ttk.Frame(btn_frame)
        left_btn_frame.pack(side=tk.LEFT)
        
        ttk.Button(left_btn_frame, text="Add Employee", command=self.add_employee_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(left_btn_frame, text="Edit Employee", command=self.edit_employee_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(left_btn_frame, text="View Details", command=self.create_employee_details_window).pack(side=tk.LEFT, padx=5)
        
        # Right side buttons
        right_btn_frame = ttk.Frame(btn_frame)
        right_btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(right_btn_frame, text="Deactivate", command=self.deactivate_employee).pack(side=tk.LEFT, padx=5)
        ttk.Button(right_btn_frame, text="Reactivate", command=self.reactivate_employee).pack(side=tk.LEFT, padx=5)
        ttk.Button(right_btn_frame, text="Delete Permanently", command=self.delete_employee).pack(side=tk.LEFT, padx=5)
        ttk.Button(right_btn_frame, text="Refresh", command=self.refresh_employee_list).pack(side=tk.LEFT, padx=(5, 0))
        
        self.refresh_employee_list()
    
    def create_time_tracking_tab(self):
        """Create time tracking tab with multiple start/end times and German labor law compliance"""
        time_frame = ttk.Frame(self.notebook)
        self.notebook.add(time_frame, text="Time Tracking")

        # Main container
        main_container = ttk.Frame(time_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Employee selection frame
        select_frame = ttk.LabelFrame(main_container, text="Employee & Period Selection")
        select_frame.pack(fill=tk.X, pady=(0, 10))

        # Employee selection row
        emp_row = ttk.Frame(select_frame)
        emp_row.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(emp_row, text="Employee:").pack(side=tk.LEFT)
        self.emp_var = tk.StringVar()
        self.emp_combo = ttk.Combobox(emp_row, textvariable=self.emp_var, width=40, state="readonly")
        self.emp_combo.pack(side=tk.LEFT, padx=(5, 20))
        self.emp_combo.bind('<<ComboboxSelected>>', self.on_employee_select)

        # Month/Year selection frame
        period_frame = ttk.Frame(emp_row)
        period_frame.pack(side=tk.LEFT, padx=(20, 0))

        self.period_display_var = tk.StringVar()
        self.period_display_var.set(f"Viewing: {self.date_manager.view_month:02d}/{self.date_manager.view_year}")
        ttk.Label(period_frame, textvariable=self.period_display_var, style='Info.TLabel').pack(side=tk.LEFT, padx=(5, 20))

        ttk.Button(period_frame, text="Load Month Data", command=self.load_month_data).pack(side=tk.LEFT, padx=5)

        # Time entry section
        entry_frame = ttk.LabelFrame(main_container, text="Add/Edit Time Entry")
        entry_frame.pack(fill=tk.X, pady=(0, 10))

        # Date selection frame
        date_selection_frame = ttk.Frame(entry_frame)
        date_selection_frame.pack(fill=tk.X, padx=10, pady=5)

        # Date input section
        date_input_frame = ttk.Frame(date_selection_frame)
        date_input_frame.pack(side=tk.LEFT)

        ttk.Label(date_input_frame, text="Date:").pack(side=tk.LEFT)

        # Date entry fields
        self.day_var = tk.IntVar(value=date.today().day)
        self.date_month_var = tk.IntVar(value=date.today().month)
        self.date_year_var = tk.IntVar(value=date.today().year)

        # Date spinboxes
        self.day_spin = tk.Spinbox(date_input_frame, from_=1, to=31, textvariable=self.day_var, width=4)
        self.day_spin.pack(side=tk.LEFT, padx=(15, 2))
        ttk.Label(date_input_frame, text="/").pack(side=tk.LEFT)

        self.month_spin = tk.Spinbox(date_input_frame, from_=1, to=12, textvariable=self.date_month_var, width=4)
        self.month_spin.pack(side=tk.LEFT, padx=2)
        ttk.Label(date_input_frame, text="/").pack(side=tk.LEFT)

        self.year_spin = tk.Spinbox(date_input_frame, from_=2020, to=2030, textvariable=self.date_year_var, width=6)
        self.year_spin.pack(side=tk.LEFT, padx=2)

        # Calendar buttons
        calendar_frame = ttk.Frame(date_selection_frame)
        calendar_frame.pack(side=tk.LEFT, padx=(20, 0))

        ttk.Button(calendar_frame, text="Calendar", width=12, command=self.open_calendar).pack(side=tk.LEFT, padx=5)
        ttk.Button(calendar_frame, text="Today", width=8, command=self.set_to_today).pack(side=tk.LEFT, padx=5)

        # Time entries frame (new section for multiple start/end times)
        time_entries_frame = ttk.LabelFrame(entry_frame, text="Work Time Periods (Max 3)")
        time_entries_frame.pack(fill=tk.X, padx=10, pady=5)

        # Initialize time entry variables
        self.start_time_vars = [tk.StringVar() for _ in range(3)]
        self.end_time_vars = [tk.StringVar() for _ in range(3)]

        # Create 3 rows for time entries
        for i in range(3):
            time_row = ttk.Frame(time_entries_frame)
            time_row.pack(fill=tk.X, padx=10, pady=2)

            ttk.Label(time_row, text=f"Period {i+1}:", width=10).pack(side=tk.LEFT)

            ttk.Label(time_row, text="Start:").pack(side=tk.LEFT, padx=(10, 2))
            start_entry = ttk.Entry(time_row, textvariable=self.start_time_vars[i], width=8)
            start_entry.pack(side=tk.LEFT, padx=(0, 5))

            ttk.Label(time_row, text="End:").pack(side=tk.LEFT, padx=(5, 2))
            end_entry = ttk.Entry(time_row, textvariable=self.end_time_vars[i], width=8)
            end_entry.pack(side=tk.LEFT, padx=(0, 10))

            # Add time format hint
            if i == 0:
                ttk.Label(time_row, text="(Format: HH:MM, e.g., 09:00)", 
                         style='TLabel', foreground='gray').pack(side=tk.LEFT, padx=(10, 0))

        # Break time and additional options frame
        options_frame = ttk.Frame(entry_frame)
        options_frame.pack(fill=tk.X, padx=10, pady=5)

        # Record type and notes in first row
        type_notes_row = ttk.Frame(options_frame)
        type_notes_row.pack(fill=tk.X, pady=2)

        ttk.Label(type_notes_row, text="Type:").pack(side=tk.LEFT)
        self.type_var = tk.StringVar(value="work")
        type_combo = ttk.Combobox(type_notes_row, textvariable=self.type_var, 
                                 values=["work", "vacation", "sick", "holiday"], width=10, state="readonly")
        type_combo.pack(side=tk.LEFT, padx=(5, 15))

        ttk.Label(type_notes_row, text="Notes:").pack(side=tk.LEFT)
        self.notes_var = tk.StringVar()
        ttk.Entry(type_notes_row, textvariable=self.notes_var, width=40).pack(side=tk.LEFT, padx=(5, 20))

        # Action buttons
        button_frame = ttk.Frame(options_frame)
        button_frame.pack(side=tk.RIGHT)

        ttk.Button(button_frame, text="Calculate Preview", command=self.preview_time_calculation).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Button(button_frame, text="Add Entry", command=self.add_time_entry).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Clear Form", command=self.clear_time_form).pack(side=tk.LEFT, padx=(2, 5))

        # Calculation preview frame
        self.preview_frame = ttk.LabelFrame(entry_frame, text="Time Calculation Preview")
        self.preview_frame.pack(fill=tk.X, padx=10, pady=5)

        self.preview_text = tk.Text(self.preview_frame, height=3, wrap=tk.WORD, state=tk.DISABLED)
        self.preview_text.pack(fill=tk.X, padx=5, pady=5)

        # Time records display
        records_frame = ttk.LabelFrame(main_container, text="Time Records")
        records_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview and scrollbars should all use grid within their container
        tree_container = ttk.Frame(records_frame)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Updated columns to match new database schema
        time_columns = ('Date', 'Time Periods', 'Present', 'Worked', 'Breaks', 'Overtime', 'Type', 'Compliance', 'Notes')
        self.time_tree = ttk.Treeview(tree_container, columns=time_columns, show='headings', height=12)

        # Updated column widths for new data
        time_widths = {
            'Date': 80, 
            'Time Periods': 150,  # Shows start-end time ranges (e.g., "09:00-12:00, 13:00-17:00")
            'Present': 70,        # total_time_present
            'Worked': 60,         # hours_worked  
            'Breaks': 60,         # total_break_time
            'Overtime': 60,       # overtime_hours
            'Type': 60,           # record_type
            'Compliance': 100,    # Break/Working time compliance status
            'Notes': 120          # notes
        }

        for col in time_columns:
            self.time_tree.heading(col, text=col)
            self.time_tree.column(col, width=time_widths.get(col, 100))

        # Scrollbars for the treeview
        time_v_scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.time_tree.yview)
        time_h_scrollbar = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.time_tree.xview)
        self.time_tree.configure(yscrollcommand=time_v_scrollbar.set, xscrollcommand=time_h_scrollbar.set)

        # Grid layout for treeview and scrollbars
        self.time_tree.grid(row=0, column=0, sticky='nsew')
        time_v_scrollbar.grid(row=0, column=1, sticky='ns')
        time_h_scrollbar.grid(row=1, column=0, sticky='ew')

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Time records buttons
        time_btn_frame = ttk.Frame(records_frame)
        time_btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(time_btn_frame, width=18, text="Edit Selected", command=self.edit_time_entry).pack(side=tk.TOP, padx=5, pady=2, anchor=tk.E)
        ttk.Button(time_btn_frame, width=18, text="Delete Selected", command=self.delete_time_entry).pack(side=tk.TOP, padx=5, pady=2, anchor=tk.E)
        ttk.Button(time_btn_frame, width=18, text="View Details", command=self.view_time_details).pack(side=tk.TOP, padx=5, pady=2, anchor=tk.E)
        ttk.Button(time_btn_frame, width=18, text="Refresh Records", command=self.load_month_data).pack(side=tk.TOP, padx=5, pady=2, anchor=tk.E)

        # Bind events
        for widget in [self.day_spin, self.month_spin, self.year_spin]:
            widget.bind('<FocusOut>', lambda e: self.update_date_display())
            widget.bind('<KeyRelease>', lambda e: self.root.after(100, self.update_date_display))

        # Bind double-click to edit
        self.time_tree.bind('<Double-1>', lambda e: self.edit_time_entry())

        self.update_employee_combo()

    def preview_time_calculation(self):
        """Preview time calculation before adding entry"""
        if self.type_var.get() != 'work':
            self.update_preview_text("Non-work entries don't require time calculation.")
            return

        # Get time entries
        start_times = [var.get().strip() for var in self.start_time_vars if var.get().strip()]
        end_times = [var.get().strip() for var in self.end_time_vars if var.get().strip()]

        if not start_times or not end_times or len(start_times) != len(end_times):
            self.update_preview_text("Please enter matching start and end times.")
            return

        try:
            # Use the time tracker's calculation method
            calculated = self.time_tracker.calculate_time_entry(start_times, end_times)

            preview_text = f"""Time Calculation Preview:
     • Total Time Present: {calculated['total_time_present']:.2f} hours
     • Work Time: {calculated['hours_worked']:.2f} hours  
     • Break Time: {calculated['total_break_time']:.2f} hours
     • Required Break: {calculated['minimum_break_required']:.2f} hours
     • Overtime: {calculated['overtime_hours']:.2f} hours
     • Break Compliance: {'✓' if calculated['break_compliance'] else '✗ Insufficient break'}
     • Working Time Compliance: {'✓' if calculated['max_working_time_compliance'] else '✗ Exceeds 10h limit'}"""

            self.update_preview_text(preview_text)

        except Exception as e:
            self.update_preview_text(f"Error in calculation: {str(e)}")

    def update_preview_text(self, text):
        """Update the preview text widget"""
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, text)
        self.preview_text.config(state=tk.DISABLED)

    def add_time_entry(self):
        """Add time entry for selected employee"""
        if not self.selected_employee:
            messagebox.showwarning("Warning", "Please select an employee first.")
            return

        try:
            # Get date components from form fields
            print("Selecting the date:") #TODO: remove
            day = self.day_var.get()
            month = self.date_month_var.get()
            year = self.date_year_var.get()
            # Create date string in YYYY-MM-DD format
            entry_date = f"{year:04d}-{month:02d}-{day:02d}"
            
            self.start_times = [var.get().strip() for var in self.start_time_vars if var.get().strip()]
            self.end_times = [var.get().strip() for var in self.end_time_vars if var.get().strip()]
            self.clear_time_form()

            print(f"day:\t\t{day}") #TODO: remove
            print(f"month:\t\t{month}") #TODO: remove
            print(f"year:\t\t{year}") #TODO: remove
            print(f"entry_date:\t{entry_date}") #TODO: remove
            # Get time entry data
            hours = self.hours_var.get()
            record_type = self.type_var.get()
            notes = self.notes_var.get()

            print(f"hours\t\t{hours}") #TODO: remove
            print(f"record_type\t\t{record_type}") #TODO: remove
            print(f"notes\t\t{notes}") #TODO: remove

            success, message = self.time_tracker.add_time_record(
                employee_id = self.selected_employee, 
                record_date = entry_date, 
                start_times=self.start_times, 
                end_times=self.end_times,
                record_type=record_type, 
                notes=notes
                )

            if success:
                messagebox.showinfo("Success", message)
                self.load_time_records_data() 
                self.hours_var.set(0.0)
                self.notes_var.set("")
                self.sort_out_time_entries()
            else:
                print("Error!") #TODO: remove
                print(message) #TODO: remove
                messagebox.showerror("Error", message)

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid date or time value: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

    def clear_time_form(self):
        """Clear all time entry form fields"""
        for var in self.start_time_vars + self.end_time_vars:
            var.set("")
        self.notes_var.set("")
        self.type_var.set("work")
        self.update_preview_text("Enter time periods above and click 'Calculate Preview' to see calculations.")

    def edit_time_entry(self):
        """Edit selected time entry"""
        selection = self.time_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a time record to edit.")
            return

        # Get record data
        item = self.time_tree.item(selection[0])
        record_date = item['values'][0]

        employee_id = self.get_selected_employee_id()
        if not employee_id:
            messagebox.showerror("Error", "No employee selected.")
            return

        # Get detailed time information
        details = self.time_tracker.get_daily_time_details(employee_id, record_date)
        if not details:
            messagebox.showerror("Error", "Could not load time entry details.")
            return

        # Populate form with existing data
        start_times = [t for t in details['start_times'] if t]
        end_times = [t for t in details['end_times'] if t]

        # Clear form first
        self.clear_time_form()

        # Set date
        date_parts = record_date.split('-')
        self.date_year_var.set(int(date_parts[0]))
        self.date_month_var.set(int(date_parts[1]))
        self.day_var.set(int(date_parts[2]))

        # Set times
        for i, (start, end) in enumerate(zip(start_times, end_times)):
            if i < 3:  # Max 3 periods
                self.start_time_vars[i].set(start)
                self.end_time_vars[i].set(end)

        # Set other fields
        self.type_var.set(details['record_type'])
        self.notes_var.set(details['notes'] or '')

        # Show preview
        self.preview_time_calculation()

    def get_selected_employee_id(self):
        """Get the ID of the currently selected employee"""
        if not self.emp_var.get():
            return None

        # Extract employee ID from the combo selection (assuming format "Name (ID: xxx)")
        emp_text = self.emp_var.get()
        if "(ID:" in emp_text:
            try:
                emp_id = int(emp_text.split("(ID:")[1].split(")")[0].strip())
                return emp_id
            except (IndexError, ValueError):
                return None
        return None

    def set_to_today(self):
        """Set date fields to today's date"""
        today = date.today()
        self.day_var.set(today.day)
        self.date_month_var.set(today.month)
        self.date_year_var.set(today.year)
        self.update_date_display()

    def create_reports_tab(self):
        """Create reports tab"""
        reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(reports_frame, text="Reports")
        
        # Main container
        main_container = ttk.Frame(reports_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        ttk.Label(main_container, text="Reports & Analytics", style='Title.TLabel').pack(anchor='w', pady=(0, 10))
        
        # Report controls
        controls_frame = ttk.LabelFrame(main_container, text="Report Generation")
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Control row 1
        row1 = ttk.Frame(controls_frame)
        row1.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(row1, text="Employee:").pack(side=tk.LEFT)
        self.report_emp_var = tk.StringVar()
        self.report_emp_combo = ttk.Combobox(row1, textvariable=self.report_emp_var, 
                                            width=30, state="readonly")
        self.report_emp_combo.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row1, text="Report Type:").pack(side=tk.LEFT)
        self.report_type_var = tk.StringVar(value="monthly")
        report_type_combo = ttk.Combobox(row1, textvariable=self.report_type_var,
                                        values=["monthly", "yearly", "custom_period"], 
                                        width=15, state="readonly")
        report_type_combo.pack(side=tk.LEFT, padx=5)
        
        # Control row 2
        row2 = ttk.Frame(controls_frame)
        row2.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(row2, text="Month:").pack(side=tk.LEFT)
        self.report_month_var = tk.IntVar(value=datetime.now().month)
        tk.Spinbox(row2, from_=1, to=12, textvariable=self.report_month_var, width=5).pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(row2, text="Year:").pack(side=tk.LEFT)
        self.report_year_var = tk.IntVar(value=datetime.now().year)
        tk.Spinbox(row2, from_=2020, to=2030, textvariable=self.report_year_var, width=8).pack(side=tk.LEFT, padx=(5, 20))
        
        # Report buttons
        btn_container = ttk.Frame(row2)
        btn_container.pack(side=tk.RIGHT)
        
        ttk.Button(btn_container, text="Generate Report", command=self.not_yet_implemented).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_container, text="Export Report", command=self.not_yet_implemented).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_container, text="Clear", command=self.not_yet_implemented).pack(side=tk.LEFT, padx=5)
        
        # Report display area
        display_frame = ttk.LabelFrame(main_container, text="Report Output")
        display_frame.pack(fill=tk.BOTH, expand=True)
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(display_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.report_text = tk.Text(text_frame, wrap=tk.WORD, font=('Courier', 10))
        report_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.report_text.yview)
        self.report_text.configure(yscrollcommand=report_scroll.set)
        
        self.report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        report_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initialize report employee combo
        self.update_report_employee_combo()
    
    def create_export_tab(self):
        """Create data export tab"""
        export_frame = ttk.Frame(self.notebook)
        self.notebook.add(export_frame, text="Data Export")
        
        # Main container
        main_container = ttk.Frame(export_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        ttk.Label(main_container, text="Data Export", style='Title.TLabel').pack(anchor='w', pady=(0, 20))
        
        # Export options frame
        options_frame = ttk.LabelFrame(main_container, text="Export Options")
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Employee selection for export
        emp_frame = ttk.Frame(options_frame)
        emp_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(emp_frame, text="Select Employees to Export:").pack(anchor='w', pady=(0, 5))
        
        # Listbox for employee selection
        listbox_frame = ttk.Frame(emp_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.export_listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE, height=8)
        export_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.export_listbox.yview)
        self.export_listbox.configure(yscrollcommand=export_scrollbar.set)
        
        self.export_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        export_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Selection buttons
        select_btn_frame = ttk.Frame(emp_frame)
        select_btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        #ttk.Button(select_btn_frame, text="Select All", command=self.select_all_employees).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(select_btn_frame, text="Clear Selection", command=self.clear_employee_selection).pack(side=tk.LEFT, padx=5)
        ttk.Button(select_btn_frame, text="Refresh List", command=self.not_yet_implemented).pack(side=tk.LEFT, padx=5)
        
        # Export settings
        settings_frame = ttk.Frame(options_frame)
        settings_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.include_time_records_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Include Time Records", 
                       variable=self.include_time_records_var).pack(anchor='w')
        
        self.include_inactive_export_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_frame, text="Include Inactive Employees", 
                       variable=self.include_inactive_export_var,
                       command=self.not_yet_implemented).pack(anchor='w')
        
        # Export buttons
        export_btn_frame = ttk.Frame(main_container)
        export_btn_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Button(export_btn_frame, text="Export Selected to JSON", 
                  command=self.not_yet_implemented).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(export_btn_frame, text="Export All to JSON", 
                  command=self.not_yet_implemented).pack(side=tk.LEFT, padx=10)
        ttk.Button(export_btn_frame, text="Preview Export Data", 
                  command=self.not_yet_implemented).pack(side=tk.LEFT, padx=10)
        
        # Export preview/status
        preview_frame = ttk.LabelFrame(main_container, text="Export Preview/Status")
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        self.export_text = tk.Text(preview_frame, wrap=tk.WORD, height=15, font=('Courier', 9))
        export_text_scroll = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.export_text.yview)
        self.export_text.configure(yscrollcommand=export_text_scroll.set)
        
        self.export_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        export_text_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Initialize export employee list
        #self.refresh_export_employee_list()

    def create_settings_tab(self):
        """Create settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")

        # Create scrollable frame for all settings
        canvas = tk.Canvas(settings_frame)
        scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Main container
        main_container = ttk.Frame(scrollable_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(main_container, text="Application Settings", style='Title.TLabel').pack(anchor='w', pady=(0, 20))

        # Database settings
        db_frame = ttk.LabelFrame(main_container, text="Database Settings")
        db_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(db_frame, text="Database Location:").pack(anchor='w', padx=10, pady=(10, 5))
        db_path_frame = ttk.Frame(db_frame)
        db_path_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.db_path_var = tk.StringVar(value=self.db_manager.db_name)
        ttk.Entry(db_path_frame, textvariable=self.db_path_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(db_path_frame, text="Browse", command=self.browse_database).pack(side=tk.RIGHT, padx=(5, 0)) #TODO: implement later!

        # Company Data Settings
        company_frame = ttk.LabelFrame(main_container, text="Company Information")
        company_frame.pack(fill=tk.X, pady=(0, 20))

        # Company data grid
        company_grid = ttk.Frame(company_frame)
        company_grid.pack(padx=10, pady=10, fill=tk.X)

        # Configure grid weights for proper resizing
        company_grid.columnconfigure(1, weight=1)
        company_grid.columnconfigure(3, weight=1)

        # Company name
        ttk.Label(company_grid, text="Company Name:").grid(row=0, column=0, sticky='w', pady=2)
        self.company_name_var = tk.StringVar(value="Meine Firma GmbH")
        ttk.Entry(company_grid, textvariable=self.company_name_var, width=25).grid(row=0, column=1, sticky='ew', padx=(5, 20), pady=2)

        # Company email
        ttk.Label(company_grid, text="Email:").grid(row=0, column=2, sticky='w', pady=2)
        self.company_email_var = tk.StringVar(value="contact@meinefirma.com")
        ttk.Entry(company_grid, textvariable=self.company_email_var, width=25).grid(row=0, column=3, sticky='ew', padx=5, pady=2)

        # Company street
        ttk.Label(company_grid, text="Street Address:").grid(row=1, column=0, sticky='w', pady=2)
        self.company_street_var = tk.StringVar(value="Geschäftsstraße 123")
        ttk.Entry(company_grid, textvariable=self.company_street_var, width=25).grid(row=1, column=1, sticky='ew', padx=(5, 20), pady=2)

        # Company phone
        ttk.Label(company_grid, text="Phone:").grid(row=1, column=2, sticky='w', pady=2)
        self.company_phone_var = tk.StringVar(value="+49-30-1234567")
        ttk.Entry(company_grid, textvariable=self.company_phone_var, width=25).grid(row=1, column=3, sticky='ew', padx=5, pady=2)

        # Company city
        ttk.Label(company_grid, text="City:").grid(row=2, column=0, sticky='w', pady=2)
        self.company_city_var = tk.StringVar(value="10115 Berlin")
        ttk.Entry(company_grid, textvariable=self.company_city_var, width=25).grid(row=2, column=1, sticky='ew', padx=(5, 20), pady=2)

        # Company colors section
        ttk.Label(company_grid, text="Brand Colors:", font=('TkDefaultFont', 9, 'bold')).grid(row=3, column=0, sticky='w', pady=(15, 5))

        # Color 1
        ttk.Label(company_grid, text="Primary Color:").grid(row=4, column=0, sticky='w', pady=2)
        color1_frame = ttk.Frame(company_grid)
        color1_frame.grid(row=4, column=1, sticky='ew', padx=(5, 20), pady=2)
        self.company_color1_var = tk.StringVar(value="#1E40AF")
        ttk.Entry(color1_frame, textvariable=self.company_color1_var, width=10).pack(side=tk.LEFT)
        self.color1_preview = tk.Label(color1_frame, text="  ", bg="#1E40AF", width=3, relief="solid", borderwidth=1)
        self.color1_preview.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(color1_frame, text="Pick", command=lambda: self.pick_color(self.company_color1_var, self.color1_preview)).pack(side=tk.LEFT, padx=(5, 0))

        # Color 2
        ttk.Label(company_grid, text="Secondary Color:").grid(row=4, column=2, sticky='w', pady=2)
        color2_frame = ttk.Frame(company_grid)
        color2_frame.grid(row=4, column=3, sticky='ew', padx=5, pady=2)
        self.company_color2_var = tk.StringVar(value="#3B82F6")
        ttk.Entry(color2_frame, textvariable=self.company_color2_var, width=10).pack(side=tk.LEFT)
        self.color2_preview = tk.Label(color2_frame, text="  ", bg="#3B82F6", width=3, relief="solid", borderwidth=1)
        self.color2_preview.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(color2_frame, text="Pick", command=lambda: self.pick_color(self.company_color2_var, self.color2_preview)).pack(side=tk.LEFT, padx=(5, 0))

        # Color 3
        ttk.Label(company_grid, text="Accent Color:").grid(row=5, column=0, sticky='w', pady=2)
        color3_frame = ttk.Frame(company_grid)
        color3_frame.grid(row=5, column=1, sticky='ew', padx=(5, 20), pady=2)
        self.company_color3_var = tk.StringVar(value="#93C5FD")
        ttk.Entry(color3_frame, textvariable=self.company_color3_var, width=10).pack(side=tk.LEFT)
        self.color3_preview = tk.Label(color3_frame, text="  ", bg="#93C5FD", width=3, relief="solid", borderwidth=1)
        self.color3_preview.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(color3_frame, text="Pick", command=lambda: self.pick_color(self.company_color3_var, self.color3_preview)).pack(side=tk.LEFT, padx=(5, 0))

        # Template Generation Settings
        template_frame = ttk.LabelFrame(main_container, text="Template Generation")
        template_frame.pack(fill=tk.X, pady=(0, 20))

        # Template settings grid
        template_grid = ttk.Frame(template_frame)
        template_grid.pack(padx=10, pady=10, fill=tk.X)

        # Language selection
        ttk.Label(template_grid, text="Language:").grid(row=0, column=0, sticky='w', pady=2)
        self.template_lang_var = tk.StringVar(value="en")
        lang_combobox = ttk.Combobox(template_grid, textvariable=self.template_lang_var, 
                                   values=["en", "de"], width=8, state="readonly")
        lang_combobox.grid(row=0, column=1, sticky='w', padx=(5, 20), pady=2)

        # Template style selection
        ttk.Label(template_grid, text="Template Style:").grid(row=0, column=2, sticky='w', pady=2)
        self.template_style_var = tk.StringVar(value="color")
        style_combobox = ttk.Combobox(template_grid, textvariable=self.template_style_var, 
                                     values=["color", "black-white"], width=12, state="readonly")
        style_combobox.grid(row=0, column=3, sticky='w', padx=5, pady=2)

        # Output path selection 
        ttk.Label(template_grid, text="Default Output Path:").grid(row=2, column=0, sticky='w', pady=(10, 2))

        output_path_frame = ttk.Frame(template_grid)
        output_path_frame.grid(row=2, column=1, columnspan=3, sticky='ew', pady=(15, 2))

        self.output_path_var = tk.StringVar(value=os.path.expanduser("~/Documents"))
        ttk.Entry(output_path_frame, textvariable=self.output_path_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_path_frame, text="Browse", command=self.browse_output_path).pack(side=tk.RIGHT, padx=(5, 0))

        # Default settings
        defaults_frame = ttk.LabelFrame(main_container, text="Default Settings")
        defaults_frame.pack(fill=tk.X, pady=(0, 20))

        # Settings grid
        settings_grid = ttk.Frame(defaults_frame)
        settings_grid.pack(padx=10, pady=10)

        ttk.Label(settings_grid, text="Standard Hours per Day:").grid(row=0, column=0, sticky='w', pady=2)
        self.std_hours_var = tk.DoubleVar(value=8.0)
        ttk.Entry(settings_grid, textvariable=self.std_hours_var, width=10).grid(row=0, column=1, padx=(5, 20), pady=2)

        ttk.Label(settings_grid, text="Default Vacation Days:").grid(row=0, column=2, sticky='w', pady=2)
        self.default_vacation_var = tk.IntVar(value=20)
        ttk.Entry(settings_grid, textvariable=self.default_vacation_var, width=10).grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(settings_grid, text="Overtime Threshold (hours/week):").grid(row=1, column=0, sticky='w', pady=2)
        self.overtime_threshold_var = tk.DoubleVar(value=40.0)
        ttk.Entry(settings_grid, textvariable=self.overtime_threshold_var, width=10).grid(row=1, column=1, padx=(5, 20), pady=2)

        ttk.Label(settings_grid, text="Default Sick Days:").grid(row=1, column=2, sticky='w', pady=2)
        self.default_sick_var = tk.IntVar(value=10)
        ttk.Entry(settings_grid, textvariable=self.default_sick_var, width=10).grid(row=1, column=3, padx=5, pady=2)

        # Settings buttons
        settings_btn_frame = ttk.Frame(main_container)
        settings_btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(settings_btn_frame, text="Save Settings", command=self.save_settings).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(settings_btn_frame, text="Reset to Defaults", command=self.reset_settings).pack(side=tk.LEFT)
        ttk.Button(settings_btn_frame, text="Load Settings", command=self.load_settings).pack(side=tk.LEFT, padx=(10, 0))
        self.load_settings()

    def pick_color(self, color_var, preview_label):
        """Open color picker dialog"""
        try:
            from tkinter import colorchooser
            current_color = color_var.get()
            color = colorchooser.askcolor(initialcolor=current_color, title="Choose Color")
            if color[1]:  # If user didn't cancel
                color_var.set(color[1])
                preview_label.config(bg=color[1])
        except Exception as e:
            print(f"Color picker error: {e}")

    def save_settings(self):
        """Save all settings to database using SettingsManager"""
        try:
            # Collect general settings from GUI
            general_settings = {
                'standard_hours_per_day': self.std_hours_var.get(),
                'overtime_threshold': self.overtime_threshold_var.get(),
                'vacation_days_per_year': self.default_vacation_var.get(),
                'sick_days_per_year': self.default_sick_var.get(),
                'business_days_per_week': 5 
            }

            # Collect company data from GUI
            company_data = {
                'companyname': self.company_name_var.get(),
                'companystreet': self.company_street_var.get(),
                'companycity': self.company_city_var.get(),
                'companyphone': self.company_phone_var.get(),
                'companyemail': self.company_email_var.get(),
                'company_color_1': self.company_color1_var.get(),
                'company_color_2': self.company_color2_var.get(),
                'company_color_3': self.company_color3_var.get()
            }

            # Collect report settings from GUI
            report_settings = {
                'lang': self.template_lang_var.get(),
                'template': self.template_style_var.get(),
                'default_output_path': self.output_path_var.get()
            }

            # Save all settings
            if self.settings_manager.save_all_settings(general_settings, company_data, report_settings):
                print("Settings saved successfully!")
            else:
                print("Error saving settings!")

        except Exception as e:
            print(f"Error in save_settings: {e}")

    def load_settings(self):
        """Load settings from database using SettingsManager"""
        try:
            # Load all settings
            all_settings = self.settings_manager.load_all_settings()

            # Update general settings in GUI
            general = all_settings.get('general', {})
            self.std_hours_var.set(general.get('standard_hours_per_day', 8.0))
            self.overtime_threshold_var.set(general.get('overtime_threshold', 200.0))
            self.default_vacation_var.set(general.get('vacation_days_per_year', 30))
            self.default_sick_var.set(general.get('sick_days_per_year', 10))

            # Update company data in GUI
            company = all_settings.get('company', {})
            self.company_name_var.set(company.get('companyname', 'Meine Firma GmbH'))
            self.company_street_var.set(company.get('companystreet', 'Geschäftsstraße 123'))
            self.company_city_var.set(company.get('companycity', '10115 Berlin'))
            self.company_phone_var.set(company.get('companyphone', '+49-30-1234567'))
            self.company_email_var.set(company.get('companyemail', 'contact@meinefirma.com'))

            # Update company colors
            color1 = company.get('company_color_1', '#1E40AF')
            color2 = company.get('company_color_2', '#3B82F6')
            color3 = company.get('company_color_3', '#93C5FD')

            self.company_color1_var.set(color1)
            self.company_color2_var.set(color2)
            self.company_color3_var.set(color3)

            # Update color previews
            self.color1_preview.config(bg=color1)
            self.color2_preview.config(bg=color2)
            self.color3_preview.config(bg=color3)

            # Update report settings in GUI
            report = all_settings.get('report', {})
            self.template_lang_var.set(report.get('lang', 'en'))
            self.template_style_var.set(report.get('template', 'color'))
            self.output_path_var.set(report.get('default_output_path', './reports/'))

            print("Settings loaded successfully!")

        except Exception as e:
            print(f"Error loading settings: {e}")

    def reset_settings(self):
        """Reset all settings to defaults using SettingsManager"""

        # First ask for confirmation
        if not messagebox.askyesno(
            "Confirm Reset", 
            "Are you sure you want to reset all settings to their default values?\n\n"
            "This will reset:\n"
            "• General application settings\n"
            "• Company information\n"
            "• Report generation settings\n\n"
            "This action cannot be undone!"
        ):
            return  # User cancelled, do nothing

        try:
            if self.settings_manager.reset_to_defaults():
                # After resetting in database, load the defaults into the GUI
                self.load_settings()
                print("Settings reset to defaults!")
                messagebox.showinfo("Success", "All settings have been reset to their default values!")
            else:
                print("Error resetting settings!")
                messagebox.showerror("Error", "Failed to reset settings to defaults!")

        except Exception as e:
            print(f"Error in reset_settings: {e}")
            messagebox.showerror("Error", f"Failed to reset settings: {e}")
    
    def open_calendar(self):
        """Open calendar popup for date selection"""
        try:
            initial_date = date(self.year_var.get(), self.month_var.get(), self.day_var.get())
        except ValueError:
            initial_date = date.today()
        
        calendar_dialog = CalendarDialog(self.root, initial_date)
        selected_date = calendar_dialog.show()
        
        if selected_date:
            self.day_var.set(selected_date.day)
            self.month_var.set(selected_date.month)
            self.year_var.set(selected_date.year)
            self.update_date_display()

    def create_employee_details_tab(self):
        """Create a tab to display detailed employee information"""
        details_frame = ttk.Frame(self.notebook)
        self.notebook.add(details_frame, text="Employee Details")

        # Main container frame
        container = ttk.Frame(details_frame)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Employee selection
        selection_frame = ttk.Frame(container)
        selection_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(selection_frame, text="Select Employee:").pack(side=tk.LEFT)
        self.details_emp_var = tk.StringVar()
        self.details_emp_combo = ttk.Combobox(
            selection_frame, 
            textvariable=self.details_emp_var, 
            width=30,
            state='readonly'
        )
        self.details_emp_combo.pack(side=tk.LEFT, padx=5)
        self.details_emp_combo.bind('<<ComboboxSelected>>', self.load_employee_details)

        # Refresh button
        ttk.Button(
            selection_frame, 
            text="Refresh", 
            command=self.update_details_combo
        ).pack(side=tk.LEFT, padx=5)

        # Details display notebook
        details_notebook = ttk.Notebook(container)
        details_notebook.pack(fill=tk.BOTH, expand=True)

        # Personal Info Tab
        personal_frame = ttk.Frame(details_notebook)
        details_notebook.add(personal_frame, text="Personal Info")

        # Create labels for personal info
        self.personal_info_labels = {
            'Name': ttk.Label(personal_frame, text="Name:"),
            'Employee ID': ttk.Label(personal_frame, text="Employee ID:"),
            'Position': ttk.Label(personal_frame, text="Position:"),
            'Hourly Rate': ttk.Label(personal_frame, text="Hourly Rate:"),
            'Email': ttk.Label(personal_frame, text="Email:"),
            'Hire Date': ttk.Label(personal_frame, text="Hire Date:"),
            'Status': ttk.Label(personal_frame, text="Status:")
        }

        # Corresponding value labels
        self.personal_info_values = {
            'Name': ttk.Label(personal_frame, text="", foreground='blue'),
            'Employee ID': ttk.Label(personal_frame, text="", foreground='blue'),
            'Position': ttk.Label(personal_frame, text="", foreground='blue'),
            'Hourly Rate': ttk.Label(personal_frame, text="", foreground='blue'),
            'Email': ttk.Label(personal_frame, text="", foreground='blue'),
            'Hire Date': ttk.Label(personal_frame, text="", foreground='blue'),
            'Status': ttk.Label(personal_frame, text="", foreground='blue')
        }

        # Grid layout for personal info
        for i, (key, label) in enumerate(self.personal_info_labels.items()):
            label.grid(row=i, column=0, sticky='w', padx=5, pady=5)
            self.personal_info_values[key].grid(row=i, column=1, sticky='w', padx=5, pady=5)

        # Work Details Tab
        work_frame = ttk.Frame(details_notebook)
        details_notebook.add(work_frame, text="Work Details")

        # Work details labels
        self.work_info_labels = {
            'Hours/Week': ttk.Label(work_frame, text="Hours/Week:"),
            'Vacation Days/Year': ttk.Label(work_frame, text="Vacation Days/Year:"),
            'Sick Days/Year': ttk.Label(work_frame, text="Sick Days/Year:"),
            'Vacation Days Remaining': ttk.Label(work_frame, text="Vacation Days Remaining:"),
            'Sick Days Remaining': ttk.Label(work_frame, text="Sick Days Remaining:")
        }

        # Work details values
        self.work_info_values = {
            'Hours/Week': ttk.Label(work_frame, text="", foreground='blue'),
            'Vacation Days/Year': ttk.Label(work_frame, text="", foreground='blue'),
            'Sick Days/Year': ttk.Label(work_frame, text="", foreground='blue'),
            'Vacation Days Remaining': ttk.Label(work_frame, text="", foreground='blue'),
            'Sick Days Remaining': ttk.Label(work_frame, text="", foreground='blue')
        }

        # Grid layout for work info
        for i, (key, label) in enumerate(self.work_info_labels.items()):
            label.grid(row=i, column=0, sticky='w', padx=5, pady=5)
            self.work_info_values[key].grid(row=i, column=1, sticky='w', padx=5, pady=5)

        # Stats Tab
        stats_frame = ttk.Frame(details_notebook)
        details_notebook.add(stats_frame, text="Statistics")

        # Current month/year
        current_month = datetime.now().month
        current_year = datetime.now().year

        # Stats labels
        self.stats_labels = {
            'Current Month': ttk.Label(stats_frame, text=f"{calendar.month_name[current_month]} {current_year}:"),
            'Work Hours': ttk.Label(stats_frame, text="Work Hours:"),
            'Overtime': ttk.Label(stats_frame, text="Overtime:"),
            'Vacation Days': ttk.Label(stats_frame, text="Vacation Days:"),
            'Sick Days': ttk.Label(stats_frame, text="Sick Days:"),
            'YTD Work Hours': ttk.Label(stats_frame, text="YTD Work Hours:"),
            'YTD Overtime': ttk.Label(stats_frame, text="YTD Overtime:")
        }

        # Stats values
        self.stats_values = {
            'Work Hours': ttk.Label(stats_frame, text="", foreground='blue'),
            'Overtime': ttk.Label(stats_frame, text="", foreground='blue'),
            'Vacation Days': ttk.Label(stats_frame, text="", foreground='blue'),
            'Sick Days': ttk.Label(stats_frame, text="", foreground='blue'),
            'YTD Work Hours': ttk.Label(stats_frame, text="", foreground='blue'),
            'YTD Overtime': ttk.Label(stats_frame, text="", foreground='blue')
        }

        # Grid layout for stats
        self.stats_labels['Current Month'].grid(row=0, column=0, sticky='w', padx=5, pady=5)
        for i, (key, label) in enumerate(self.stats_labels.items()):
            if key != 'Current Month':
                label.grid(row=i, column=0, sticky='w', padx=5, pady=5)
                self.stats_values[key].grid(row=i, column=1, sticky='w', padx=5, pady=5)

        # Initialize the combo box
        self.update_details_combo()

    def create_employee_details_window(self):
        """Create a standalone window to display details of the selected employee"""
        # Get selected employee
        selection = self.emp_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an employee first.")
            return

        item = self.emp_tree.item(selection[0])
        employee_id = item['values'][0] 

        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees WHERE employee_id = ?", (employee_id,))
        employee = cursor.fetchone()
        conn.close()

        if not employee:
            messagebox.showerror("Error", "Selected employee not found in database")
            return

        details_window = tk.Toplevel(self.root)
        details_window.title(f"Employee Details - {employee[1]} ({employee[2]})")
        details_window.geometry("500x450")
        details_window.transient(self.root)
        details_window.grab_set()

        details_window.protocol("WM_DELETE_WINDOW", details_window.destroy)

        container = ttk.Frame(details_window)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        header_frame = ttk.Frame(container)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, 
                 text=f"{employee[1]} ({employee[2]})", 
                 font=('Arial', 12, 'bold')).pack(side=tk.LEFT)

        ttk.Button(
            header_frame,
            text="Close",
            command=details_window.destroy
        ).pack(side=tk.RIGHT)

        details_notebook = ttk.Notebook(container)
        details_notebook.pack(fill=tk.BOTH, expand=True)

        personal_frame = ttk.Frame(details_notebook)
        details_notebook.add(personal_frame, text="Personal Info")

        personal_info = [
            ("Name:", employee[1]),
            ("Employee ID:", employee[2]),
            ("Position:", employee[3] if employee[3] else "N/A"),
            ("Hourly Rate:", f"${employee[4]:.2f}" if employee[4] else "N/A"),
            ("Email:", employee[5] if employee[5] else "N/A"),
            ("Hire Date:", employee[6] if employee[6] else "N/A"),
            ("Status:", "Active" if employee[10] else "Inactive")
        ]

        for row, (label, value) in enumerate(personal_info):
            ttk.Label(personal_frame, text=label).grid(row=row, column=0, sticky='w', padx=5, pady=5)
            ttk.Label(personal_frame, text=value, foreground='blue').grid(row=row, column=1, sticky='w', padx=5, pady=5)

        work_frame = ttk.Frame(details_notebook)
        details_notebook.add(work_frame, text="Work Details")

        current_year = datetime.now().year
        start_of_year = date(current_year, 1, 1)

        conn = self.db_manager.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) FROM time_records 
            WHERE employee_id = ? AND date >= ? AND record_type = 'vacation'
        ''', (employee[0], start_of_year))
        vacation_used = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM time_records 
            WHERE employee_id = ? AND date >= ? AND record_type = 'sick'
        ''', (employee[0], start_of_year))
        sick_used = cursor.fetchone()[0]
        conn.close()

        vacation_remaining = max(0, (employee[8] if len(employee) > 8 else 20)) - vacation_used
        sick_remaining = max(0, (employee[9] if len(employee) > 9 else 10) - sick_used)

        work_info = [
            ("Hours/Week:", f"{employee[7]:.1f}" if len(employee) > 7 else "40.0"),
            ("Vacation Days/Year:", str(employee[8]) if len(employee) > 8 else "20"),
            ("Sick Days/Year:", str(employee[9]) if len(employee) > 9 else "10"),
            ("Vacation Days Remaining:", f"{vacation_remaining}"),
            ("Sick Days Remaining:", f"{sick_remaining}")
        ]

        for row, (label, value) in enumerate(work_info):
            ttk.Label(work_frame, text=label).grid(row=row, column=0, sticky='w', padx=5, pady=5)
            ttk.Label(work_frame, text=value, foreground='blue').grid(row=row, column=1, sticky='w', padx=5, pady=5)

        stats_frame = ttk.Frame(details_notebook)
        details_notebook.add(stats_frame, text="Statistics")

        current_month = datetime.now().month
        monthly_summary = self.time_tracker.calculate_monthly_summary(employee[0], current_year, current_month)
        yearly_summary = self.time_tracker.calculate_yearly_summary(employee[0], current_year)

        stats_info = [
            (f"{calendar.month_name[current_month]} {current_year}:", ""),
            ("Work Hours:", f"{monthly_summary['total_work_hours']:.1f}"),
            ("Overtime:", f"{monthly_summary['total_overtime']:.1f}"),
            ("Vacation Days:", str(monthly_summary['vacation_days'])),
            ("Sick Days:", str(monthly_summary['sick_days'])),
            ("YTD Work Hours:", f"{yearly_summary['total_work_hours']:.1f}"),
            ("YTD Overtime:", f"{yearly_summary['total_overtime']:.1f}")
        ]

        for row, (label, value) in enumerate(stats_info):
            ttk.Label(stats_frame, text=label).grid(row=row, column=0, sticky='w', padx=5, pady=5)
            if value:  # Skip empty value for header row
                ttk.Label(stats_frame, text=value, foreground='blue').grid(row=row, column=1, sticky='w', padx=5, pady=5)

  # =============================================================================
  # HELPER METHODS
  # =============================================================================

    def update_date_display(self):
        """Update the displayed date and store it in self.date_var (YYYY-MM-DD)"""
        try:
            # Check if required variables exist
            if not all(hasattr(self, var) for var in ['day_var', 'date_month_var', 'date_year_var']):
                return

            day = self.day_var.get()
            month = self.date_month_var.get()
            year = self.date_year_var.get()

            # Validate date (basic check)
            if not (1 <= day <= 31 and 1 <= month <= 12 and year >= 2020):
                raise ValueError("Invalid date range")

            # Format as YYYY-MM-DD
            formatted_date = f"{year:04d}-{month:02d}-{day:02d}"

            # Update variables if they exist
            if hasattr(self, 'date_var'):
                self.date_var.set(formatted_date)
            if hasattr(self, 'date_display_var'):
                self.date_display_var.set(formatted_date)

        except (ValueError, AttributeError, tk.TclError):
            # Fallback for invalid dates
            if hasattr(self, 'date_display_var'):
                self.date_display_var.set("Invalid date")
            if hasattr(self, 'date_var'):
                self.date_var.set("")

    def _get_selected_employee_db_id(self):
        """Helper method to get database ID of selected employee"""
        try:
            selection = self.emp_tree.selection()
            if not selection:
                return None

            item = self.emp_tree.item(selection[0])

            print("Treeview item values:", item['values'])  # For debugging TODO: remove

            if not item['values'] or len(item['values']) < 1:
                return None

            displayed_id = item['values'][0] 

            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT id FROM employees WHERE employee_id = ?", (displayed_id,))
                result = cursor.fetchone()

                if not result:
                    try:
                        cursor.execute("SELECT id FROM employees WHERE id = ?", (int(displayed_id),))
                        result = cursor.fetchone()
                    except (ValueError, TypeError):
                        pass

                if not result:
                    print(f"Employee with ID {displayed_id} not found in database")
                    return None

                return result[0]

            finally:
                conn.close()

        except Exception as e:
            print(f"Error in _get_selected_employee_db_id: {str(e)}")
            return None

    # def load_time_records(self, employee_id=None, month=None, year=None):
    #     """Load time records for the selected employee and period into the Treeview"""
    #     # Clear existing records
    #     self.time_tree.delete(*self.time_tree.get_children())

    #     # Use current selection if no parameters provided
    #     employee_id = employee_id or self.selected_employee
    #     month = month or self.month_var.get()
    #     year = year or self.year_var.get()

    #     if not employee_id:
    #         return

    #     try:
    #         conn = self.db_manager.get_connection()
    #         cursor = conn.cursor()

    #         # Get records for the selected month/year
    #         cursor.execute('''
    #             SELECT date, hours_worked, overtime_hours, record_type, notes 
    #             FROM time_records 
    #             WHERE employee_id = ? 
    #             AND strftime('%m', date) = ? 
    #             AND strftime('%Y', date) = ?
    #             ORDER BY date
    #         ''', (employee_id, f"{month:02d}", str(year)))

    #         records = cursor.fetchall()

    #         # Insert records into the Treeview
    #         for record in records:
    #             self.time_tree.insert('', 'end', values=(
    #                 record[0],  # Date
    #                 f"{record[1]:.2f}",  # Hours worked
    #                 f"{record[2]:.2f}" if record[2] else "0.00",  # Overtime
    #                 record[3].capitalize(),  # Type
    #                 record[4]  # Notes
    #             ))

    #     except Exception as e:
    #         messagebox.showerror("Database Error", f"Could not load time records: {str(e)}")
    #     finally:
    #         conn.close()

    def sort_out_time_entries(self):
        """Check all entries for current employee/month and consolidate duplicates"""
        if not self.selected_employee:
            messagebox.showwarning("Warning", "Please select an employee first")
            return

        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            month = self.month_var.get()
            year = self.year_var.get()

            # Find duplicate dates for selected employee/month
            cursor.execute('''
                SELECT date, COUNT(*) as count
                FROM time_records
                WHERE employee_id = ?
                  AND strftime('%m', date) = ?
                  AND strftime('%Y', date) = ?
                GROUP BY date
                HAVING count > 1
            ''', (
                self.selected_employee,
                f"{month:02d}",  # Ensure 2-digit month
                str(year)
            ))

            duplicate_dates = cursor.fetchall()

            if not duplicate_dates:
                return  # Silent return - no duplicates found

            processed_count = 0

            for dup_date, dup_count in duplicate_dates:
                # Get all entries for this duplicate date sorted by priority
                cursor.execute('''
                    SELECT id, hours_worked, overtime_hours, record_type, notes
                    FROM time_records
                    WHERE employee_id = ? AND date = ?
                    ORDER BY CASE record_type
                        WHEN 'work' THEN 1
                        WHEN 'holiday' THEN 2
                        WHEN 'sick' THEN 3
                        WHEN 'vacation' THEN 4
                        ELSE 5
                    END
                ''', (self.selected_employee, dup_date))

                entries = cursor.fetchall()
                keep_type = entries[0][3]  # Highest priority type

                # Combine only same-type entries
                total_hours = sum(e[1] for e in entries if e[3] == keep_type)
                total_overtime = sum(e[2] for e in entries if e[3] == keep_type)
                combined_notes = " | ".join(e[4] for e in entries if e[4] and e[3] == keep_type)

                # Delete old entries
                cursor.execute('''
                    DELETE FROM time_records
                    WHERE employee_id = ? AND date = ?
                ''', (self.selected_employee, dup_date))

                # Insert consolidated entry
                cursor.execute('''
                    INSERT INTO time_records
                    (employee_id, date, hours_worked, overtime_hours, record_type, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    self.selected_employee,
                    dup_date,
                    total_hours,
                    total_overtime,
                    keep_type,
                    combined_notes
                ))

                processed_count += 1

            conn.commit()

            if processed_count > 0:
                messagebox.showinfo(
                    "Duplicates Consolidated",
                    f"Processed {processed_count} dates with multiple entries"
                )
                self.load_time_records_data()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process duplicates: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def not_yet_implemented(self):#TODO: Remove!
        """TODO Remove later, here just to patch up the missing functionality"""
        messagebox.showinfo("Info", "functionality to be implemented....")

    def update_period_display(self):
        """Update the period display label"""
        self.period_display_var.set(f"Viewing: {self.date_manager.view_month:02d}/{self.date_manager.view_year}")

    def update_view_period_if_needed(self):
        """Update view period if the selected date is in a different month/year"""
        selected_date = self.date_manager.selected_date
        if (selected_date.month != self.date_manager.view_month or 
            selected_date.year != self.date_manager.view_year):
            
            self.date_manager.set_view_period(selected_date.month, selected_date.year)
            self.update_period_display()
            if self.selected_employee:
                self.load_time_records_data()

    def on_date_component_change(self, *args):
        """Handle changes to date component spinboxes"""
        try:
            day = self.day_var.get()
            month = self.month_var.get()
            year = self.year_var.get()
            
            success, error_msg = self.date_manager.set_date_components(day, month, year)
            if success:
                self.update_date_display()
                self.update_view_period_if_needed()
            else:
                # Show error but don't crash
                self.date_display_var.set(f"Invalid date: {error_msg}")
        except tk.TclError:
            # Handle spinbox in transition state
            pass

    def set_to_today(self):
        """Set the selected date to today"""
        self.date_manager.reset_to_today()
        day, month, year = self.date_manager.get_date_components()
        
        # Update UI variables without triggering events
        self.day_var.set(day)
        self.month_var.set(month)
        self.year_var.set(year)
        
        self.update_date_display()
        self.update_view_period_if_needed()

    def browse_database(self):
        """Open file dialog to select database location"""
        from tkinter import filedialog

        # Open file dialog to select .db file
        file_path = filedialog.asksaveasfilename(
            title="Select Database File",
            defaultextension=".db",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")],
            initialfile=self.db_path_var.get()  # Start with current path if any
        )

        # If user didn't cancel the dialog
        if file_path:
            self.db_path_var.set(file_path)

    def browse_output_path(self):
        """Open directory dialog to select output path for generated PDFs"""
        from tkinter import filedialog

        # Open directory dialog
        dir_path = filedialog.askdirectory(
            title="Select Default Output Directory",
            initialdir=self.output_path_var.get()  # Start with current path if any
        )

        # If user didn't cancel the dialog
        if dir_path:
            self.output_path_var.set(dir_path)

    def load_time_records_data(self):
        """Load time records data from database and populate the treeview"""
        print("=== load_time_records_data STARTED ===")

        # Check if emp_var exists and has a value
        if not hasattr(self, 'emp_var'):
            print("ERROR: emp_var attribute does not exist!")
            return

        emp_display_name = self.emp_var.get()
        print(f"Employee selected (raw): '{emp_display_name}'")

        if not emp_display_name:
            print("ERROR: No employee selected!")
            return

        # Extract just the name part before the parentheses
        # e.g., "Max Musterman (0001)" -> "Max Musterman"
        if '(' in emp_display_name:
            emp_name = emp_display_name.split('(')[0].strip()
        else:
            emp_name = emp_display_name.strip()
        
        print(f"Employee name extracted: '{emp_name}'")

        # Clear existing data
        current_items = self.time_tree.get_children()
        print(f"Clearing {len(current_items)} existing items from tree")
        for item in current_items:
            self.time_tree.delete(item)

        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            # Get employee ID
            print(f"Looking up employee ID for: {emp_name}")
            cursor.execute("SELECT id FROM employees WHERE name = ?", (emp_name,))
            emp_result = cursor.fetchone()
            if not emp_result:
                print(f"ERROR: Employee '{emp_name}' not found in database!")
                return

            employee_id = emp_result[0]
            print(f"Found employee ID: {employee_id}")

            # Check date manager values
            print(f"Date manager - Year: {self.date_manager.view_year}, Month: {self.date_manager.view_month}")

            # Get time records for the selected month/year
            query_params = (employee_id, str(self.date_manager.view_year), f"{self.date_manager.view_month:02d}")
            print(f"Query parameters: {query_params}")

            cursor.execute("""
                SELECT date, 
                       start_time_1, end_time_1,
                       start_time_2, end_time_2, 
                       start_time_3, end_time_3,
                       total_time_present, hours_worked, total_break_time, 
                       overtime_hours, record_type, notes,
                       break_compliance, max_working_time_compliance,
                       minimum_break_required, break_deficit
                FROM time_records 
                WHERE employee_id = ? 
                AND strftime('%Y', date) = ? 
                AND strftime('%m', date) = ?
                ORDER BY date
            """, query_params)

            records = cursor.fetchall()
            print(f"Found {len(records)} records in database")

            for i, record in enumerate(records):
                print(f"Processing record {i+1}: {record[0]}")  # Just print the date

                (date, start1, end1, start2, end2, start3, end3, 
                 total_present, worked, breaks, overtime, rec_type, notes,
                 break_comp, work_time_comp, min_break_req, break_def) = record

                # Format date
                from datetime import datetime
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%d.%m')

                # Format time periods
                time_periods = []
                if start1 and end1:
                    time_periods.append(f"{start1}-{end1}")
                if start2 and end2:
                    time_periods.append(f"{start2}-{end2}")
                if start3 and end3:
                    time_periods.append(f"{start3}-{end3}")

                time_periods_str = ", ".join(time_periods) if time_periods else "—"

                # Format hours (show as HH:MM)
                def format_hours(hours):
                    if hours is None or hours == 0:
                        return "—"
                    total_minutes = int(hours * 60)
                    hrs = total_minutes // 60
                    mins = total_minutes % 60
                    return f"{hrs}:{mins:02d}"

                # Format compliance status
                compliance_issues = []
                if not break_comp and break_def and break_def > 0:
                    deficit_mins = int(break_def * 60)
                    compliance_issues.append(f"Break -{deficit_mins}min")
                if not work_time_comp:
                    compliance_issues.append("Work time")

                compliance_str = ", ".join(compliance_issues) if compliance_issues else "✓ OK"

                # Add row to treeview
                values_to_insert = (
                    formatted_date,        # Date
                    time_periods_str,      # Time Periods  
                    format_hours(total_present),  # Present
                    format_hours(worked),         # Worked
                    format_hours(breaks),         # Breaks
                    format_hours(overtime),       # Overtime
                    rec_type.title() if rec_type else "Work",  # Type
                    compliance_str,               # Compliance
                    notes or "—"                  # Notes
                )

                print(f"Inserting into tree: {values_to_insert}")
                self.time_tree.insert('', 'end', values=values_to_insert)

            print(f"Successfully inserted {len(records)} records into treeview")
            conn.close()

        except Exception as e:
            print(f"ERROR in load_time_records_data: {e}")
            import traceback
            traceback.print_exc()
            if hasattr(self, 'messagebox'):
                self.messagebox.showerror("Error", f"Failed to load time records: {str(e)}")

        print("=== load_time_records_data FINISHED ===")
    
    def load_month_data(self):
        """Load time records for the selected month"""
        if not hasattr(self, 'emp_var') or not self.emp_var.get():
            if hasattr(self, 'messagebox'):
                self.messagebox.showwarning("Warning", "Please select an employee first.")
            return

        # Update period display
        self.period_display_var.set(f"Viewing: {self.date_manager.view_month:02d}/{self.date_manager.view_year}")

        # Load the time records data
        self.load_time_records_data()

        if hasattr(self, 'messagebox'):
            self.messagebox.showinfo("Success", f"Loaded data for {self.emp_var.get()} - {self.date_manager.view_month:02d}/{self.date_manager.view_year}")

    def view_time_details(self):
        """Show detailed view of selected time record"""
        selection = self.time_tree.selection()
        if not selection:
            if hasattr(self, 'messagebox'):
                self.messagebox.showwarning("Warning", "Please select a time record to view details.")
            return

        # Get the selected item values
        item = self.time_tree.item(selection[0])
        values = item['values']

        if not values:
            return

        # Create detail window
        detail_window = tk.Toplevel(self.root)
        detail_window.title("Time Record Details")
        detail_window.geometry("450x400")
        detail_window.resizable(False, False)

        # Get full record from database for detailed view
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            # Get employee ID
            cursor.execute("SELECT id FROM employees WHERE name = ?", (self.emp_var.get(),))
            emp_result = cursor.fetchone()
            if not emp_result:
                return

            employee_id = emp_result[0]

            # Convert displayed date back to database format
            displayed_date = values[0]  # DD.MM format
            full_date = f"{self.date_manager.view_year}-{self.date_manager.view_month:02d}-{displayed_date.split('.')[0].zfill(2)}"

            cursor.execute("""
                SELECT * FROM time_records 
                WHERE employee_id = ? AND date = ?
            """, (employee_id, full_date))

            record = cursor.fetchone()
            conn.close()

            if record:
                # Display detailed information
                details_text = tk.Text(detail_window, wrap=tk.WORD, padx=10, pady=10)
                details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                # Format detailed information
                detail_info = f"""Date: {full_date}
        Employee: {self.emp_var.get()}

        Time Periods:
        """
                if record[3] and record[4]:  # start_time_1, end_time_1
                    detail_info += f"  Period 1: {record[3]} - {record[4]}\n"
                if record[5] and record[6]:  # start_time_2, end_time_2
                    detail_info += f"  Period 2: {record[5]} - {record[6]}\n"
                if record[7] and record[8]:  # start_time_3, end_time_3
                    detail_info += f"  Period 3: {record[7]} - {record[8]}\n"

                detail_info += f"""
        Time Summary:
          Total Present: {record[12]:.2f} hours
          Hours Worked: {record[13]:.2f} hours
          Break Time: {record[9]:.2f} hours
          Overtime: {record[14]:.2f} hours

        German Labor Law Compliance:
          Minimum Break Required: {record[10]:.2f} hours
          Break Deficit: {record[11]:.2f} hours
          Break Compliance: {'✓ OK' if record[17] else '✗ Non-compliant'}
          Working Time Compliance: {'✓ OK' if record[18] else '✗ Non-compliant'}

        Record Information:
          Type: {record[15].title() if record[15] else 'Work'}
          Notes: {record[16] if record[16] else 'None'}

        Created: {record[19] if len(record) > 19 else 'N/A'}
        Updated: {record[20] if len(record) > 20 else 'N/A'}
        """

                details_text.insert('1.0', detail_info)
                details_text.config(state=tk.DISABLED)

        except Exception as e:
            if hasattr(self, 'messagebox'):
                self.messagebox.showerror("Error", f"Failed to load record details: {str(e)}")
            detail_window.destroy()

  # =============================================================================
  #  TIME MANAGEMENT METHODS
  # =============================================================================

  # =============================================================================
  # EMPLOYEE MANAGEMENT METHODS
  # =============================================================================

    def refresh_employee_list(self):
        """Refresh the employee list display"""
        # Clear existing items
        for item in self.emp_tree.get_children():
            self.emp_tree.delete(item)
        
        # Get employees
        include_inactive = self.show_inactive_var.get()
        employees = self.employee_manager.get_all_employees(include_inactive=self.show_inactive_var) #TODO: Maybe create a new variable for this
        
        for emp in employees:
            try:
                status = "Active" if emp[10] else "Inactive"  # emp[10] is active column
                self.emp_tree.insert('', 'end', values=(
                    emp[2],    # employee_id
                    emp[1],    # name
                    emp[3] or "",    # position
                    f"${emp[4]:.2f}" if emp[4] else "$0.00",  # hourly_rate
                    f"{emp[7]:.1f}" if emp[7] else "40.0",   # hours_per_week
                    emp[8] if emp[8] else "20",    # vacation_days_per_year
                    emp[5] or "",     # email
                    status
                ))
            except (IndexError, TypeError):
                # Handle any database format issues
                continue
    
    def update_employee_combo(self):
        """Update employee combobox with current employees"""
        employees = self.employee_manager.get_all_employees()
        emp_names = [f"{emp[1]} ({emp[2]})" for emp in employees]
        self.emp_combo['values'] = emp_names
    
    def update_report_employee_combo(self):
        """Update report employee combobox"""
        employees = self.employee_manager.get_all_employees()
        emp_names = ["All Employees"] + [f"{emp[1]} ({emp[2]})" for emp in employees]
        self.report_emp_combo['values'] = emp_names
    
    def add_employee_dialog(self):
        """Show dialog to add new employee with strict ID validation"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Employee")
        dialog.geometry("400x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # Form fields
        ttk.Label(dialog, text="Name:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=30).grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Employee ID (max 4 digits):").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        id_var = tk.StringVar()
        id_entry = ttk.Entry(dialog, textvariable=id_var, width=30)
        id_entry.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Position:").grid(row=2, column=0, sticky='w', padx=10, pady=5)
        pos_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=pos_var, width=30).grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Hourly Rate:").grid(row=3, column=0, sticky='w', padx=10, pady=5)
        rate_var = tk.DoubleVar()
        ttk.Entry(dialog, textvariable=rate_var, width=30).grid(row=3, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Email:").grid(row=4, column=0, sticky='w', padx=10, pady=5)
        email_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=email_var, width=30).grid(row=4, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Hours per Week:").grid(row=5, column=0, sticky='w', padx=10, pady=5)
        hours_per_week_var = tk.DoubleVar(value=40.0)
        ttk.Entry(dialog, textvariable=hours_per_week_var, width=30).grid(row=5, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Vacation Days/Year:").grid(row=6, column=0, sticky='w', padx=10, pady=5)
        vacation_days_var = tk.IntVar(value=20)
        ttk.Entry(dialog, textvariable=vacation_days_var, width=30).grid(row=6, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Sick Days/Year:").grid(row=7, column=0, sticky='w', padx=10, pady=5)
        sick_days_var = tk.IntVar(value=10)
        ttk.Entry(dialog, textvariable=sick_days_var, width=30).grid(row=7, column=1, padx=10, pady=5)

        def save_employee():
            # Get and validate ID
            id_input = id_var.get().strip()

            try:
                # Convert to integer (will raise ValueError if invalid)
                id_num = int(id_input)

                # Take last 4 digits if longer than 4
                if id_num > 9999:
                    id_num = id_num % 10000
                    messagebox.showwarning("Notice", f"Using last 4 digits: {id_num:04d}")

                employee_id = f"{id_num:04d}"  # Format as 4-digit string

            except ValueError:
                messagebox.showerror("Error", "ID must be a number (digits only)")
                return

            # Check for duplicate ID
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM employees WHERE employee_id = ?", (employee_id,))
            if cursor.fetchone()[0] > 0:
                messagebox.showerror("Error", f"Employee ID {employee_id} already exists!")
                conn.close()
                return
            conn.close()

            # Validate name
            if not name_var.get().strip():
                messagebox.showerror("Error", "Name is required!")
                return

            # All validations passed - save employee
            success = self.employee_manager.add_employee(
                name_var.get().strip(),
                employee_id,  # Formatted 4-digit string
                pos_var.get().strip(),
                rate_var.get(),
                email_var.get().strip(),
                hours_per_week_var.get(),
                vacation_days_var.get(),
                sick_days_var.get()
            )

            if success:
                self.refresh_employee_list()
                self.update_employee_combo()
                dialog.destroy()
                messagebox.showinfo("Success", f"Employee {employee_id} added successfully!")
            else:
                messagebox.showerror("Error", "Failed to add employee")

        ttk.Button(dialog, text="Save", command=save_employee).grid(row=8, column=0, padx=10, pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).grid(row=8, column=1, padx=10, pady=20)

        # Input validation for ID field
        def validate_id_input(new_val):
            if not new_val:  # Allow empty field (for backspacing)
                return True
            return new_val.isdigit()  # Only allow digits

        vcmd = (dialog.register(validate_id_input), '%P')
        id_entry.configure(validate='key', validatecommand=vcmd)

    def edit_employee_dialog(self):
        """Show dialog to edit existing employee with proper saving"""
        selection = self.emp_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an employee to edit.")
            return

        item = self.emp_tree.item(selection[0])
        displayed_id = item['values'][0]  # Get displayed employee ID

        # Get full employee data from database
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees WHERE employee_id = ?", (displayed_id,))
        employee = cursor.fetchone()
        conn.close()

        if not employee:
            messagebox.showerror("Error", "Selected employee not found in database")
            return

        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Employee {displayed_id}")
        dialog.geometry("400x450")  # Slightly taller for better spacing
        dialog.transient(self.root)
        dialog.grab_set()

        # Form fields with current values - using grid for better layout
        fields = [
            ("Name:", tk.StringVar(value=employee[1])),
            ("Employee ID:", None, displayed_id),  # Display only
            ("Position:", tk.StringVar(value=employee[3] or "")),
            ("Hourly Rate:", tk.DoubleVar(value=employee[4] or 0.0)),
            ("Email:", tk.StringVar(value=employee[5] or "")),
            ("Hours/Week:", tk.DoubleVar(value=employee[7] if len(employee) > 7 else 40.0)),
            ("Vacation Days:", tk.IntVar(value=employee[8] if len(employee) > 8 else 20)),
            ("Sick Days:", tk.IntVar(value=employee[9] if len(employee) > 9 else 10)),
        ]

        for row, (label, var, *display) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=row, column=0, sticky='w', padx=10, pady=5)
            if var is not None:
                ttk.Entry(dialog, textvariable=var, width=30).grid(row=row, column=1, padx=10, pady=5)
            else:
                ttk.Label(dialog, text=display[0], foreground='blue').grid(row=row, column=1, sticky='w', padx=10, pady=5)

        def save_changes():
            # Validate required fields
            if not fields[0][1].get().strip():  # Name field
                messagebox.showerror("Error", "Name is required!")
                return

            # Prepare update data
            update_data = {
                'name': fields[0][1].get().strip(),
                'position': fields[2][1].get().strip(),
                'hourly_rate': float(fields[3][1].get()),
                'email': fields[4][1].get().strip(),
                'hours_per_week': float(fields[5][1].get()),
                'vacation_days_per_year': int(fields[6][1].get()),
                'sick_days_per_year': int(fields[7][1].get())
            }

            # Update employee in database
            try:
                success = self.employee_manager.update_employee(employee[0], **update_data)
                if success:
                    self.refresh_employee_list()
                    self.update_employee_combo()
                    dialog.destroy()
                    messagebox.showinfo("Success", f"Employee {displayed_id} updated successfully!")
                else:
                    messagebox.showerror("Error", "Failed to update employee in database")
            except Exception as e:
                messagebox.showerror("Error", f"Database error: {str(e)}")

        # Button frame
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="Save Changes", command=save_changes).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
    
    def deactivate_employee(self):
        """Deactivate selected employee"""
        emp_id = self._get_selected_employee_db_id()
        if not emp_id:
            messagebox.showwarning("Warning", "Please select an employee to deactivate.")
            return

        if messagebox.askyesno("Confirm", 
                             "Are you sure you want to deactivate this employee?\n"
                             "(You can reactivate them later)"):
            success, message = self.employee_manager.remove_employee(emp_id, permanent=False)

            if success:
                messagebox.showinfo("Success", message)
                self.refresh_employee_list()
            else:
                messagebox.showerror("Error", message)

    def reactivate_employee(self):
        """Reactivate selected employee"""
        emp_id = self._get_selected_employee_db_id()
        if not emp_id:
            messagebox.showwarning("Warning", "Please select an employee to reactivate.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to reactivate this employee?"):
            success, message = self.employee_manager.reactivate_employee(emp_id)

            if success:
                messagebox.showinfo("Success", message)
                self.refresh_employee_list()
            else:
                messagebox.showerror("Error", message)

    def delete_employee(self):
        """Permanently delete selected employee"""
        emp_id = self._get_selected_employee_db_id()
        if not emp_id:
            messagebox.showwarning("Warning", "Please select an employee to delete.")
            return

        if messagebox.askyesno("Confirm", 
                             "WARNING: This will permanently delete the employee and all their records!\n"
                             "Are you absolutely sure?"):
            success, message = self.employee_manager.remove_employee(emp_id, permanent=True)

            if success:
                messagebox.showinfo("Success", message)
                self.refresh_employee_list()
            else:
                messagebox.showerror("Error", message)

    def on_employee_select(self, event):
        """Handle employee selection"""
        selected = self.emp_var.get()
        if selected:
            # Extract employee ID from selection
            emp_id = selected.split('(')[1].split(')')[0]
            # Find employee in database and set selected_employee
            employees = self.employee_manager.get_all_employees()
            for emp in employees:
                if emp[2] == emp_id:  # emp[2] is employee_id
                    self.selected_employee = emp[0]  # emp[0] is database id
                    break
            #self.load_time_records()
            self.load_time_records_data()  

    def clear_employee_selection(self):
        """Handle employee selection"""
        self.selected_employee = None
        self.selected_employee_id = None

    def delete_time_entry(self):
        """Delete selected time entry from database (single record only)"""
        selected_items = self.time_tree.selection()

        if not selected_items:
            messagebox.showwarning("Warning", "Please select a time entry to delete")
            return

        # Only process the first selected item to ensure single deletion
        first_selected = selected_items[0]

        try:
            # Get record details from Treeview
            item_values = self.time_tree.item(first_selected)['values']
            if not item_values or len(item_values) < 1:
                raise ValueError("Invalid record selected")

            record_date = item_values[0]  # First column is date
            employee_id = self.selected_employee

            # Confirm deletion
            confirm = messagebox.askyesno(
                "Confirm Deletion",
                f"Delete time entry for {record_date}?\nThis action cannot be undone."
            )
            if not confirm:
                return

            # Delete from database with precise matching
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            # First verify we have exactly one matching record
            cursor.execute('''
                SELECT COUNT(*) FROM time_records 
                WHERE employee_id = ? AND date = ?
            ''', (employee_id, record_date))

            count = cursor.fetchone()[0]

            if count == 0:
                raise ValueError("No matching record found in database")
            elif count > 1:
                # Handle case where duplicates exist
                messagebox.showwarning("Warning", 
                                     f"Found {count} entries for this date. Deleting all matching entries.")

            # Proceed with deletion
            cursor.execute('''
                DELETE FROM time_records 
                WHERE employee_id = ? AND date = ?
            ''', (employee_id, record_date))

            deleted_rows = cursor.rowcount
            conn.commit()

            if deleted_rows == 1:
                messagebox.showinfo("Success", "Time entry deleted successfully")
            else:
                messagebox.showinfo("Info", f"Deleted {deleted_rows} time entries")

            # Refresh the display
            self.load_time_records_data()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete time entry: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    # def edit_time_entry(self):
    #     """Edit selected time entry via pop-up window"""
    #     selected_item = self.time_tree.selection()

    #     if not selected_item:
    #         messagebox.showwarning("Warning", "Please select a time entry to edit")
    #         return

    #     try:
    #         item_values = self.time_tree.item(selected_item[0])['values']
    #         if not item_values or len(item_values) < 5:
    #             raise ValueError("Invalid record selected")

    #         self.create_edit_window(item_values)

    #     except Exception as e:
    #         messagebox.showerror("Error", f"Failed to edit time entry: {str(e)}")
    
    def generate_employee_report(self):
        """Generate report for selected employee"""
        if not self.selected_employee:
            messagebox.showwarning("Warning", "Please select an employee first.")
            return
        
        month = self.month_var.get()
        year = self.year_var.get()
        
        summary = self.time_tracker.calculate_monthly_summary(self.selected_employee, year, month)
        
        report = f"Employee Report - {calendar.month_name[month]} {year}\n"
        report += "=" * 50 + "\n"
        report += f"Contract: {summary['hours_per_week']:.1f} hours/week\n"
        report += f"Vacation Allowance: {summary['vacation_allowance']} days/year\n"
        report += f"Sick Leave Allowance: {summary['sick_allowance']} days/year\n\n"
        report += "MONTHLY SUMMARY:\n"
        report += f"Total Work Hours: {summary['total_work_hours']:.2f}\n"
        report += f"Total Overtime: {summary['total_overtime']:.2f}\n"
        report += f"Vacation Days: {summary['vacation_days']}\n"
        report += f"Sick Days: {summary['sick_days']}\n"
        report += f"Work Days: {summary['work_days']}\n\n"
        report += "YEAR-TO-DATE REMAINING:\n"
        report += f"Vacation Days: {summary['vacation_days_remaining']}\n"
        report += f"Sick Days: {summary['sick_days_remaining']}\n"
        
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(1.0, report)
    
    def generate_summary_report(self):
        """Generate summary report for all employees"""
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(1.0, "Summary report functionality to be implemented...")

    def update_details_combo(self):
        """Update the employee combobox in details tab"""
        employees = self.employee_manager.get_all_employees(include_inactive=True)
        emp_names = [f"{emp[1]} ({emp[2]})" for emp in employees]
        self.details_emp_combo['values'] = emp_names
        if emp_names:
            self.details_emp_combo.current(0)
            self.load_employee_details()

    def load_employee_details(self, event=None):
        """Load details for the selected employee"""
        selected = self.details_emp_var.get()
        if not selected:
            return

        # Extract employee ID from selection
        emp_id = selected.split('(')[1].split(')')[0]

        # Find employee in database
        employees = self.employee_manager.get_all_employees(include_inactive=True)
        employee = None
        for emp in employees:
            if emp[2] == emp_id:  # emp[2] is employee_id
                employee = emp
                break

        if not employee:
            return

        # Update personal info
        self.personal_info_values['Name'].config(text=employee[1])
        self.personal_info_values['Employee ID'].config(text=employee[2])
        self.personal_info_values['Position'].config(text=employee[3] if employee[3] else "N/A")
        self.personal_info_values['Hourly Rate'].config(text=f"${employee[4]:.2f}" if employee[4] else "N/A")
        self.personal_info_values['Email'].config(text=employee[5] if employee[5] else "N/A")
        self.personal_info_values['Hire Date'].config(text=employee[6] if employee[6] else "N/A")
        self.personal_info_values['Status'].config(
            text="Active" if employee[10] else "Inactive",
            foreground="green" if employee[10] else "red"
        )

        # Update work info
        self.work_info_values['Hours/Week'].config(text=f"{employee[7]:.1f}" if employee[7] else "N/A")
        self.work_info_values['Vacation Days/Year'].config(text=str(employee[8]) if employee[8] else "N/A")
        self.work_info_values['Sick Days/Year'].config(text=str(employee[9]) if employee[9] else "N/A")

        # Calculate and display remaining days
        current_year = datetime.now().year
        start_of_year = date(current_year, 1, 1)

        conn = self.db_manager.get_connection()
        cursor = conn.cursor()

        # Get vacation days used this year
        cursor.execute('''
            SELECT COUNT(*) FROM time_records 
            WHERE employee_id = ? AND date >= ? AND record_type = 'vacation'
        ''', (employee[0], start_of_year))
        vacation_used = cursor.fetchone()[0]

        # Get sick days used this year
        cursor.execute('''
            SELECT COUNT(*) FROM time_records 
            WHERE employee_id = ? AND date >= ? AND record_type = 'sick'
        ''', (employee[0], start_of_year))
        sick_used = cursor.fetchone()[0]
        conn.close()

        vacation_remaining = max(0, (employee[8] if employee[8] else 20) - vacation_used)
        sick_remaining = max(0, (employee[9] if employee[9] else 10) - sick_used)

        self.work_info_values['Vacation Days Remaining'].config(
            text=f"{vacation_remaining} (of {employee[8] if employee[8] else 20})",
            foreground="green" if vacation_remaining > 0 else "red"
        )
        self.work_info_values['Sick Days Remaining'].config(
            text=f"{sick_remaining} (of {employee[9] if employee[9] else 10})",
            foreground="green" if sick_remaining > 0 else "red"
        )

        # Update statistics
        current_month = datetime.now().month
        monthly_summary = self.time_tracker.calculate_monthly_summary(employee[0], current_year, current_month)
        yearly_summary = self.time_tracker.calculate_yearly_summary(employee[0], current_year)

        self.stats_values['Work Hours'].config(text=f"{monthly_summary['total_work_hours']:.1f}")
        self.stats_values['Overtime'].config(text=f"{monthly_summary['total_overtime']:.1f}")
        self.stats_values['Vacation Days'].config(text=str(monthly_summary['vacation_days']))
        self.stats_values['Sick Days'].config(text=str(monthly_summary['sick_days']))
        self.stats_values['YTD Work Hours'].config(text=f"{yearly_summary['total_work_hours']:.1f}")
        self.stats_values['YTD Overtime'].config(text=f"{yearly_summary['total_overtime']:.1f}")

# =============================================================================
# MAIN APPLICATION ENTRY POINT                                                  #TODO:  later edit
# =============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = EmployeeTimeApp(root)
    root.mainloop()
