# Employee Time Management Desktop App - Enhanced GUI

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font
import sqlite3
from datetime import datetime, date, timedelta
import calendar
import json
from calendar_popup import CalendarDialog
from database_management import DatabaseManager, EmployeeManager, TimeTracker
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
        self.date_var = tk.StringVar()
        self.date_display_var = tk.StringVar()        

        # Initialize database and managers
        self.db_manager = DatabaseManager()
        self.employee_manager = EmployeeManager(self.db_manager)
        self.time_tracker = TimeTracker(self.db_manager)
        self.date_manager = DateManager()

        # Current selections
        self.selected_employee = None
        self.selected_employee_id = None
        self.current_month = datetime.now().month
        self.current_year = datetime.now().year
        
        # Style configuration
        self.configure_styles()
        self.create_widgets()

  # =============================================================================
  # WINDOWS, TABS ETC...
  # =============================================================================

    def configure_styles(self):
        """Configure custom styles for the application"""
        style = ttk.Style()
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
    
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
        """Create time tracking tab"""
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

        # Month/Year selection
        ttk.Label(emp_row, text="Month:").pack(side=tk.LEFT)
        self.month_var = tk.IntVar(value=self.current_month)
        month_spin = tk.Spinbox(emp_row, from_=1, to=12, textvariable=self.month_var, width=5)
        month_spin.pack(side=tk.LEFT, padx=(5, 10))

        ttk.Label(emp_row, text="Year:").pack(side=tk.LEFT)
        self.year_var = tk.IntVar(value=self.current_year)
        year_spin = tk.Spinbox(emp_row, from_=2020, to=2030, textvariable=self.year_var, width=8)
        year_spin.pack(side=tk.LEFT, padx=(5, 20))

        ttk.Button(emp_row, text="Load Month Data", command=self.load_month_data).pack(side=tk.LEFT, padx=5)

        # Time entry section
        entry_frame = ttk.LabelFrame(main_container, text="Add/Edit Time Entry")
        entry_frame.pack(fill=tk.X, pady=(0, 10))

        # First row - Date and basic info
        date_row = ttk.Frame(entry_frame)
        date_row.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(date_row, text="Date:").pack(side=tk.LEFT)
        self.date_display_var = tk.StringVar()

        # Date entry fields
        self.day_var = tk.IntVar(value=date.today().day)
        self.date_month_var = tk.IntVar(value=date.today().month)
        self.date_year_var = tk.IntVar(value=date.today().year)

        # formatted date (YYYY-MM-DD)
        self.date_var = tk.StringVar()
        self.update_date_display()

        day_spin = tk.Spinbox(date_row, from_=1, to=31, textvariable=self.day_var, width=4)
        day_spin.pack(side=tk.LEFT, padx=2)
        ttk.Label(date_row, text="/").pack(side=tk.LEFT)

        month_spin = tk.Spinbox(date_row, from_=1, to=12, textvariable=self.date_month_var, width=4)
        month_spin.pack(side=tk.LEFT, padx=2)
        ttk.Label(date_row, text="/").pack(side=tk.LEFT)

        year_spin = tk.Spinbox(date_row, from_=2020, to=2030, textvariable=self.date_year_var, width=6)
        year_spin.pack(side=tk.LEFT, padx=2)

        # Calendar button #TODO: this icon is ugly, change this 
        ttk.Button(date_row, text="📅", width=3, command=self.open_calendar).pack(side=tk.LEFT, padx=5)

        # Display selected date
        self.date_display_var = tk.StringVar()
        self.update_date_display()
        ttk.Label(date_row, textvariable=self.date_display_var, foreground='blue').pack(side=tk.LEFT, padx=10)

        # Hours and type
        ttk.Label(date_row, text="Hours:").pack(side=tk.LEFT, padx=(20, 0))
        self.hours_var = tk.DoubleVar()
        ttk.Entry(date_row, textvariable=self.hours_var, width=8).pack(side=tk.LEFT, padx=5)

        ttk.Label(date_row, text="Type:").pack(side=tk.LEFT, padx=(10, 0))
        self.type_var = tk.StringVar(value="work")
        type_combo = ttk.Combobox(date_row, textvariable=self.type_var, 
                                 values=["work", "vacation", "sick", "holiday"], width=10, state="readonly")
        type_combo.pack(side=tk.LEFT, padx=5)

        # Second row - Notes and buttons
        notes_row = ttk.Frame(entry_frame)
        notes_row.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(notes_row, text="Notes:").pack(side=tk.LEFT)
        self.notes_var = tk.StringVar()
        ttk.Entry(notes_row, textvariable=self.notes_var, width=50).pack(side=tk.LEFT, padx=(5, 20))

        ttk.Button(notes_row, text="Add Entry", command=self.add_time_entry).pack(side=tk.RIGHT, padx=5)

        # Bind events to update date display
        for widget in [day_spin, month_spin, year_spin]:
            widget.bind('<FocusOut>', lambda e: self.update_date_display())
            widget.bind('<KeyRelease>', lambda e: self.root.after(100, self.update_date_display))

        # Time records display
        records_frame = ttk.LabelFrame(main_container, text="Time Records")
        records_frame.pack(fill=tk.BOTH, expand=True)

        # Time records treeview
        time_columns = ('Date', 'Hours', 'Overtime', 'Type', 'Notes')
        self.time_tree = ttk.Treeview(records_frame, columns=time_columns, show='headings', height=10)

        time_widths = {'Date': 100, 'Hours': 80, 'Overtime': 80, 'Type': 100, 'Notes': 200}
        for col in time_columns:
            self.time_tree.heading(col, text=col)
            self.time_tree.column(col, width=time_widths.get(col, 100))

        time_scrollbar = ttk.Scrollbar(records_frame, orient=tk.VERTICAL, command=self.time_tree.yview)
        self.time_tree.configure(yscrollcommand=time_scrollbar.set)

        self.time_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        time_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        # Time records buttons
        time_btn_frame = ttk.Frame(records_frame)
        time_btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(time_btn_frame, text="Edit Selected", command=self.not_yet_implemented).pack(side=tk.LEFT, padx=5)
        ttk.Button(time_btn_frame, text="Delete Selected", command=self.delete_time_entry).pack(side=tk.LEFT, padx=5)

        self.update_employee_combo()

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
        
        # Main container
        main_container = ttk.Frame(settings_frame)
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
        #ttk.Button(db_path_frame, text="Browse", command=self.browse_database).pack(side=tk.RIGHT, padx=(5, 0)) #TODO: implement later!
        
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
        settings_btn_frame.pack(fill=tk.X)
        
        ttk.Button(settings_btn_frame, text="Save Settings", command=self.not_yet_implemented).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(settings_btn_frame, text="Reset to Defaults", command=self.not_yet_implemented).pack(side=tk.LEFT)
    
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

    def load_time_records(self, employee_id=None, month=None, year=None):
        """Load time records for the selected employee and period into the Treeview"""
        # Clear existing records
        self.time_tree.delete(*self.time_tree.get_children())

        # Use current selection if no parameters provided
        employee_id = employee_id or self.selected_employee
        month = month or self.month_var.get()
        year = year or self.year_var.get()

        if not employee_id:
            return

        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            # Get records for the selected month/year
            cursor.execute('''
                SELECT date, hours_worked, overtime_hours, record_type, notes 
                FROM time_records 
                WHERE employee_id = ? 
                AND strftime('%m', date) = ? 
                AND strftime('%Y', date) = ?
                ORDER BY date
            ''', (employee_id, f"{month:02d}", str(year)))

            records = cursor.fetchall()

            # Insert records into the Treeview
            for record in records:
                self.time_tree.insert('', 'end', values=(
                    record[0],  # Date
                    f"{record[1]:.2f}",  # Hours worked
                    f"{record[2]:.2f}" if record[2] else "0.00",  # Overtime
                    record[3].capitalize(),  # Type
                    record[4]  # Notes
                ))

        except Exception as e:
            messagebox.showerror("Database Error", f"Could not load time records: {str(e)}")
        finally:
            conn.close()

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
                self.load_time_records()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process duplicates: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def not_yet_implemented(self):#TODO: Remove!
        """TODO Remove later, here just to patch up the missing functionality"""
        messagebox.showinfo("Info", "functionality to be implemented....")

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
            self.load_time_records()  

    def clear_employee_selection(self):
        """Handle employee selection"""
        self.selected_employee = None
        self.selected_employee_id = None

    def load_month_data(self):
        """Load time data for selected month"""
        if not self.selected_employee:
            messagebox.showwarning("Warning", "Please select an employee first.")
            return
        
        month = self.month_var.get()
        year = self.year_var.get()
        
        # Load and display month data
        records = self.time_tracker.get_monthly_records(self.selected_employee, year, month)
        summary = self.time_tracker.calculate_monthly_summary(self.selected_employee, year, month)
        self.load_time_records()

        # Display summary (implement display logic)
        messagebox.showinfo("Month Summary", 
                          f"Work Hours: {summary['total_work_hours']:.1f} / {summary['hours_per_week']:.1f} per week\n"
                          f"Overtime: {summary['total_overtime']:.1f}\n"
                          f"Vacation Days: {summary['vacation_days']} (Remaining: {summary['vacation_days_remaining']})\n"
                          f"Sick Days: {summary['sick_days']} (Remaining: {summary['sick_days_remaining']})")
    
    def add_time_entry(self):
        """Add time entry for selected employee"""
        if not self.selected_employee:
            messagebox.showwarning("Warning", "Please select an employee first.")
            return
        try:
            entry_date = datetime.strptime(self.date_var.get(), "%Y-%m-%d").date()
            hours = self.hours_var.get()
            record_type = self.type_var.get()
            notes = self.notes_var.get()
            success, message = self.time_tracker.add_time_record(
                self.selected_employee, entry_date, hours, record_type, notes
            )
            if success:
                messagebox.showinfo("Success", message)
                self.load_time_records() 
                self.hours_var.set(0.0)
                self.notes_var.set("")
                self.sort_out_time_entries()

            else:
                messagebox.showerror("Error", message)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid date (YYYY-MM-DD)")
        except AttributeError:
            messagebox.showerror("Error", "Could not find date attribute. Please check the date field.")

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
            self.load_time_records()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete time entry: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def edit_time_entry(self):
        sort_out_time_entries()
        pass

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
