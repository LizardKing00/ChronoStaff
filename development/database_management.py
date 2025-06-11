import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font
import sqlite3
from typing import Dict, Any, Optional
from datetime import datetime, date, timedelta
import calendar
import json
import os
from calendar_popup import CalendarDialog
from typing import Dict, List, Tuple

# =============================================================================
# DATABASE SETUP
# =============================================================================

class DatabaseManager:
    def __init__(self, db_name=None):
        if db_name is None:
            # Default to data/employee_time.db relative to this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)  # Go up one level from development to project root
            db_name = os.path.join(project_root, "data", "employee_time.db") # ./../data/employee_time.db
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        """Initialize database with required tables"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_name), exist_ok=True)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Employees table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                employee_id TEXT UNIQUE NOT NULL,
                position TEXT,
                hourly_rate REAL DEFAULT 0.0,
                email TEXT,
                hire_date DATE,
                hours_per_week REAL DEFAULT 40.0,
                vacation_days_per_year INTEGER DEFAULT 20,
                sick_days_per_year INTEGER DEFAULT 10,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Time records table with German break requirements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                date DATE NOT NULL,
                
                -- Time entries (up to 3 start/end pairs per day)
                start_time_1 TIME,
                end_time_1 TIME,
                start_time_2 TIME,
                end_time_2 TIME,
                start_time_3 TIME,
                end_time_3 TIME,
                
                -- Break calculations
                total_break_time REAL DEFAULT 0.0,  -- Total break time taken (in hours)
                minimum_break_required REAL DEFAULT 0.0,  -- Minimum break required by German law (in hours)
                break_deficit REAL DEFAULT 0.0,  -- If employee didn't take enough break (in hours)
                
                -- Working time calculations
                total_time_present REAL DEFAULT 0.0,  -- Total time from first start to last end (in hours)
                hours_worked REAL DEFAULT 0.0,  -- Actual work time (total_time_present - breaks)
                overtime_hours REAL DEFAULT 0.0,  -- Hours beyond standard working time
                
                record_type TEXT CHECK(record_type IN ('work', 'vacation', 'sick', 'holiday')),
                notes TEXT,
                
                -- Compliance flags
                break_compliance BOOLEAN DEFAULT 1,  -- Whether minimum break requirements were met
                max_working_time_compliance BOOLEAN DEFAULT 1,  -- Whether daily working time limits were respected
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            )
        ''')

        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Report settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lang TEXT CHECK(lang IN ('de', 'en')) DEFAULT 'en',
                template TEXT CHECK(template IN ('default', 'color', 'black-white')) DEFAULT 'default',                
                default_output_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Company data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                companyname TEXT NOT NULL,
                companystreet TEXT,
                companycity TEXT,
                companyphone TEXT,
                companyemail TEXT,
                company_color_1 TEXT CHECK(company_color_1 GLOB '#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]'),
                company_color_2 TEXT CHECK(company_color_2 GLOB '#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]'),
                company_color_3 TEXT CHECK(company_color_3 GLOB '#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]'),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert default settings including German labor law requirements
        default_settings = [
            ('standard_hours_per_day', '8.0'),
            ('overtime_threshold', '200.0'),
            ('vacation_days_per_year', '30'),
            ('sick_days_per_year', '10'),
            ('business_days_per_week', '5'),
            # German labor law settings (Arbeitszeitgesetz - ArbZG)
            ('max_daily_working_hours', '8.0'),  # Standard max 8 hours per day
            ('max_daily_working_hours_extended', '10.0'),  # Extended max 10 hours (with conditions)
            ('min_break_6_hours', '0.5'),  # 30 min break for >6 hours work
            ('min_break_9_hours', '0.75'),  # 45 min break for >9 hours work
            ('min_rest_period_hours', '11.0'),  # 11 hours rest between work days
            ('max_weekly_working_hours', '48.0')  # Max 48 hours per week average over 6 months
        ]

        cursor.executemany('''
            INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
        ''', default_settings)

        # Insert default report settings (only if no record exists)
        cursor.execute('''
            INSERT OR IGNORE INTO report_settings (id, lang, template, default_output_path) 
            VALUES (1, 'en', 'color', './reports/')
        ''')

        # Insert default company data (only if no record exists)
        cursor.execute('''
            INSERT OR IGNORE INTO company_data (
                id, companyname, companystreet, companycity, companyphone, companyemail,
                company_color_1, company_color_2, company_color_3
            ) VALUES (
                1, 'Meine Firma GmbH', 'Geschäftsstraße 123', '10115 Berlin', 
                '+49-30-1234567', 'contact@meinefirma.com', '#1E40AF', '#3B82F6', '#93C5FD'
            )
        ''')

        conn.commit()
        conn.close()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)

# =============================================================================
# EMPLOYEE MANAGEMENT CLASS
# =============================================================================

class EmployeeManager:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def add_employee(self, name, employee_id, position="", hourly_rate=0.0, 
                    email="", hours_per_week=40.0, vacation_days=20, sick_days=10):
        """Add new employee to database"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO employees (name, employee_id, position, hourly_rate, email, 
                                     hire_date, hours_per_week, vacation_days_per_year, sick_days_per_year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, employee_id, position, hourly_rate, email, date.today(), 
                  hours_per_week, vacation_days, sick_days))
            conn.commit()
            return True, "Employee added successfully"
        except sqlite3.IntegrityError:
            return False, "Employee ID already exists"
        except Exception as e:
            return False, f"Error adding employee: {str(e)}"
        finally:
            conn.close()
    
    def get_all_employees(self, include_inactive=False):
        """Get all employees (active by default)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if include_inactive:
            cursor.execute('SELECT * FROM employees ORDER BY name')
        else:
            cursor.execute('SELECT * FROM employees WHERE active = 1 ORDER BY name')
        
        employees = cursor.fetchall()
        conn.close()
        return employees
    
    def update_employee(self, emp_id, **kwargs):
        """Properly update employee information in database"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            # Build the update query dynamically based on provided kwargs
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(emp_id)  # Add emp_id for WHERE clause

            query = f"UPDATE employees SET {set_clause} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()

    def remove_employee(self, emp_id, permanent=False):
        """Remove employee (soft delete by default, permanent if specified)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            if permanent:
                # Permanently delete employee and all associated records
                cursor.execute('DELETE FROM time_records WHERE employee_id = ?', (emp_id,))
                cursor.execute('DELETE FROM employees WHERE id = ?', (emp_id,))
                message = "Employee permanently deleted"
            else:
                # Soft delete (mark as inactive)
                cursor.execute('UPDATE employees SET active = 0 WHERE id = ?', (emp_id,))
                message = "Employee deactivated"
            
            conn.commit()
            return True, message
        except sqlite3.Error as e:
            conn.rollback()
            return False, f"Database error: {str(e)}"
        finally:
            conn.close()
    
    def reactivate_employee(self, emp_id):
        """Reactivate a deactivated employee"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE employees SET active = 1 WHERE id = ?', (emp_id,))
            conn.commit()
            return True, "Employee reactivated"
        except sqlite3.Error as e:
            conn.rollback()
            return False, f"Database error: {str(e)}"
        finally:
            conn.close()

# =============================================================================
# TIME TRACKING CLASS
# =============================================================================

class TimeTracker:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def add_time_record(self, employee_id, record_date, start_times=None, end_times=None,
                       record_type='work', notes=""):
        """
        Add time record for employee with multiple start/end times
        
        Args:
            employee_id (int): Employee ID
            record_date (str): Date in YYYY-MM-DD format
            start_times (list): List of start times ['HH:MM', 'HH:MM', 'HH:MM'] (max 3)
            end_times (list): List of end times ['HH:MM', 'HH:MM', 'HH:MM'] (max 3)
            record_type (str): 'work', 'vacation', 'sick', 'holiday'
            notes (str): Additional notes
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get employee's hours per week to calculate daily standard hours
        cursor.execute('SELECT hours_per_week FROM employees WHERE id = ? AND active = 1', (employee_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False, "Employee not found or inactive"
        
        standard_daily_hours = result[0] / 5.0  # assuming 5 work days per week
        
        # Initialize time values
        calculated_values = {
            'total_time_present': 0.0,
            'total_break_time': 0.0,
            'hours_worked': 0.0,
            'minimum_break_required': 0.0,
            'max_working_time_compliance': True,
            'overtime_hours': 0.0
        }
        
        # For work records, calculate time values
        print(f"NOW CHECKING Record Time:\n\trecord_type:'{record_type}'")
        if record_type == 'work' and start_times and end_times:
            # Ensure we have valid start/end time pairs (max 3)
            start_times = (start_times or [])[:3]
            end_times = (end_times or [])[:3]
            
            # Calculate working hours and breaks using the database manager method
            calculated_values = self.calculate_time_entry(start_times, end_times)
            
            # Calculate overtime based on standard daily hours
            if calculated_values['hours_worked'] > standard_daily_hours:
                calculated_values['overtime_hours'] = calculated_values['hours_worked'] - standard_daily_hours
        
        try:
            # Prepare time fields (pad with None if less than 3 entries)
            time_fields = [None] * 6  # 3 start times + 3 end times
            if start_times:
                for i, time_val in enumerate(start_times[:3]):
                    if time_val:
                        time_fields[i*2] = time_val  # start_time_1, start_time_2, start_time_3
            if end_times:
                for i, time_val in enumerate(end_times[:3]):
                    if time_val:
                        time_fields[i*2 + 1] = time_val  # end_time_1, end_time_2, end_time_3
            
            cursor.execute('''
                INSERT OR REPLACE INTO time_records 
                (employee_id, date, start_time_1, end_time_1, start_time_2, end_time_2, 
                 start_time_3, end_time_3, total_break_time, minimum_break_required, 
                 total_time_present, hours_worked, overtime_hours, record_type, notes,
                 max_working_time_compliance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (employee_id, record_date, *time_fields, 
                  calculated_values['total_break_time'], calculated_values['minimum_break_required'],
                  calculated_values['total_time_present'], calculated_values['hours_worked'], 
                  calculated_values['overtime_hours'], record_type, notes,
                  calculated_values['max_working_time_compliance']))
            
            conn.commit()
            return True, "Time record added successfully"
        except Exception as e:
            return False, f"Error adding time record: {str(e)}"
        finally:
            conn.close()
    
    def get_time_records(self, employee_id=None, start_date=None, end_date=None):
        """Get time records with optional filters"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM time_records'
        params = []
        conditions = []
        
        if employee_id:
            conditions.append('employee_id = ?')
            params.append(employee_id)
        
        if start_date:
            conditions.append('date >= ?')
            params.append(start_date)
        
        if end_date:
            conditions.append('date <= ?')
            params.append(end_date)
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY date DESC'
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        conn.close()
        return records
        
    def calculate_period_summary(self, employee_id, start_date, end_date):
        """Calculate summary for any date period"""
        records = self.get_time_records(employee_id, start_date, end_date)
        
        # Get employee settings
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT hours_per_week, vacation_days_per_year, sick_days_per_year, hourly_rate, name
            FROM employees WHERE id = ?
        ''', (employee_id,))
        emp_data = cursor.fetchone()
        conn.close()
        
        if not emp_data:
            return None
        
        hours_per_week, vacation_allowance, sick_allowance, hourly_rate, emp_name = emp_data
        
        summary = {
            'employee_name': emp_name,
            'period_start': str(start_date),
            'period_end': str(end_date),
            'total_work_hours': 0.0,
            'total_overtime': 0.0,
            'total_break_time': 0.0,
            'total_time_present': 0.0,
            'vacation_days': 0,
            'sick_days': 0,
            'holiday_days': 0,
            'work_days': 0,
            'hours_per_week': hours_per_week,
            'hourly_rate': hourly_rate,
            'regular_pay': 0.0,
            'overtime_pay': 0.0,
            'total_pay': 0.0,
            'break_compliance_violations': 0,
            'working_time_violations': 0
        }
        
        # Process records - updated column indices for new schema
        for record in records:
            # New column order: id, employee_id, date, start_time_1, end_time_1, start_time_2, 
            # end_time_2, start_time_3, end_time_3, total_break_time, minimum_break_required,
            # total_time_present, hours_worked, overtime_hours, record_type, notes, max_working_time_compliance
            record_type = record[14]  # record_type column
            hours = record[12] or 0.0        # hours_worked column
            overtime = record[13] or 0.0     # overtime_hours column
            total_break_time = record[9] or 0.0    # total_break_time column
            time_present = record[11] or 0.0 # total_time_present column
            min_break_req = record[10] or 0.0 # minimum_break_required column
            max_time_compliance = record[16] # max_working_time_compliance column
            
            if record_type == 'work':
                summary['total_work_hours'] += hours
                summary['total_overtime'] += overtime
                summary['total_break_time'] += total_break_time
                summary['total_time_present'] += time_present
                summary['work_days'] += 1
                
                # Check compliance violations
                if total_break_time < min_break_req:
                    summary['break_compliance_violations'] += 1
                if not max_time_compliance:
                    summary['working_time_violations'] += 1
                    
            elif record_type == 'vacation':
                summary['vacation_days'] += 1
            elif record_type == 'sick':
                summary['sick_days'] += 1
            elif record_type == 'holiday':
                summary['holiday_days'] += 1
        
        # Calculate pay
        regular_hours = summary['total_work_hours'] - summary['total_overtime']
        summary['regular_pay'] = regular_hours * hourly_rate
        summary['overtime_pay'] = summary['total_overtime'] * hourly_rate * 1.5  # 1.5x overtime rate
        summary['total_pay'] = summary['regular_pay'] + summary['overtime_pay']
        
        return summary
    
    def calculate_monthly_summary(self, employee_id, year, month):
        """Calculate monthly summary for employee"""
        from datetime import date, timedelta
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        summary = self.calculate_period_summary(employee_id, start_date, end_date)
        
        if summary:
            # Add year-to-date calculations
            ytd_summary = self.calculate_yearly_summary(employee_id, year)
            if ytd_summary:
                summary['vacation_days_used_ytd'] = ytd_summary['vacation_days']
                summary['sick_days_used_ytd'] = ytd_summary['sick_days']
                summary['vacation_days_remaining'] = max(0, ytd_summary['vacation_allowance'] - ytd_summary['vacation_days'])
                summary['sick_days_remaining'] = max(0, ytd_summary['sick_allowance'] - ytd_summary['sick_days'])
        
        return summary
    
    def calculate_yearly_summary(self, employee_id, year):
        """Calculate yearly summary for employee"""
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        summary = self.calculate_period_summary(employee_id, start_date, end_date)
        
        if summary:
            # Get employee allowances
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT vacation_days_per_year, sick_days_per_year
                FROM employees WHERE id = ?
            ''', (employee_id,))
            allowances = cursor.fetchone()
            conn.close()
            
            if allowances:
                summary['vacation_allowance'] = allowances[0]
                summary['sick_allowance'] = allowances[1]
                summary['vacation_days_remaining'] = max(0, allowances[0] - summary['vacation_days'])
                summary['sick_days_remaining'] = max(0, allowances[1] - summary['sick_days'])
        
        return summary
    
    def delete_time_record(self, record_id):
        """Delete a time record"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM time_records WHERE id = ?', (record_id,))
            conn.commit()
            return True, "Time record deleted successfully"
        except Exception as e:
            return False, f"Error deleting time record: {str(e)}"
        finally:
            conn.close()
    
    def update_time_record(self, record_id, start_times=None, end_times=None, **kwargs):
        """
        Update a time record with new start/end times or other fields
        
        Args:
            record_id (int): Record ID to update
            start_times (list): List of start times (max 3)
            end_times (list): List of end times (max 3)
            **kwargs: Other fields to update (date, record_type, notes)
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get current record data
        cursor.execute('SELECT * FROM time_records WHERE id = ?', (record_id,))
        current_record = cursor.fetchone()
        
        if not current_record:
            conn.close()
            return False, "Time record not found"
        
        # Get employee's standard daily hours for overtime calculation
        cursor.execute('''
            SELECT hours_per_week FROM employees 
            WHERE id = (SELECT employee_id FROM time_records WHERE id = ?)
        ''', (record_id,))
        emp_result = cursor.fetchone()
        standard_daily_hours = emp_result[0] / 5.0 if emp_result else 8.0
        
        valid_fields = ['date', 'record_type', 'notes']
        fields = []
        values = []
        
        # Handle regular field updates
        for key, value in kwargs.items():
            if key in valid_fields:
                fields.append(f"{key} = ?")
                values.append(value)
        
        # Handle time updates if provided
        if start_times is not None or end_times is not None:
            # Use current times if not provided
            current_start_times = [current_record[3], current_record[5], current_record[7]]  # start_time_1,2,3
            current_end_times = [current_record[4], current_record[6], current_record[8]]    # end_time_1,2,3
            
            # Filter out None values and convert to list
            current_start_times = [t for t in current_start_times if t is not None]
            current_end_times = [t for t in current_end_times if t is not None]
            
            if start_times is None:
                start_times = current_start_times
            if end_times is None:
                end_times = current_end_times
            
            # Recalculate time values
            calculated_values = self.calculate_time_entry(start_times, end_times)
            
            # Calculate overtime
            if calculated_values['hours_worked'] > standard_daily_hours:
                calculated_values['overtime_hours'] = calculated_values['hours_worked'] - standard_daily_hours
            
            # Update time fields (pad with None if less than 3 entries)
            time_fields = [None] * 6  # 3 start times + 3 end times
            if start_times:
                for i, time_val in enumerate(start_times[:3]):
                    if time_val:
                        time_fields[i*2] = time_val
            if end_times:
                for i, time_val in enumerate(end_times[:3]):
                    if time_val:
                        time_fields[i*2 + 1] = time_val
            
            # Add time field updates
            time_field_names = ['start_time_1', 'end_time_1', 'start_time_2', 
                               'end_time_2', 'start_time_3', 'end_time_3']
            for i, field_name in enumerate(time_field_names):
                fields.append(f"{field_name} = ?")
                values.append(time_fields[i])
            
            # Add calculated field updates
            calc_fields = ['total_break_time', 'minimum_break_required', 'total_time_present', 
                          'hours_worked', 'overtime_hours', 'max_working_time_compliance']
            calc_values = [calculated_values['total_break_time'], calculated_values['minimum_break_required'],
                          calculated_values['total_time_present'], calculated_values['hours_worked'],
                          calculated_values['overtime_hours'], calculated_values['max_working_time_compliance']]
            
            for field, value in zip(calc_fields, calc_values):
                fields.append(f"{field} = ?")
                values.append(value)
        
        if fields:
            fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(record_id)
            query = f"UPDATE time_records SET {', '.join(fields)} WHERE id = ?"
            
            try:
                cursor.execute(query, values)
                conn.commit()
                return True, "Time record updated successfully"
            except Exception as e:
                return False, f"Error updating time record: {str(e)}"
        
        conn.close()
        return False, "No valid fields to update"
    
    def get_daily_time_details(self, employee_id, record_date):
        """Get detailed time information for a specific day"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT start_time_1, end_time_1, start_time_2, end_time_2, start_time_3, end_time_3,
                   total_break_time, minimum_break_required, total_time_present, hours_worked, 
                   overtime_hours, max_working_time_compliance, record_type, notes
            FROM time_records 
            WHERE employee_id = ? AND date = ?
        ''', (employee_id, record_date))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        return {
            'start_times': [result[0], result[2], result[4]],
            'end_times': [result[1], result[3], result[5]],
            'total_break_time': result[6],
            'minimum_break_required': result[7],
            'total_time_present': result[8],
            'hours_worked': result[9],
            'overtime_hours': result[10],
            'max_working_time_compliance': result[11],
            'record_type': result[12],
            'notes': result[13]
        }

    def calculate_german_break_requirements(self, total_working_hours):
        """
        Calculate minimum break requirements according to German labor law (ArbZG §4)
        
        Args:
            total_working_hours (float): Total working hours for the day
            
        Returns:
            float: Minimum break time required in hours
        """
        if total_working_hours > 9:
            return 0.75  # 45 minutes for more than 9 hours
        elif total_working_hours > 6:
            return 0.5   # 30 minutes for more than 6 hours
        else:
            return 0.0   # No mandatory break for 6 hours or less

    def calculate_time_entry(self, start_times, end_times, break_times=None):
        """
        Calculate working hours, breaks, and compliance for a day's time entries
        
        Args:
            start_times (list): List of start times (up to 3)
            end_times (list): List of end times (up to 3)
            break_times (list, optional): Manual break times if provided
            
        Returns:
            dict: Calculated values for database insertion
        """
        from datetime import datetime, timedelta
        
        # Convert time strings to datetime objects for calculation
        work_periods = []
        for i in range(min(len(start_times), len(end_times))):
            if start_times[i] and end_times[i]:
                start = datetime.strptime(start_times[i], '%H:%M')
                end = datetime.strptime(end_times[i], '%H:%M')
                if end > start:
                    work_periods.append((start, end))
        
        if not work_periods:
            return {
                'total_time_present': 0.0,
                'total_break_time': 0.0,
                'hours_worked': 0.0,
                'minimum_break_required': 0.0,
                'break_deficit': 0.0,
                'break_compliance': True,
                'max_working_time_compliance': True,
                'overtime_hours': 0.0
            }
        
        # Calculate total time present (from first start to last end)
        first_start = min(period[0] for period in work_periods)
        last_end = max(period[1] for period in work_periods)
        total_time_present = (last_end - first_start).total_seconds() / 3600.0
        
        # Calculate actual work time (sum of all work periods)
        total_work_time = sum((end - start).total_seconds() / 3600.0 for start, end in work_periods)
        
        # Calculate break time (time present - actual work time)
        total_break_time = total_time_present - total_work_time
        
        # Calculate minimum break required
        minimum_break_required = self.calculate_german_break_requirements(total_work_time)
        
        # Check break compliance
        break_deficit = max(0, minimum_break_required - total_break_time)
        break_compliance = break_deficit == 0
        
        # Adjust hours worked if break deficit exists
        hours_worked = total_work_time - break_deficit
        
        # Calculate overtime (assuming 8 hours standard day)
        standard_hours = 8.0
        overtime_hours = max(0, hours_worked - standard_hours)
        
        # Check max working time compliance (10 hours max per day)
        max_working_time_compliance = total_work_time <= 10.0
        
        return {
            'total_time_present': round(total_time_present, 2),
            'total_break_time': round(total_break_time, 2),
            'hours_worked': round(hours_worked, 2),
            'minimum_break_required': round(minimum_break_required, 2),
            'break_deficit': round(break_deficit, 2),
            'break_compliance': break_compliance,
            'max_working_time_compliance': max_working_time_compliance,
            'overtime_hours': round(overtime_hours, 2)
        }

# =============================================================================
# SETTINGS MANAGEMENT CLASS
# =============================================================================

class SettingsManager:
    """
    Manages all application settings including general settings, company data, and report settings.
    Provides a clean interface between the GUI and database.
    """
    
    def __init__(self, db_manager):
        """
        Initialize SettingsManager with a database manager instance.
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
    
    def get_general_settings(self) -> Dict[str, Any]:
        """
        Retrieve all general settings from the settings table.
        
        Returns:
            Dict with setting keys and their values (converted to appropriate types)
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT key, value FROM settings")
            rows = cursor.fetchall()
            
            settings = {}
            for key, value in rows:
                # Convert values to appropriate types
                if key in ['standard_hours_per_day', 'overtime_threshold']:
                    settings[key] = float(value)
                elif key in ['vacation_days_per_year', 'sick_days_per_year', 'business_days_per_week']:
                    settings[key] = int(value)
                else:
                    settings[key] = value
                    
            return settings
            
        except sqlite3.Error as e:
            print(f"Error retrieving general settings: {e}")
            return {}
        finally:
            conn.close()
    
    def save_general_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Save general settings to the settings table.
        
        Args:
            settings: Dictionary of setting key-value pairs
            
        Returns:
            True if successful, False otherwise
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            for key, value in settings.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO settings (key, value, updated_at) 
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (key, str(value)))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Error saving general settings: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_company_data(self) -> Dict[str, Any]:
        """
        Retrieve company data from the database.
        
        Returns:
            Dict with company information, or empty dict if none found
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT companyname, companystreet, companycity, companyphone, companyemail,
                       company_color_1, company_color_2, company_color_3
                FROM company_data 
                WHERE id = 1
            ''')
            
            row = cursor.fetchone()
            if row:
                return {
                    'companyname': row[0] or '',
                    'companystreet': row[1] or '',
                    'companycity': row[2] or '',
                    'companyphone': row[3] or '',
                    'companyemail': row[4] or '',
                    'company_color_1': row[5] or '#1E40AF',
                    'company_color_2': row[6] or '#3B82F6',
                    'company_color_3': row[7] or '#93C5FD'
                }
            else:
                return {}
                
        except sqlite3.Error as e:
            print(f"Error retrieving company data: {e}")
            return {}
        finally:
            conn.close()
    
    def save_company_data(self, company_data: Dict[str, str]) -> bool:
        """
        Save company data to the database.
        
        Args:
            company_data: Dictionary with company information
            
        Returns:
            True if successful, False otherwise
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO company_data (
                    id, companyname, companystreet, companycity, companyphone, companyemail,
                    company_color_1, company_color_2, company_color_3, updated_at
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                company_data.get('companyname', ''),
                company_data.get('companystreet', ''),
                company_data.get('companycity', ''),
                company_data.get('companyphone', ''),
                company_data.get('companyemail', ''),
                company_data.get('company_color_1', '#1E40AF'),
                company_data.get('company_color_2', '#3B82F6'),
                company_data.get('company_color_3', '#93C5FD')
            ))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Error saving company data: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_report_settings(self) -> Dict[str, Any]:
        """
        Retrieve report settings from the database.
        
        Returns:
            Dict with report settings, or defaults if none found
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT lang, template, default_output_path
                FROM report_settings 
                WHERE id = 1
            ''')
            
            row = cursor.fetchone()
            if row:
                return {
                    'lang': row[0] or 'en',
                    'template': row[1] or 'color',
                    'default_output_path': row[2] or './reports/'
                }
            else:
                return {
                    'lang': 'en',
                    'template': 'color',
                    'default_output_path': './reports/'
                }
                
        except sqlite3.Error as e:
            print(f"Error retrieving report settings: {e}")
            return {
                'lang': 'en',
                'template': 'color',
                'default_output_path': './reports/'
            }
        finally:
            conn.close()
    
    def save_report_settings(self, report_settings: Dict[str, str]) -> bool:
        """
        Save report settings to the database.
        
        Args:
            report_settings: Dictionary with report settings
            
        Returns:
            True if successful, False otherwise
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO report_settings (
                    id, lang, template, default_output_path, updated_at
                ) VALUES (1, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                report_settings.get('lang', 'en'),
                report_settings.get('template', 'color'),
                report_settings.get('default_output_path', './reports/')
            ))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Error saving report settings: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def load_all_settings(self) -> Dict[str, Any]:
        """
        Load all settings from the database at once.
        
        Returns:
            Dict containing all settings organized by category
        """
        return {
            'general': self.get_general_settings(),
            'company': self.get_company_data(),
            'report': self.get_report_settings()
        }
    
    def save_all_settings(self, general_settings: Dict[str, Any], 
                         company_data: Dict[str, str], 
                         report_settings: Dict[str, str]) -> bool:
        """
        Save all settings to the database in a single transaction.
        
        Args:
            general_settings: General application settings
            company_data: Company information
            report_settings: Report generation settings
            
        Returns:
            True if all saves successful, False otherwise
        """
        success = True
        success &= self.save_general_settings(general_settings)
        success &= self.save_company_data(company_data)
        success &= self.save_report_settings(report_settings)
        
        return success
    
    def reset_to_defaults(self) -> bool:
        """
        Reset all settings to their default values.
        
        Returns:
            True if successful, False otherwise
        """
        # Default general settings
        default_general = {
            'standard_hours_per_day': 8.0,
            'overtime_threshold': 200.0,
            'vacation_days_per_year': 30,
            'sick_days_per_year': 10,
            'business_days_per_week': 5
        }
        
        # Default company data
        default_company = {
            'companyname': 'Meine Firma GmbH',
            'companystreet': 'Geschäftsstraße 123',
            'companycity': '10115 Berlin',
            'companyphone': '+49-30-1234567',
            'companyemail': 'contact@meinefirma.com',
            'company_color_1': '#1E40AF',
            'company_color_2': '#3B82F6',
            'company_color_3': '#93C5FD'
        }
        
        # Default report settings
        default_report = {
            'lang': 'en',
            'template': 'color',
            'default_output_path': './reports/'
        }
        
        return self.save_all_settings(default_general, default_company, default_report)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a single setting value by key.
        
        Args:
            key: Setting key to retrieve
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        settings = self.get_general_settings()
        return settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> bool:
        """
        Set a single setting value.
        
        Args:
            key: Setting key
            value: Setting value
            
        Returns:
            True if successful, False otherwise
        """
        return self.save_general_settings({key: value})