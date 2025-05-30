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

# =============================================================================
# DATABASE SETUP
# =============================================================================

class DatabaseManager:
    def __init__(self, db_name="data/employee_time.db"):
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

        # Time records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                date DATE NOT NULL,
                hours_worked REAL DEFAULT 0.0,
                overtime_hours REAL DEFAULT 0.0,
                record_type TEXT CHECK(record_type IN ('work', 'vacation', 'sick', 'holiday')),
                notes TEXT,
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
                template TEXT CHECK(template IN ('color', 'black-white')) DEFAULT 'color',
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

        # Insert default settings
        default_settings = [
            ('standard_hours_per_day', '8.0'),
            ('overtime_threshold', '200.0'),
            ('vacation_days_per_year', '30'),
            ('sick_days_per_year', '10'),
            ('business_days_per_week', '5')
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
    
    def get_employee_by_id(self, emp_id):
        """Get specific employee by ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM employees WHERE id = ?', (emp_id,))
        employee = cursor.fetchone()
        conn.close()
        return employee
    
    def _update_employee(self, emp_id, **kwargs):
        """Update employee information"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Build dynamic update query
        fields = []
        values = []
        valid_fields = ['name', 'employee_id', 'position', 'hourly_rate', 'email', 
                       'hours_per_week', 'vacation_days_per_year', 'sick_days_per_year']
        
        for key, value in kwargs.items():
            if key in valid_fields:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if fields:
            # Add updated timestamp
            fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(emp_id)
            query = f"UPDATE employees SET {', '.join(fields)} WHERE id = ?"
            
            try:
                cursor.execute(query, values)
                conn.commit()
                return True, "Employee updated successfully"
            except sqlite3.IntegrityError:
                return False, "Employee ID already exists"
            except Exception as e:
                return False, f"Error updating employee: {str(e)}"
        
        conn.close()
        return False, "No valid fields to update"
    
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

    def get_employee_settings(self, employee_id):
        """Get employee-specific settings"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT hours_per_week, vacation_days_per_year, sick_days_per_year, hourly_rate 
            FROM employees WHERE id = ?
        ''', (employee_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'hours_per_week': result[0],
                'vacation_days_per_year': result[1],
                'sick_days_per_year': result[2],
                'hourly_rate': result[3]
            }
        return None
    
    def export_employee_data(self, employee_ids=None, include_time_records=True):
        """Export employee data to JSON format"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get employees
        if employee_ids:
            placeholders = ','.join(['?'] * len(employee_ids))
            cursor.execute(f'SELECT * FROM employees WHERE id IN ({placeholders})', employee_ids)
        else:
            cursor.execute('SELECT * FROM employees')
        
        employees = cursor.fetchall()
        
        # Get column names for employees table
        cursor.execute("PRAGMA table_info(employees)")
        emp_columns = [col[1] for col in cursor.fetchall()]
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'employees': []
        }
        
        for emp_row in employees:
            employee_data = dict(zip(emp_columns, emp_row))
            
            # Convert dates to strings for JSON serialization
            if employee_data.get('hire_date'):
                employee_data['hire_date'] = str(employee_data['hire_date'])
            if employee_data.get('created_at'):
                employee_data['created_at'] = str(employee_data['created_at'])
            if employee_data.get('updated_at'):
                employee_data['updated_at'] = str(employee_data['updated_at'])
            
            if include_time_records:
                # Get time records for this employee
                cursor.execute('SELECT * FROM time_records WHERE employee_id = ? ORDER BY date', (emp_row[0],))
                time_records = cursor.fetchall()
                
                # Get column names for time_records table
                cursor.execute("PRAGMA table_info(time_records)")
                time_columns = [col[1] for col in cursor.fetchall()]
                
                employee_data['time_records'] = []
                for record_row in time_records:
                    record_data = dict(zip(time_columns, record_row))
                    # Convert dates to strings
                    if record_data.get('date'):
                        record_data['date'] = str(record_data['date'])
                    if record_data.get('created_at'):
                        record_data['created_at'] = str(record_data['created_at'])
                    if record_data.get('updated_at'):
                        record_data['updated_at'] = str(record_data['updated_at'])
                    
                    employee_data['time_records'].append(record_data)
            
            export_data['employees'].append(employee_data)
        
        conn.close()
        return export_data
    
    def save_export_to_file(self, data, filename=None):
        """Save export data to JSON file"""
        if not filename:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Save Employee Data"
            )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                return True, f"Data exported to {filename}"
            except Exception as e:
                return False, f"Error saving file: {str(e)}"
        return False, "Export cancelled"

# =============================================================================
# TIME TRACKING CLASS
# =============================================================================

class TimeTracker:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def add_time_record(self, employee_id, record_date, hours_worked=0.0, 
                       record_type='work', notes=""):
        """Add time record for employee"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get employee's hours per week to calculate daily standard hours
        cursor.execute('SELECT hours_per_week FROM employees WHERE id = ? AND active = 1', (employee_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False, "Employee not found or inactive"
        
        standard_daily_hours = result[0] / 5.0  # assuming 5 work days per week
        
        # Calculate overtime if work record
        overtime_hours = 0.0
        if record_type == 'work' and hours_worked > standard_daily_hours:
            overtime_hours = hours_worked - standard_daily_hours
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO time_records 
                (employee_id, date, hours_worked, overtime_hours, record_type, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (employee_id, record_date, hours_worked, overtime_hours, record_type, notes))
            
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
    
    def get_monthly_records(self, employee_id, year, month):
        """Get all records for employee for specific month"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        return self.get_time_records(employee_id, start_date, end_date)
    
    def get_yearly_records(self, employee_id, year):
        """Get all records for employee for specific year"""
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        return self.get_time_records(employee_id, start_date, end_date)
    
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
            'vacation_days': 0,
            'sick_days': 0,
            'holiday_days': 0,
            'work_days': 0,
            'hours_per_week': hours_per_week,
            'hourly_rate': hourly_rate,
            'regular_pay': 0.0,
            'overtime_pay': 0.0,
            'total_pay': 0.0
        }
        
        # Process records
        for record in records:
            record_type = record[5]  # record_type column
            hours = record[3] or 0.0        # hours_worked column
            overtime = record[4] or 0.0     # overtime_hours column
            
            if record_type == 'work':
                summary['total_work_hours'] += hours
                summary['total_overtime'] += overtime
                summary['work_days'] += 1
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
    
    def update_time_record(self, record_id, **kwargs):
        """Update a time record"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        valid_fields = ['date', 'hours_worked', 'record_type', 'notes']
        fields = []
        values = []
        
        for key, value in kwargs.items():
            if key in valid_fields:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if fields:
            # Recalculate overtime if hours_worked is being updated
            if 'hours_worked' in kwargs:
                # Get employee's standard daily hours
                cursor.execute('''
                    SELECT e.hours_per_week, tr.record_type 
                    FROM employees e 
                    JOIN time_records tr ON e.id = tr.employee_id 
                    WHERE tr.id = ?
                ''', (record_id,))
                result = cursor.fetchone()
                
                if result:
                    hours_per_week, record_type = result
                    standard_daily_hours = hours_per_week / 5.0
                    
                    if record_type == 'work' or kwargs.get('record_type') == 'work':
                        overtime = max(0, kwargs['hours_worked'] - standard_daily_hours)
                        fields.append("overtime_hours = ?")
                        values.append(overtime)
            
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

# =============================================================================
# EMPLOYEE MANAGEMENT CLASS
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