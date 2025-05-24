import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font
import sqlite3
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
        
        # Insert default settings
        default_settings = [
            ('standard_hours_per_day', '8.0'),
            ('overtime_threshold', '40.0'),
            ('vacation_days_per_year', '20'),
            ('sick_days_per_year', '10'),
            ('business_days_per_week', '5')
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
        ''', default_settings)
        
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
    
    def update_employee(self, emp_id, **kwargs):
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
                cursor.execute('UPDATE employees SET active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (emp_id,))
                message = "Employee deactivated"
            
            conn.commit()
            return True, message
        except Exception as e:
            return False, f"Error removing employee: {str(e)}"
        finally:
            conn.close()
    
    def reactivate_employee(self, emp_id):
        """Reactivate a deactivated employee"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('UPDATE employees SET active = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (emp_id,))
            conn.commit()
            return True, "Employee reactivated successfully"
        except Exception as e:
            return False, f"Error reactivating employee: {str(e)}"
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