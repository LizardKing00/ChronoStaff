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
from report_generation import ReportManager
import os
import threading
import base64

# =============================================================================
# MAIN APPLICATION GUI
# =============================================================================

class EmployeeTimeApp:
    
 # =============================================================================
 # INITIALIZATION & SETUP METHODS
 # =============================================================================
    
    def __init__(self, root):
        self.root = root
        self.root.title("Chrono Staff")
        # Load the image file from disk.
        icon = tk.PhotoImage(file="/home/zarathustra/repos/ChronoStaff/resources/pictures/main_logo.png") #TODO: edit to make not dependant on the username!
        # Set it as the window icon.
        self.root.iconphoto(True, icon)
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

        # Set template to color LaTeX
        self.settings_manager.save_report_settings({
            'template': 'color',  # or 'black-white' or 'default'
            'lang': 'en',
            'default_output_path': './reports/'
        })
        try:
            self.report_manager = ReportManager(
                db_path=self.db_manager.db_name,
                templates_dir="resources/templates"
            )
            print("\nReport manager initialized successfully")
            print(f"Database path: {self.db_manager.db_name}")
            
            # Get current template setting
            current_settings = self.report_manager.get_report_settings()
            print(f"Current template: {current_settings.get('template', 'default')}")
            
        except ImportError as e:
            print(f"\nWarning: Could not import ReportManager: {e}")
            print("Make sure report_generation.py is in your Python path")
            self.report_manager = None
        except Exception as e:
            print(f"\nWarning: Could not initialize report manager: {e}")
            self.report_manager = None   
     
        self.employees_data = []
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
        self.report_generation_active = False
        self.last_pdf_path = None

    def configure_styles(self):
        """Configure custom styles for the application"""
        style = ttk.Style()
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Info.TLabel', font=('Arial', 10), foreground='blue')
        style.configure('Error.TLabel', font=('Arial', 10), foreground='red')

 # =============================================================================
 # MAIN UI CREATION METHODS (TABS & WINDOWS)
 # =============================================================================
    
    def create_widgets(self):
        """Create main GUI widgets"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_employees_tab()
        self.create_time_tracking_tab()
        self.create_reports_tab()
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

    def create_reports_tab(self):
        """Create reports tab with functional PDF generation"""
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
        # Bind selection event to update available months
        self.report_emp_combo.bind('<<ComboboxSelected>>', self.on_report_employee_selected)
        
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
        self.month_spinbox = tk.Spinbox(row2, from_=1, to=12, textvariable=self.report_month_var, width=5)
        self.month_spinbox.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(row2, text="Year:").pack(side=tk.LEFT)
        self.report_year_var = tk.IntVar(value=datetime.now().year)
        self.year_spinbox = tk.Spinbox(row2, from_=2020, to=2030, textvariable=self.report_year_var, width=8)
        self.year_spinbox.pack(side=tk.LEFT, padx=(5, 20))
        
        # Report buttons (with actual functionality)
        btn_container = ttk.Frame(row2)
        btn_container.pack(side=tk.RIGHT)
        
        self.generate_btn = ttk.Button(btn_container, text="Generate Preview", command=self.generate_report_preview)
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        
        self.export_btn = ttk.Button(btn_container, text="Export PDF", command=self.export_pdf_report)
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_container, text="Clear", command=self.clear_report).pack(side=tk.LEFT, padx=5)
        
        # Progress bar (new addition)
        self.progress_frame = ttk.Frame(controls_frame)
        self.progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_label = ttk.Label(self.progress_frame, text="Ready")
        self.progress_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
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
        
        # Store last generated PDF path
        self.last_pdf_path = None
    
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

        self.create_report_settings_frame(main_container)

        # Settings buttons
        settings_btn_frame = ttk.Frame(main_container)
        settings_btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(settings_btn_frame, text="Save Settings", command=self.save_settings).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(settings_btn_frame, text="Reset to Defaults", command=self.reset_settings).pack(side=tk.LEFT)
        ttk.Button(settings_btn_frame, text="Load Settings", command=self.load_settings).pack(side=tk.LEFT, padx=(10, 0))
        self.load_settings()

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

    def create_report_settings_frame(self, parent):
        """Create report settings section with language and template selection"""

        # Report Template Settings
        report_template_frame = ttk.LabelFrame(parent, text="Report Generation Settings")
        report_template_frame.pack(fill=tk.X, pady=(0, 20))

        # Template settings grid
        template_grid = ttk.Frame(report_template_frame)
        template_grid.pack(padx=10, pady=10, fill=tk.X)

        # Language selection (new)
        ttk.Label(template_grid, text="Language:").grid(row=0, column=0, sticky='w', pady=2)

        self.language_var = tk.StringVar()
        language_combo = ttk.Combobox(template_grid, textvariable=self.language_var, 
                                     values=["English", "Deutsch"], state="readonly", width=15)
        language_combo.grid(row=0, column=1, sticky="w", padx=(5, 20), pady=2)

        # Template selection
        ttk.Label(template_grid, text="Report Template:").grid(row=1, column=0, sticky='w', pady=2)

        if self.report_manager:
            # Get available templates and check their availability
            templates = self.report_manager.get_available_templates()
            template_choices = []
            template_mapping = {}

            # Check system capabilities
            available_methods = self.report_manager.get_available_pdf_methods()
            latex_available = available_methods.get('latex', False)
            reportlab_available = available_methods.get('reportlab', False)

            for template in templates:
                display_name = template['name']
                template_id = template['id']

                # Add availability and language support indicators
                lang_support = template.get('languages', ['en'])
                lang_text = "EN+DE" if len(lang_support) >= 2 else "EN only"

                if template_id in ['latex_bw', 'latex_color'] and not latex_available:
                    display_name += f" ({lang_text}, ⚠️ Requires LaTeX)"
                elif template_id == 'default' and not reportlab_available:
                    display_name += f" ({lang_text}, ⚠️ Requires ReportLab)"
                elif template_id in ['latex_bw', 'latex_color'] and latex_available:
                    display_name += f" ({lang_text}, ✅ Available)"
                elif template_id == 'default' and reportlab_available:
                    display_name += f" ({lang_text}, ✅ Available)"

                template_choices.append(display_name)
                template_mapping[display_name] = template_id

            # Store mapping for later use
            self.template_mapping = template_mapping

        else:
            template_choices = ['Report Manager Not Available']
            template_mapping = {}

        self.template_mapping = template_mapping

        self.template_display_var = tk.StringVar()
        template_combo = ttk.Combobox(template_grid, textvariable=self.template_display_var, 
                                     values=template_choices, state="readonly", width=50)
        template_combo.grid(row=1, column=1, sticky="w", padx=(5, 20), pady=2)

        # Apply template button
        ttk.Button(template_grid, text="Apply Settings", 
                  command=self.apply_language_and_template_settings).grid(row=1, column=2, padx=5, pady=2)

        # System status info
        if self.report_manager:
            available_methods = self.report_manager.get_available_pdf_methods()
            info_text = "System status: "
            if available_methods.get('reportlab', False):
                info_text += "ReportLab ✅ "
            else:
                info_text += "ReportLab ❌ "
            if available_methods.get('latex', False):
                info_text += "LaTeX ✅"
            else:
                info_text += "LaTeX ❌"
        else:
            info_text = "Report Manager not initialized"

        ttk.Label(template_grid, text=info_text, font=('TkDefaultFont', 8), 
                 foreground='darkgreen' if 'LaTeX ✅' in info_text else 'darkorange').grid(
                     row=2, column=1, sticky='w', padx=5, pady=2)

        # Load current settings
        if self.report_manager:
            try:
                current_settings = self.settings_manager.get_report_settings()

                # Set language
                current_lang = current_settings.get('lang', 'en')
                if current_lang == 'de':
                    self.language_var.set('Deutsch')
                else:
                    self.language_var.set('English')

                # Set template
                current_template = current_settings.get('template', 'default')
                db_to_display = {
                    'default': 'Default (ReportLab)',
                    'black-white': 'LaTeX Black & White',
                    'color': 'LaTeX Color'
                }

                target_display = db_to_display.get(current_template, 'Default (ReportLab)')

                # Find matching choice (with availability suffix)
                for choice in template_choices:
                    if choice.startswith(target_display):
                        self.template_display_var.set(choice)
                        break
                else:
                    # If current template not available, set to first available
                    available_choices = [c for c in template_choices if '✅ Available' in c]
                    if available_choices:
                        self.template_display_var.set(available_choices[0])
                    elif template_choices:
                        self.template_display_var.set(template_choices[0])

            except Exception as e:
                print(f"Error setting current settings: {e}")
                self.language_var.set('English')
                if template_choices:
                    self.template_display_var.set(template_choices[0])

        # Output path selection 
        ttk.Label(template_grid, text="Output Path:").grid(row=3, column=0, sticky='w', pady=(10, 2))

        output_path_frame = ttk.Frame(template_grid)
        output_path_frame.grid(row=3, column=1, columnspan=2, sticky='ew', padx=(5, 0), pady=(10, 2))

        default_output = './reports/'
        if self.report_manager:
            try:
                current_settings = self.settings_manager.get_report_settings()
                default_output = current_settings.get('default_output_path', './reports/')
            except:
                pass
            
        self.template_output_var = tk.StringVar(value=default_output)
        ttk.Entry(output_path_frame, textvariable=self.template_output_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_path_frame, text="Browse", command=self.browse_template_output).pack(side=tk.LEFT, padx=(5, 0))

        # Language preview section
        preview_frame = ttk.Frame(template_grid)
        preview_frame.grid(row=4, column=1, sticky='w', padx=5, pady=10)

        ttk.Label(preview_frame, text="Preview:", font=('TkDefaultFont', 8, 'bold')).pack(side=tk.LEFT)
        self.language_preview_label = ttk.Label(preview_frame, text="", font=('TkDefaultFont', 8))
        self.language_preview_label.pack(side=tk.LEFT, padx=(5, 0))

        # Update preview when language changes
        self.language_var.trace('w', self.update_language_preview)
        self.update_language_preview()

 # =============================================================================
 # EMPLOYEE MANAGEMENT METHODS
 # =============================================================================
    
    def refresh_employee_list(self):
        """Refresh the employee list display - with formatted DB_ID"""
        print("=== REFRESHING EMPLOYEE LIST ===")

        # Clear existing items
        for item in self.emp_tree.get_children():
            self.emp_tree.delete(item)

        # Get employees
        include_inactive = self.show_inactive_var.get()
        employees = self.employee_manager.get_all_employees(include_inactive=include_inactive)
        print(f"Retrieved {len(employees)} employees from database")

        for i, emp in enumerate(employees):
            try:
                print(f"Processing employee {i+1}:")
                print(f"  Database ID (emp[0]): {emp[0]}")
                print(f"  Name (emp[1]): {emp[1]}")
                print(f"  Employee ID (emp[2]): {emp[2]}")
                print(f"  Position (emp[3]): {emp[3]}")
                print(f"  Hourly Rate (emp[4]): {emp[4]}")
                print(f"  Email (emp[5]): {emp[5]}")
                print(f"  Hours/Week (emp[7]): {emp[7] if len(emp) > 7 else 'N/A'}")
                print(f"  Vacation Days (emp[8]): {emp[8] if len(emp) > 8 else 'N/A'}")
                print(f"  Active (emp[10]): {emp[10] if len(emp) > 10 else 'N/A'}")

                status = "Active" if emp[10] else "Inactive"

                # FORMAT the database ID as "DB_ID: {number}"
                formatted_db_id = f"{emp[0]}"

                values_to_insert = (
                    formatted_db_id,    # "1", "2", etc.
                    emp[1],    # name
                    emp[3] or "",    # position
                    f"${emp[4]:.2f}" if emp[4] else "$0.00",  # hourly_rate
                    f"{emp[7]:.1f}" if emp[7] else "40.0",   # hours_per_week
                    emp[8] if emp[8] else "20",    # vacation_days_per_year
                    emp[5] or "",     # email
                    status
                )

                print(f"  Inserting into TreeView: {values_to_insert}")
                self.emp_tree.insert('', 'end', values=values_to_insert)

            except (IndexError, TypeError) as e:
                print(f"ERROR processing employee {i+1}: {e}")
                print(f"Employee data: {emp}")
                continue
            
        print("=== EMPLOYEE LIST REFRESH COMPLETED ===\n")

    def update_employee_combo(self):
        """Update employee combobox with current employees"""
        employees = self.employee_manager.get_all_employees()
        emp_names = [f"{emp[1]} ({emp[2]})" for emp in employees]
        self.emp_combo['values'] = emp_names
    
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
        """Show dialog to edit existing employee - with DB_ID parsing"""
        print("=== EDIT EMPLOYEE DIALOG STARTED ===")

        selection = self.emp_tree.selection()
        print(f"TreeView selection: {selection}")

        if not selection:
            print("ERROR: No employee selected in TreeView")
            messagebox.showwarning("Warning", "Please select an employee to edit.")
            return

        item = self.emp_tree.item(selection[0])
        print(f"Selected item data: {item}")
        print(f"Item values: {item['values']}")

        if not item['values'] or len(item['values']) == 0:
            print("ERROR: No values in selected item")
            messagebox.showerror("Error", "Invalid selection - no data found")
            return

        formatted_db_id = item['values'][0]  # e.g., "1"
        print(f"Formatted DB ID from TreeView: '{formatted_db_id}'")

        try:
            database_id = int(formatted_db_id)
            print(f"Direct conversion database_id: {database_id}")
        except ValueError as e:
            print(f"ERROR parsing database ID from '{formatted_db_id}': {e}")
            messagebox.showerror("Error", f"Invalid database ID format: {formatted_db_id}")
            return

        # Get full employee data from database using database ID
        print(f"Looking up employee in database with database ID: {database_id}")
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees WHERE id = ?", (database_id,))
        employee = cursor.fetchone()
        print(f"Database query result: {employee}")
        conn.close()

        if not employee:
            print(f"ERROR: Employee with database ID {database_id} not found in database")

            # Additional debugging - let's see what database IDs actually exist
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, employee_id, name FROM employees")
            all_employees = cursor.fetchall()
            print("All employees in database:")
            for emp in all_employees:
                print(f"  DB_ID: {emp[0]}, Employee_ID: '{emp[1]}', Name: {emp[2]}")
            conn.close()

            messagebox.showerror("Error", "Selected employee not found in database")
            return

        print(f"Employee data retrieved successfully:")
        print(f"  Database ID: {employee[0]}")
        print(f"  Name: {employee[1]}")
        print(f"  Employee ID: {employee[2]}")
        print(f"  Position: {employee[3]}")
        print(f"  Hourly Rate: {employee[4]}")
        print(f"  Email: {employee[5]}")
        print(f"  Hire Date: {employee[6]}")
        print(f"  Hours/Week: {employee[7] if len(employee) > 7 else 'N/A'}")
        print(f"  Vacation Days: {employee[8] if len(employee) > 8 else 'N/A'}")
        print(f"  Sick Days: {employee[9] if len(employee) > 9 else 'N/A'}")
        print(f"  Active: {employee[10] if len(employee) > 10 else 'N/A'}")
        print(f"  Full employee record length: {len(employee)}")

        # Create dialog window
        print("Creating dialog window...")
        dialog = tk.Toplevel(self.root)
        # Show both database ID and employee_id in title for clarity
        dialog.title(f"Edit Employee {employee[2]} (DB ID: {database_id})")
        dialog.geometry("400x450")
        dialog.transient(self.root)
        dialog.grab_set()
        print("Dialog window created successfully")

        # Create individual variables for each field
        print("Creating form variables...")
        try:
            name_var = tk.StringVar(value=employee[1])
            print(f"  Name variable set to: '{employee[1]}'")

            position_var = tk.StringVar(value=employee[3] or "")
            print(f"  Position variable set to: '{employee[3] or ''}'")

            hourly_rate_var = tk.DoubleVar(value=employee[4] or 0.0)
            print(f"  Hourly rate variable set to: {employee[4] or 0.0}")

            email_var = tk.StringVar(value=employee[5] or "")
            print(f"  Email variable set to: '{employee[5] or ''}'")

            hours_per_week_var = tk.DoubleVar(value=employee[7] if len(employee) > 7 else 40.0)
            hours_per_week_value = employee[7] if len(employee) > 7 else 40.0
            print(f"  Hours/week variable set to: {hours_per_week_value}")

            vacation_days_var = tk.IntVar(value=employee[8] if len(employee) > 8 else 20)
            vacation_days_value = employee[8] if len(employee) > 8 else 20
            print(f"  Vacation days variable set to: {vacation_days_value}")

            sick_days_var = tk.IntVar(value=employee[9] if len(employee) > 9 else 10)
            sick_days_value = employee[9] if len(employee) > 9 else 10
            print(f"  Sick days variable set to: {sick_days_value}")

            print("All form variables created successfully")
        except Exception as e:
            print(f"ERROR creating form variables: {e}")
            messagebox.showerror("Error", f"Failed to initialize form: {e}")
            dialog.destroy()
            return

        # Create form fields with grid layout
        print("Creating form fields...")
        row = 0

        try:
            # Name field
            print(f"  Creating name field at row {row}")
            ttk.Label(dialog, text="Name:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
            ttk.Entry(dialog, textvariable=name_var, width=30).grid(row=row, column=1, padx=10, pady=5)
            row += 1

            # Employee ID field (read-only) - show the actual employee_id, not database id
            print(f"  Creating employee ID field at row {row}")
            ttk.Label(dialog, text="Employee ID:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
            ttk.Label(dialog, text=employee[2], foreground='blue').grid(row=row, column=1, sticky='w', padx=10, pady=5)
            row += 1

            # Position field
            print(f"  Creating position field at row {row}")
            ttk.Label(dialog, text="Position:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
            ttk.Entry(dialog, textvariable=position_var, width=30).grid(row=row, column=1, padx=10, pady=5)
            row += 1

            # Hourly Rate field
            print(f"  Creating hourly rate field at row {row}")
            ttk.Label(dialog, text="Hourly Rate:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
            ttk.Entry(dialog, textvariable=hourly_rate_var, width=30).grid(row=row, column=1, padx=10, pady=5)
            row += 1

            # Email field
            print(f"  Creating email field at row {row}")
            ttk.Label(dialog, text="Email:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
            ttk.Entry(dialog, textvariable=email_var, width=30).grid(row=row, column=1, padx=10, pady=5)
            row += 1

            # Hours/Week field
            print(f"  Creating hours/week field at row {row}")
            ttk.Label(dialog, text="Hours/Week:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
            ttk.Entry(dialog, textvariable=hours_per_week_var, width=30).grid(row=row, column=1, padx=10, pady=5)
            row += 1

            # Vacation Days field
            print(f"  Creating vacation days field at row {row}")
            ttk.Label(dialog, text="Vacation Days:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
            ttk.Entry(dialog, textvariable=vacation_days_var, width=30).grid(row=row, column=1, padx=10, pady=5)
            row += 1

            # Sick Days field
            print(f"  Creating sick days field at row {row}")
            ttk.Label(dialog, text="Sick Days:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
            ttk.Entry(dialog, textvariable=sick_days_var, width=30).grid(row=row, column=1, padx=10, pady=5)
            row += 1

            print("All form fields created successfully")

        except Exception as e:
            print(f"ERROR creating form fields: {e}")
            messagebox.showerror("Error", f"Failed to create form fields: {e}")
            dialog.destroy()
            return

        def save_changes():
            print("\n=== SAVE CHANGES FUNCTION CALLED ===")

            # Validate required fields
            name_value = name_var.get().strip()
            print(f"Name field value: '{name_value}'")

            if not name_value:
                print("ERROR: Name field is empty")
                messagebox.showerror("Error", "Name is required!")
                return

            # Get all form values
            print("Getting form values...")
            try:
                position_value = position_var.get().strip()
                print(f"Position: '{position_value}'")

                hourly_rate_value = hourly_rate_var.get()
                print(f"Hourly rate: {hourly_rate_value}")

                email_value = email_var.get().strip()
                print(f"Email: '{email_value}'")

                hours_per_week_value = hours_per_week_var.get()
                print(f"Hours per week: {hours_per_week_value}")

                vacation_days_value = vacation_days_var.get()
                print(f"Vacation days: {vacation_days_value}")

                sick_days_value = sick_days_var.get()
                print(f"Sick days: {sick_days_value}")

            except Exception as e:
                print(f"ERROR getting form values: {e}")
                messagebox.showerror("Error", f"Invalid form values: {e}")
                return

            # Validate numeric fields
            print("Validating numeric fields...")
            try:
                hourly_rate = float(hourly_rate_value)
                hours_per_week = float(hours_per_week_value)
                vacation_days = int(vacation_days_value)
                sick_days = int(sick_days_value)
                print(f"Validated values: rate={hourly_rate}, hours={hours_per_week}, vacation={vacation_days}, sick={sick_days}")
            except ValueError as e:
                print(f"ERROR: Invalid numeric values - {e}")
                messagebox.showerror("Error", "Please enter valid numeric values!")
                return

            # Prepare update data
            update_data = {
                'name': name_value,
                'position': position_value,
                'hourly_rate': hourly_rate,
                'email': email_value,
                'hours_per_week': hours_per_week,
                'vacation_days_per_year': vacation_days,
                'sick_days_per_year': sick_days
            }
            print(f"Update data prepared: {update_data}")

            # Update employee in database using the database ID
            print(f"Updating employee in database with database ID: {database_id}")
            try:
                success = self.employee_manager.update_employee(database_id, **update_data)
                print(f"Update result: {success}")

                if success:
                    print("Update successful - refreshing UI")
                    self.refresh_employee_list()
                    self.update_employee_combo()
                    dialog.destroy()
                    messagebox.showinfo("Success", f"Employee {employee[2]} updated successfully!")
                    print("=== SAVE CHANGES COMPLETED SUCCESSFULLY ===")
                else:
                    print("ERROR: Database update failed")
                    messagebox.showerror("Error", "Failed to update employee in database")
            except Exception as e:
                print(f"ERROR during database update: {e}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", f"Database error: {str(e)}")

        # Button frame
        print("Creating button frame...")
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Save Changes", command=save_changes).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)

        # Set focus on the name field
        dialog.after(100, lambda: name_var.get() and dialog.focus_set())

        print("=== EDIT EMPLOYEE DIALOG SETUP COMPLETED ===\n")

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

    def create_employee_details_window(self):
        """Create a standalone window to display details of the selected employee"""
        print("=== CREATE EMPLOYEE DETAILS WINDOW STARTED ===")
        
        # Get selected employee from TreeView
        selection = self.emp_tree.selection()
        print(f"TreeView selection: {selection}")
        
        if not selection:
            print("ERROR: No employee selected in TreeView")
            messagebox.showwarning("Warning", "Please select an employee first.")
            return
    
        item = self.emp_tree.item(selection[0])
        print(f"Selected item data: {item}")
        print(f"Item values: {item['values']}")
        
        if not item['values'] or len(item['values']) == 0:
            print("ERROR: No values in selected item")
            messagebox.showerror("Error", "Invalid selection - no data found")
            return
    
        # EXTRACT database ID from TreeView
        # If you're using the formatted version "DB_ID: 1", parse it
        # If you're using just the number "1", use it directly
        first_column = item['values'][0]
        print(f"First column value: '{first_column}'")
        
        try:
            if isinstance(first_column, str) and first_column.startswith("DB_ID: "):
                # Parse "DB_ID: 1" format
                database_id = int(first_column.replace("DB_ID: ", ""))
                print(f"Parsed database_id from formatted string: {database_id}")
            else:
                # Direct conversion (should be the database ID)
                database_id = int(first_column)
                print(f"Direct conversion database_id: {database_id}")
        except ValueError as e:
            print(f"ERROR parsing database ID from '{first_column}': {e}")
            messagebox.showerror("Error", f"Invalid database ID format: {first_column}")
            return
    
        # Get employee data using database ID
        print(f"Looking up employee in database with database ID: {database_id}")
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        #Search by database ID (id column) instead of employee_id
        cursor.execute("SELECT * FROM employees WHERE id = ?", (database_id,))
        employee = cursor.fetchone()
        print(f"Database query result: {employee}")
        conn.close()
    
        if not employee:
            print(f"ERROR: Employee with database ID {database_id} not found in database")
            
            # Additional debugging - show what employees actually exist
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, employee_id, name FROM employees")
            all_employees = cursor.fetchall()
            print("All employees in database:")
            for emp in all_employees:
                print(f"  DB_ID: {emp[0]}, Employee_ID: '{emp[1]}', Name: {emp[2]}")
            conn.close()
            
            messagebox.showerror("Error", "Selected employee not found in database")
            return
    
        print(f"Employee found: {employee}")
        print(f"Creating details window for: {employee[1]} ({employee[2]})")
    
        # Create details window
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
    
        # Personal Info Tab
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
    
        # Work Details Tab
        work_frame = ttk.Frame(details_notebook)
        details_notebook.add(work_frame, text="Work Details")
    
        current_year = datetime.now().year
        start_of_year = date(current_year, 1, 1)
    
        print("Calculating vacation and sick days...")
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
    
        # Use database_id (employee[0]) for time_records queries
        print(f"Querying vacation days for database_id: {database_id}")
        cursor.execute('''
            SELECT COUNT(*) FROM time_records 
            WHERE employee_id = ? AND date >= ? AND record_type = 'vacation'
        ''', (database_id, start_of_year))  # Use database_id, not employee[0]
        vacation_used = cursor.fetchone()[0]
        print(f"Vacation days used: {vacation_used}")
    
        print(f"Querying sick days for database_id: {database_id}")
        cursor.execute('''
            SELECT COUNT(*) FROM time_records 
            WHERE employee_id = ? AND date >= ? AND record_type = 'sick'
        ''', (database_id, start_of_year))  # Use database_id, not employee[0]
        sick_used = cursor.fetchone()[0]
        print(f"Sick days used: {sick_used}")
        conn.close()
    
        vacation_remaining = max(0, (employee[8] if len(employee) > 8 else 20) - vacation_used)
        sick_remaining = max(0, (employee[9] if len(employee) > 9 else 10) - sick_used)
    
        print(f"Vacation remaining: {vacation_remaining}, Sick remaining: {sick_remaining}")
    
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
    
        # Statistics Tab
        stats_frame = ttk.Frame(details_notebook)
        details_notebook.add(stats_frame, text="Statistics")
    
        current_month = datetime.now().month
        
        print("Calculating monthly and yearly summaries...")
        # Use database_id for summary calculations
        monthly_summary = self.time_tracker.calculate_monthly_summary(database_id, current_year, current_month)
        yearly_summary = self.time_tracker.calculate_yearly_summary(database_id, current_year)
        
        print(f"Monthly summary: {monthly_summary}")
        print(f"Yearly summary: {yearly_summary}")
    
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
    
        print("=== CREATE EMPLOYEE DETAILS WINDOW COMPLETED ===\n")

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
        print("=== LOAD EMPLOYEE DETAILS STARTED ===")

        selected = self.details_emp_var.get()
        print(f"Selected from details combobox: '{selected}'")

        if not selected:
            print("No employee selected in details combobox")
            return

        # Extract employee info from combobox selection (format: "Name (employee_id)")
        # e.g., "Mario Musterjunge (0001)" -> extract "0001"
        if '(' in selected and ')' in selected:
            try:
                # Extract the employee_id part between parentheses
                employee_id_str = selected.split('(')[1].split(')')[0].strip()
                print(f"Extracted employee_id: '{employee_id_str}'")
            except (IndexError, ValueError) as e:
                print(f"ERROR parsing employee selection '{selected}': {e}")
                messagebox.showerror("Error", f"Invalid employee selection format: {selected}")
                return
        else:
            print(f"ERROR: Invalid selection format '{selected}'")
            messagebox.showerror("Error", f"Invalid employee selection format: {selected}")
            return

        # Find employee in database using employee_id
        print(f"Looking up employee with employee_id: '{employee_id_str}'")
        employees = self.employee_manager.get_all_employees(include_inactive=True)
        employee = None

        for emp in employees:
            print(f"  Checking employee: DB_ID={emp[0]}, employee_id='{emp[2]}', name='{emp[1]}'")
            if emp[2] == employee_id_str:  # emp[2] is employee_id
                employee = emp
                print(f"  FOUND MATCH: {emp}")
                break

        if not employee:
            print(f"ERROR: Employee with employee_id '{employee_id_str}' not found")
            messagebox.showerror("Error", f"Employee {employee_id_str} not found in database")
            return

        print(f"Employee found: {employee}")
        database_id = employee[0]  # Get the database ID for queries
        print(f"Using database_id {database_id} for database queries")

        # Update personal info
        print("Updating personal info display...")
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
        print("Updating work info display...")
        self.work_info_values['Hours/Week'].config(text=f"{employee[7]:.1f}" if employee[7] else "N/A")
        self.work_info_values['Vacation Days/Year'].config(text=str(employee[8]) if employee[8] else "N/A")
        self.work_info_values['Sick Days/Year'].config(text=str(employee[9]) if employee[9] else "N/A")

        # Calculate and display remaining days
        print("Calculating vacation/sick days...")
        current_year = datetime.now().year
        start_of_year = date(current_year, 1, 1)

        conn = self.db_manager.get_connection()
        cursor = conn.cursor()

        # Get vacation days used this year use database_id (employee[0])
        print(f"Querying vacation days for database_id: {database_id}")
        cursor.execute('''
            SELECT COUNT(*) FROM time_records 
            WHERE employee_id = ? AND date >= ? AND record_type = 'vacation'
        ''', (database_id, start_of_year))
        vacation_used = cursor.fetchone()[0]
        print(f"Vacation days used: {vacation_used}")

        # Get sick days used this year use database_id 
        print(f"Querying sick days for database_id: {database_id}")
        cursor.execute('''
            SELECT COUNT(*) FROM time_records 
            WHERE employee_id = ? AND date >= ? AND record_type = 'sick'
        ''', (database_id, start_of_year))
        sick_used = cursor.fetchone()[0]
        print(f"Sick days used: {sick_used}")
        conn.close()

        vacation_remaining = max(0, (employee[8] if employee[8] else 20) - vacation_used)
        sick_remaining = max(0, (employee[9] if employee[9] else 10) - sick_used)

        print(f"Vacation remaining: {vacation_remaining}, Sick remaining: {sick_remaining}")

        self.work_info_values['Vacation Days Remaining'].config(
            text=f"{vacation_remaining} (of {employee[8] if employee[8] else 20})",
            foreground="green" if vacation_remaining > 0 else "red"
        )
        self.work_info_values['Sick Days Remaining'].config(
            text=f"{sick_remaining} (of {employee[9] if employee[9] else 10})",
            foreground="green" if sick_remaining > 0 else "red"
        )

        # Update statistics
        print("Calculating statistics...")
        current_month = datetime.now().month
        monthly_summary = self.time_tracker.calculate_monthly_summary(database_id, current_year, current_month)
        yearly_summary = self.time_tracker.calculate_yearly_summary(database_id, current_year)

        print(f"Monthly summary: {monthly_summary}")
        print(f"Yearly summary: {yearly_summary}")

        self.stats_values['Work Hours'].config(text=f"{monthly_summary['total_work_hours']:.1f}")
        self.stats_values['Overtime'].config(text=f"{monthly_summary['total_overtime']:.1f}")
        self.stats_values['Vacation Days'].config(text=str(monthly_summary['vacation_days']))
        self.stats_values['Sick Days'].config(text=str(monthly_summary['sick_days']))
        self.stats_values['YTD Work Hours'].config(text=f"{yearly_summary['total_work_hours']:.1f}")
        self.stats_values['YTD Overtime'].config(text=f"{yearly_summary['total_overtime']:.1f}")

        print("=== LOAD EMPLOYEE DETAILS COMPLETED ===\n")

 # =============================================================================
 # TIME TRACKING METHODS
 # =============================================================================
    
    def on_employee_select(self, event):
        """Handle employee selection - Fixed to properly extract employee info"""
        selected = self.emp_var.get()
        if not selected:
            self.selected_employee = None
            self.selected_employee_id = None
            return

        print(f"Employee selected: '{selected}'")  # Debug print

        # Extract employee ID from selection (format: "Name (ID)")
        if '(' in selected and ')' in selected:
            try:
                # Extract the ID part between parentheses
                emp_id_str = selected.split('(')[1].split(')')[0].strip()
                print(f"Extracted employee ID string: '{emp_id_str}'")  # Debug print

                # Get employee database ID by looking up the employee_id in database
                conn = self.db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM employees WHERE employee_id = ?", (emp_id_str,))
                result = cursor.fetchone()
                conn.close()

                if result:
                    self.selected_employee = result[0]  # Database ID
                    self.selected_employee_id = emp_id_str  # Display ID
                    print(f"Selected employee DB ID: {self.selected_employee}")  # Debug print

                    # Load time records for this employee
                    self.load_time_records_data()
                else:
                    print(f"Employee with ID {emp_id_str} not found in database")
                    self.selected_employee = None
                    self.selected_employee_id = None

            except (IndexError, ValueError) as e:
                print(f"Error parsing employee selection: {e}")
                self.selected_employee = None
                self.selected_employee_id = None
        else:
            print("Invalid employee selection format")
            self.selected_employee = None
            self.selected_employee_id = None

    def load_time_records_data(self):
        """Load time records data from database and populate the treeview - Fixed version"""
        print("=== load_time_records_data STARTED ===")

        # Check if we have a selected employee
        if not self.selected_employee:
            print("ERROR: No employee selected!")
            return

        # Get employee name for display
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM employees WHERE id = ?", (self.selected_employee,))
        emp_result = cursor.fetchone()

        if not emp_result:
            print(f"ERROR: Employee with ID {self.selected_employee} not found!")
            conn.close()
            return

        emp_name = emp_result[0]
        print(f"Loading records for employee: {emp_name} (ID: {self.selected_employee})")

        # Clear existing data
        current_items = self.time_tree.get_children()
        print(f"Clearing {len(current_items)} existing items from tree")
        for item in current_items:
            self.time_tree.delete(item)

        try:
            # Check date manager values
            print(f"Date manager - Year: {self.date_manager.view_year}, Month: {self.date_manager.view_month}")

            # Get time records for the selected month/year using the database ID
            query_params = (self.selected_employee, str(self.date_manager.view_year), f"{self.date_manager.view_month:02d}")
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

        except Exception as e:
            print(f"ERROR in load_time_records_data: {e}")
            import traceback
            traceback.print_exc()
            if hasattr(self, 'messagebox'):
                messagebox.showerror("Error", f"Failed to load time records: {str(e)}")
        finally:
            conn.close()

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
        """Add time entry for selected employee - Reference implementation"""
        if not self.selected_employee:
            messagebox.showwarning("Warning", "Please select an employee first.")
            return

        try:
            # Get date components from form fields
            print("Selecting the date:")
            day = self.day_var.get()
            month = self.date_month_var.get()
            year = self.date_year_var.get()
            # Create date string in YYYY-MM-DD format
            entry_date = f"{year:04d}-{month:02d}-{day:02d}"

            self.start_times = [var.get().strip() for var in self.start_time_vars if var.get().strip()]
            self.end_times = [var.get().strip() for var in self.end_time_vars if var.get().strip()]

            print(f"day:\t\t{day}")
            print(f"month:\t\t{month}")
            print(f"year:\t\t{year}")
            print(f"entry_date:\t{entry_date}")

            # Get time entry data
            hours = self.hours_var.get()
            record_type = self.type_var.get()
            notes = self.notes_var.get()

            print(f"hours\t\t{hours}")
            print(f"record_type\t\t{record_type}")
            print(f"notes\t\t{notes}")

            # Use the database ID (self.selected_employee) directly
            success, message = self.time_tracker.add_time_record(
                employee_id=self.selected_employee,  # This is the database ID
                record_date=entry_date, 
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
                self.clear_time_form()
            else:
                print("Error!")
                print(message)
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

    def get_selected_employee_id(self):
        """Get the ID of the currently selected employee - Fixed version"""
        if not self.emp_var.get():
            return None

        # Extract employee ID from the combo selection (format: "Name (ID)")
        emp_text = self.emp_var.get()
        if '(' in emp_text and ')' in emp_text:
            try:
                emp_id_str = emp_text.split('(')[1].split(')')[0].strip()

                # Look up the database ID
                conn = self.db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM employees WHERE employee_id = ?", (emp_id_str,))
                result = cursor.fetchone()
                conn.close()

                if result:
                    return result[0]  # Return database ID
                else:
                    return None

            except (IndexError, ValueError):
                return None
        return None

 # =============================================================================
 # REPORT GENERATION METHODS
 # =============================================================================
    
    def update_report_employee_combo(self):
        """Update the employee combo box with available employees - Uses ReportManager"""
        if not self.report_manager:
            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(tk.END, "⚠️  Report manager not initialized.\n")
            return

        try:
            # Use ReportManager instead of employee_manager
            employees = self.report_manager.get_available_employees()
            employee_names = [f"{emp['name']} (ID: {emp['employee_id']})" for emp in employees]

            self.report_emp_combo['values'] = employee_names
            self.employees_data = employees

            if employee_names:
                self.report_emp_combo.current(0)
                self.on_report_employee_selected(None)
            else:
                self.report_text.delete(1.0, tk.END)
                self.report_text.insert(tk.END, "No employees found in database.\n")

        except Exception as e:
            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(tk.END, f"Error loading employees: {e}\n")    
    
    def on_report_employee_selected(self, event):
        """Handle employee selection to show available data months - Uses ReportManager"""
        if not self.report_manager:
            return

        # Check if employees_data exists, if not initialize it
        if not hasattr(self, 'employees_data') or not self.employees_data:
            self.update_report_employee_combo()
            return

        try:
            selected_index = self.report_emp_combo.current()
            if selected_index >= 0 and selected_index < len(self.employees_data):
                employee = self.employees_data[selected_index]

                # Use ReportManager instead of direct database access
                months = self.report_manager.get_available_months_for_employee(employee['id'])

                if months:
                    latest_month = months[0]
                    self.report_year_var.set(latest_month['year'])
                    self.report_month_var.set(latest_month['month'])

                    self.report_text.delete(1.0, tk.END)
                    self.report_text.insert(tk.END, f"Selected Employee: {employee['name']}\n")
                    self.report_text.insert(tk.END, f"Employee ID: {employee['employee_id']}\n\n")
                    self.report_text.insert(tk.END, "Available months with data:\n")
                    for month_info in months:
                        self.report_text.insert(tk.END, f"  • {month_info['display_name']} ({month_info['record_count']} records)\n")
                    self.report_text.insert(tk.END, f"\nCurrent selection: {calendar.month_name[latest_month['month']]} {latest_month['year']}\n\n")
                    self.report_text.insert(tk.END, "Click 'Generate Preview' to see report details\n")
                    self.report_text.insert(tk.END, "Click 'Export PDF' to create PDF file")
                else:
                    self.report_text.delete(1.0, tk.END)
                    self.report_text.insert(tk.END, f"Selected Employee: {employee['name']}\n")
                    self.report_text.insert(tk.END, f"Employee ID: {employee['employee_id']}\n\n")
                    self.report_text.insert(tk.END, "⚠️  No time records found for this employee.\n")

        except Exception as e:
            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(tk.END, f"Error loading employee data: {e}")

    def generate_report_preview(self):
        """Generate a report preview in the text area"""
        if not self.report_manager:
            messagebox.showerror("Error", "Report manager not initialized. Please check your configuration.")
            return

        if self.report_generation_active:
            messagebox.showinfo("Info", "Report generation already in progress...")
            return

        # Validate inputs
        if not self.report_emp_combo.get():
            messagebox.showerror("Error", "Please select an employee.")
            return

        # Check if employees_data exists and handle missing data
        if not hasattr(self, 'employees_data') or not self.employees_data:
            messagebox.showerror("Error", "Employee data not loaded. Please refresh the employee list.")
            self.update_report_employee_combo()
            return

        try:
            selected_index = self.report_emp_combo.current()

            # Validate selected_index bounds
            if selected_index < 0 or selected_index >= len(self.employees_data):
                messagebox.showerror("Error", "Invalid employee selection. Please select a valid employee.")
                return

            employee = self.employees_data[selected_index]
            year = self.report_year_var.get()
            month = self.report_month_var.get()

            # Start progress indication
            self.report_generation_active = True
            self.progress_label.config(text="Generating report preview...")
            self.progress_bar.start()
            self.generate_btn.config(state='disabled')

            # Run in thread to avoid blocking UI
            import threading
            thread = threading.Thread(target=self._generate_report_worker, args=(employee['id'], year, month))
            thread.daemon = True
            thread.start()

        except Exception as e:
            self.report_generation_active = False
            self.progress_bar.stop()
            self.generate_btn.config(state='normal')
            messagebox.showerror("Error", f"Failed to start report generation: {e}")    
    
    def _generate_report_worker(self, employee_id, year, month):
        """Worker thread for report generation - Uses ReportManager"""
        try:
            # Use ReportManager methods instead of duplicating logic
            employee_info = self.report_manager.get_employee_info(employee_id)
            time_records = self.report_manager.get_time_records(employee_id, year, month)
            summary = self.report_manager.calculate_summary(time_records)
            company_info = self.report_manager.get_company_info()

            month_name = calendar.month_name[month]

            # Create detailed report preview
            report_content = f"""
        MONTHLY TIME REPORT PREVIEW
        {'=' * 50}

        Company: {company_info['company_name']}
        Address: {company_info['company_street']}, {company_info['company_city']}
        Phone: {company_info['company_phone']}
        Email: {company_info['company_email']}

        Employee Information:
          Name: {employee_info['name']}
          Employee ID: {employee_info['employee_number']}
          Report Period: {month_name} {year}

        SUMMARY:
          Total Working Hours: {summary['total_hours']:.2f} hours
          Vacation Days Used: {summary['vacation_days']} day(s)
          Sick Leave Taken: {summary['sick_days']} day(s)
          Total Break Time: {summary['total_break_minutes']} minutes

        DETAILED TIME RECORDS:
        {'─' * 80}
        {'Date':<12} {'Start':<8} {'End':<8} {'Hours':<8} {'Break':<8} {'Vacation':<10} {'Sick':<6}
        {'─' * 80}
        """

            for record in time_records:
                vacation = "Yes" if record['is_vacation'] else "No"
                sick = "Yes" if record['is_sick'] else "No"
                hours = f"{record['hours_worked']:.1f}h" if record['hours_worked'] > 0 else "-"
                break_time = f"{record['break_minutes']}min" if record['break_minutes'] > 0 else "-"

                report_content += f"\t\t{record['date']:<12} {record['start_time']:<8} {record['end_time']:<8} {hours:<8} {break_time:<8} {vacation:<10} {sick:<6}\n"

            report_content += f"\n\t{'─' * 80}\n"
            report_content += f"\tTotal: {summary['total_hours']:.2f} hours worked this month\n"

            if summary['vacation_days'] > 0 or summary['sick_days'] > 0:
                report_content += f"\n\t\tTime Off Summary:\n"
                if summary['vacation_days'] > 0:
                    report_content += f"\t\t  • Vacation days: {summary['vacation_days']}\n"
                if summary['sick_days'] > 0:
                    report_content += f"\t\t  • Sick days: {summary['sick_days']}\n"

            report_content += f"\n\t📄 To generate PDF: Click 'Export PDF' button\n"
            report_content += f"\t📊 Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

            # Update UI on main thread
            self.root.after(0, self._report_generation_completed, report_content, None)

        except Exception as e:
            # Update UI on main thread with error
            self.root.after(0, self._report_generation_completed, None, str(e))
    
    def _report_generation_completed(self, report_content, error):
        """Called when report generation completes"""
        self.report_generation_active = False
        self.progress_bar.stop()
        self.generate_btn.config(state='normal')
        
        if error:
            self.progress_label.config(text="Error occurred")
            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(tk.END, f"❌ Error generating report:\n\n{error}")
            messagebox.showerror("Generation Failed", f"Failed to generate report:\n\n{error}")
        else:
            self.progress_label.config(text="Report generated successfully")
            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(tk.END, report_content)
            self.export_btn.config(state='normal')  # Enable PDF export
    
    def export_pdf_report(self):
        """Export the current report as PDF"""
        if not self.report_manager:
            messagebox.showerror("Error", "Report manager not initialized.")
            return

        if self.report_generation_active:
            messagebox.showinfo("Info", "Please wait for report generation to complete.")
            return

        # Validate inputs
        if not self.report_emp_combo.get():
            messagebox.showerror("Error", "Please select an employee and generate a report first.")
            return

        # Check if employees_data exists and handle missing data
        if not hasattr(self, 'employees_data') or not self.employees_data:
            messagebox.showerror("Error", "Employee data not loaded. Please refresh the employee list.")
            self.update_report_employee_combo()
            return

        try:
            selected_index = self.report_emp_combo.current()

            # Validate selected_index bounds
            if selected_index < 0 or selected_index >= len(self.employees_data):
                messagebox.showerror("Error", "Invalid employee selection. Please select a valid employee.")
                return

            employee = self.employees_data[selected_index]
            year = self.report_year_var.get()
            month = self.report_month_var.get()

            # Get default filename
            employee_name = employee['name'].replace(' ', '_').replace('/', '_')
            month_name = calendar.month_name[month]
            default_filename = f"TimeReport_{employee_name}_{month_name}_{year}.pdf"

            # Use initialdir instead of initialname, and set up the path properly
            default_dir = os.path.expanduser("~/Documents")  # Default to Documents folder

            # Ask user for save location
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                title="Save PDF Report",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialdir=default_dir
            )

            # If user selected a path but didn't specify filename, append default filename
            if file_path:
                # Check if the selected path ends with .pdf, if not append the default filename
                if not file_path.lower().endswith('.pdf'):
                    # If user selected a directory or file without extension, append default filename
                    if os.path.isdir(file_path):
                        file_path = os.path.join(file_path, default_filename)
                    else:
                        file_path = file_path + '.pdf'

                # Start PDF generation
                self.progress_label.config(text="Generating PDF...")
                self.progress_bar.start()
                self.export_btn.config(state='disabled')

                # Run in thread
                thread = threading.Thread(target=self._export_pdf_worker, 
                                        args=(employee['id'], year, month, file_path))
                thread.daemon = True
                thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start PDF export: {e}")

    def _export_pdf_worker(self, employee_id, year, month, file_path):
        """Worker thread for PDF export - Uses ReportManager"""
        try:
            # Use ReportManager's PDF generation method
            pdf_path = self.report_manager.generate_pdf_report(
                employee_id=employee_id,
                year=year,
                month=month,
                output_path=file_path
            )

            # Update UI on main thread
            self.root.after(0, self._pdf_export_completed, pdf_path, None)

        except Exception as e:
            # Update UI on main thread with error
            self.root.after(0, self._pdf_export_completed, None, str(e))    
    
    def _pdf_export_completed(self, pdf_path, error):
        """Called when PDF export completes"""
        self.progress_bar.stop()
        self.export_btn.config(state='normal')
        
        if error:
            self.progress_label.config(text="PDF export failed")
            messagebox.showerror("Export Failed", f"Failed to export PDF:\n\n{error}")
        else:
            self.progress_label.config(text="PDF exported successfully")
            self.last_pdf_path = pdf_path
            
            # Ask if user wants to open the PDF
            if messagebox.askyesno("Success", f"PDF exported successfully to:\n{pdf_path}\n\nWould you like to open it?"):
                try:
                    import subprocess
                    import platform
                    
                    if platform.system() == 'Windows':
                        os.startfile(pdf_path)
                    elif platform.system() == 'Darwin':  # macOS
                        subprocess.run(['open', pdf_path])
                    else:  # Linux
                        subprocess.run(['xdg-open', pdf_path])
                except Exception as e:
                    messagebox.showwarning("Warning", f"Could not open PDF automatically: {e}")
    
    def clear_report(self):
        """Clear the report display area"""
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, "Report cleared. Select an employee and generate a new report.")
        self.progress_label.config(text="Ready")
        self.last_pdf_path = None

 # =============================================================================
 # SETTINGS MANAGEMENT METHODS
 # =============================================================================
    
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
            report_settings = {}

            # Language setting - convert from display name to code
            if hasattr(self, 'language_var'):
                language_display = self.language_var.get()
                if language_display == 'Deutsch':
                    report_settings['lang'] = 'de'
                else:
                    report_settings['lang'] = 'en'
            else:
                report_settings['lang'] = 'en'  # Default

            # Template setting - convert from GUI template ID to DATABASE template ID
            if hasattr(self, 'template_display_var') and hasattr(self, 'template_mapping'):
                template_display = self.template_display_var.get()
                # Get the GUI template ID
                gui_template_id = self.template_mapping.get(template_display, 'default')

                # Map GUI template IDs to DATABASE template IDs
                gui_to_db_template_mapping = {
                    'default': 'default',           # ReportLab -> default
                    'latex_bw': 'black-white',      # LaTeX B&W -> black-white  
                    'latex_color': 'color'          # LaTeX Color -> color
                }

                # Convert to database expected value
                db_template_id = gui_to_db_template_mapping.get(gui_template_id, 'default')
                report_settings['template'] = db_template_id

                print(f"Template conversion: {template_display} -> {gui_template_id} -> {db_template_id}")
            else:
                report_settings['template'] = 'color'  # Default

            # Output path setting
            if hasattr(self, 'template_output_var'):
                report_settings['default_output_path'] = self.template_output_var.get()
            else:
                report_settings['default_output_path'] = './reports/'  # Default

            print(f"Collected settings:")
            print(f"  General: {general_settings}")
            print(f"  Company: {company_data}")
            print(f"  Report: {report_settings}")

            # Save all settings
            if self.settings_manager.save_all_settings(general_settings, company_data, report_settings):
                print("Settings saved successfully!")
                messagebox.showinfo("Success", "Settings saved successfully!")
            else:
                print("Error saving settings!")
                messagebox.showerror("Error", "Failed to save settings!")

        except Exception as e:
            print(f"Error in save_settings: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Error saving settings: {e}")

    def load_settings(self):
        """Load settings from database using SettingsManager - with corrected template mapping"""
        try:
            # Load all settings
            all_settings = self.settings_manager.load_all_settings()

            # Load general settings
            general = all_settings.get('general', {})
            if hasattr(self, 'std_hours_var'):
                self.std_hours_var.set(general.get('standard_hours_per_day', 8.0))
            if hasattr(self, 'overtime_threshold_var'):
                self.overtime_threshold_var.set(general.get('overtime_threshold', 40.0))
            if hasattr(self, 'default_vacation_var'):
                self.default_vacation_var.set(general.get('vacation_days_per_year', 20))
            if hasattr(self, 'default_sick_var'):
                self.default_sick_var.set(general.get('sick_days_per_year', 10))

            # Load company data
            company = all_settings.get('company', {})
            if hasattr(self, 'company_name_var'):
                self.company_name_var.set(company.get('companyname', 'Meine Firma GmbH'))
            if hasattr(self, 'company_street_var'):
                self.company_street_var.set(company.get('companystreet', 'Geschäftsstraße 123'))
            if hasattr(self, 'company_city_var'):
                self.company_city_var.set(company.get('companycity', '10115 Berlin'))
            if hasattr(self, 'company_phone_var'):
                self.company_phone_var.set(company.get('companyphone', '+49-30-1234567'))
            if hasattr(self, 'company_email_var'):
                self.company_email_var.set(company.get('companyemail', 'contact@meinefirma.com'))

            # Load and update company colors
            if hasattr(self, 'company_color1_var'):
                color1 = company.get('company_color_1', '#1E40AF')
                self.company_color1_var.set(color1)
                if hasattr(self, 'color1_preview'):
                    try:
                        self.color1_preview.config(bg=color1)
                    except tk.TclError:
                        pass

            if hasattr(self, 'company_color2_var'):
                color2 = company.get('company_color_2', '#3B82F6')
                self.company_color2_var.set(color2)
                if hasattr(self, 'color2_preview'):
                    try:
                        self.color2_preview.config(bg=color2)
                    except tk.TclError:
                        pass

            if hasattr(self, 'company_color3_var'):
                color3 = company.get('company_color_3', '#93C5FD')
                self.company_color3_var.set(color3)
                if hasattr(self, 'color3_preview'):
                    try:
                        self.color3_preview.config(bg=color3)
                    except tk.TclError:
                        pass

            # Load report settings
            report = all_settings.get('report', {})

            # Set language using the correct variable name
            if hasattr(self, 'language_var'):
                current_lang = report.get('lang', 'en')
                if current_lang == 'de':
                    self.language_var.set('Deutsch')
                else:
                    self.language_var.set('English')

            # Set template
            if hasattr(self, 'template_display_var') and hasattr(self, 'template_mapping'):
                current_db_template = report.get('template', 'default')

                # Map DATABASE template ID to GUI template ID
                db_to_gui_template_mapping = {
                    'default': 'default',           # default -> ReportLab
                    'black-white': 'latex_bw',      # black-white -> LaTeX B&W  
                    'color': 'latex_color'          # color -> LaTeX Color
                }

                # Convert database value to GUI template ID
                gui_template_id = db_to_gui_template_mapping.get(current_db_template, 'default')

                # Map GUI template ID to display name
                gui_template_to_display = {
                    'default': 'Default (ReportLab)',
                    'latex_bw': 'LaTeX Black & White',
                    'latex_color': 'LaTeX Color'
                }

                target_display = gui_template_to_display.get(gui_template_id, 'Default (ReportLab)')

                print(f"Template loading conversion: {current_db_template} -> {gui_template_id} -> {target_display}")

                # Find matching choice in the combo box (with availability suffix)
                for choice in self.template_mapping.keys():
                    if choice.startswith(target_display):
                        self.template_display_var.set(choice)
                        print(f"Set template display to: {choice}")
                        break
                else:
                    print(f"Warning: Could not find template choice starting with '{target_display}'")

            # Set output path using the correct variable name
            if hasattr(self, 'template_output_var'):
                self.template_output_var.set(report.get('default_output_path', './reports/'))

            print("Settings loaded successfully!")

        except Exception as e:
            print(f"Error loading settings: {e}")
            import traceback
            traceback.print_exc()

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

    def apply_language_and_template_settings(self):
        """Apply both language and template settings"""
        if not self.report_manager:
            messagebox.showerror("Error", "Report manager not available")
            return

        try:
            # Get language setting
            language_display = self.language_var.get()
            if language_display == 'Deutsch':
                language_code = 'de'
            else:
                language_code = 'en'

            # Get template setting
            selected_display = self.template_display_var.get()
            if not selected_display or selected_display not in self.template_mapping:
                messagebox.showerror("Error", "Please select a valid template")
                return

            template_id = self.template_mapping[selected_display]
            print(f"Selected template ID: {template_id}, language: {language_code}")

            # Check availability before setting
            available_methods = self.report_manager.get_available_pdf_methods()

            if template_id in ['latex_bw', 'latex_color']:
                if not available_methods.get('latex', False):
                    # Show installation instructions
                    install_msg = f"""LaTeX is required for LaTeX templates but is not installed.

        To install LaTeX:

        Ubuntu/Debian:
        sudo apt update && sudo apt install texlive-latex-base texlive-latex-extra

        After installation, restart the application.

        Would you like to set the template to 'Default (ReportLab)' instead?"""

                    if messagebox.askyesno("LaTeX Not Available", install_msg):
                        template_id = 'default'
                        # Update display
                        for choice in self.template_mapping:
                            if choice.startswith('Default (ReportLab)'):
                                self.template_display_var.set(choice)
                                break
                    else:
                        return

            elif template_id == 'default':
                if not available_methods.get('reportlab', False):
                    messagebox.showerror("ReportLab Not Available", 
                                       "ReportLab is required for the Default template.\n\n"
                                       "Install with: pip install reportlab")
                    return

            # Check if German template exists for LaTeX templates
            if template_id in ['latex_bw', 'latex_color'] and language_code == 'de':
                template_path = self.report_manager.get_template_path(template_id, language_code)
                if not template_path or not os.path.exists(template_path):
                    messagebox.showwarning("German Template Not Found", 
                                         f"German template for {template_id} not found.\n"
                                         f"Will use English template instead.")

            # Map template IDs to database values
            template_db_mapping = {
                'default': 'default',
                'latex_bw': 'black-white',
                'latex_color': 'color'
            }

            db_template_value = template_db_mapping.get(template_id, 'default')
            print(f"Database values - template: {db_template_value}, language: {language_code}")

            # Update via SettingsManager
            success = self.settings_manager.save_report_settings({
                'template': db_template_value,
                'lang': language_code,
                'default_output_path': self.template_output_var.get() if hasattr(self, 'template_output_var') else './reports/'
            })

            if not success:
                messagebox.showerror("Error", "Failed to save settings to database")
                return

            # Verify the settings were saved
            current_settings = self.settings_manager.get_report_settings()
            print(f"Verified database settings: {current_settings}")

            # Update preview
            self.update_language_preview()

            language_name = "German" if language_code == 'de' else "English"
            messagebox.showinfo("Success", f"Settings updated:\n• Language: {language_name}\n• Template: {selected_display.split('(')[0].strip()}")

        except Exception as e:
            print(f"Error applying settings: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to apply settings: {e}")

    def update_language_preview(self, *args):
        """Update the language preview text"""
        if not hasattr(self, 'language_preview_label'):
            return

        language_display = self.language_var.get()
        if language_display == 'Deutsch':
            preview_text = "Monatlicher Arbeitszeitbericht • Mitarbeitername • Gesamtarbeitsstunden"
        else:
            preview_text = "Monthly Time Report • Employee Name • Total Working Hours"

        self.language_preview_label.config(text=preview_text)

    def browse_template_output(self):
        """Browse for template output directory"""
        from tkinter import filedialog
        
        dir_path = filedialog.askdirectory(
            title="Select Report Output Directory",
            initialdir=self.template_output_var.get()
        )
        
        if dir_path:
            self.template_output_var.set(dir_path)

 # =============================================================================
 # UTILITY & HELPER METHODS
 # =============================================================================

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

    def set_to_today(self):
        """Set date fields to today's date"""
        today = date.today()
        self.day_var.set(today.day)
        self.date_month_var.set(today.month)
        self.date_year_var.set(today.year)
        self.update_date_display()

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

    def update_view_period_if_needed(self):
        """Update view period if the selected date is in a different month/year"""
        selected_date = self.date_manager.selected_date
        if (selected_date.month != self.date_manager.view_month or 
            selected_date.year != self.date_manager.view_year):
            
            self.date_manager.set_view_period(selected_date.month, selected_date.year)
            self.period_display_var.set(f"Viewing: {self.date_manager.view_month:02d}/{self.date_manager.view_year}")
            if self.selected_employee:
                self.load_time_records_data()

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

# =============================================================================
# MAIN APPLICATION ENTRY POINT                                                  #TODO:  later edit
# =============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = EmployeeTimeApp(root)
    root.mainloop()