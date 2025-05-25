import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import calendar
import subprocess
import os
import tempfile
import shutil

class ReportManager:
    """
    Manages the generation of LaTeX time reports from database data.
    Replaces placeholders in the LaTeX template with actual employee and time data.
    """
    
    def __init__(self, db_path: str, template_path: str):
        """
        Initialize the ReportManager.
        
        Args:
            db_path: Path to the SQLite database file
            template_path: Path to the LaTeX template file
        """
        self.db_path = db_path
        self.template_path = template_path
        
    def connect_db(self) -> sqlite3.Connection:
        """Create and return a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def get_company_info(self) -> Dict[str, str]:
        """
        Retrieve company information from settings table.
        
        Returns:
            Dictionary containing company information
        """
        with self.connect_db() as conn:
            cursor = conn.cursor()
            
            # Get all settings
            cursor.execute("SELECT key, value FROM settings")
            settings = dict(cursor.fetchall())
            
            # Default company info if not in settings
            default_info = {
                'company_name': 'My Company GmbH',
                'company_street': 'Businessstraße 123',
                'company_city': '10115 Berlin',
                'company_phone': '+49-30-1234567',
                'company_email': 'contact@mycompany.com',
                'company_logo': 'company_logo.png',
                'primary_color': '2B579A',
                'secondary_color': '00A4EF',
                'tertiary_color': '00A4EF'
            }
            
            # Update with settings from database
            for key, default_value in default_info.items():
                default_info[key] = settings.get(key, default_value)
                
            return default_info
    
    def get_employee_info(self, employee_id: int) -> Dict[str, str]:
        """
        Retrieve employee information.
        
        Args:
            employee_id: Employee ID from the database
            
        Returns:
            Dictionary containing employee information
        """
        with self.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, employee_id 
                FROM employees 
                WHERE id = ? AND active = 1
            """, (employee_id,))
            
            employee = cursor.fetchone()
            if not employee:
                raise ValueError(f"Employee with ID {employee_id} not found or inactive")
                
            return {
                'name': employee['name'],
                'employee_number': employee['employee_id']
            }
    
    def get_time_records(self, employee_id: int, year: int, month: int) -> List[Dict]:
        """
        Retrieve time records for a specific employee and month.
        
        Args:
            employee_id: Employee ID from the database
            year: Year for the report
            month: Month for the report (1-12)
            
        Returns:
            List of time record dictionaries
        """
        with self.connect_db() as conn:
            cursor = conn.cursor()
            
            # Get all days in the month
            days_in_month = calendar.monthrange(year, month)[1]
            start_date = f"{year}-{month:02d}-01"
            end_date = f"{year}-{month:02d}-{days_in_month:02d}"
            
            cursor.execute("""
                SELECT date, hours_worked, overtime_hours, record_type, notes
                FROM time_records 
                WHERE employee_id = ? 
                AND date BETWEEN ? AND ?
                ORDER BY date
            """, (employee_id, start_date, end_date))
            
            records = cursor.fetchall()
            
            # Convert to list of dictionaries and fill missing dates
            time_data = []
            record_dict = {record['date']: record for record in records}
            
            for day in range(1, days_in_month + 1):
                date_str = f"{year}-{month:02d}-{day:02d}"
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                
                if date_str in record_dict:
                    record = record_dict[date_str]
                    time_data.append({
                        'date': date_obj.strftime("%d.%m.%Y"),
                        'start_time': '09:00',  # Default start time
                        'end_time': self._calculate_end_time('09:00', record['hours_worked']),
                        'total_minutes': int(record['hours_worked'] * 60),
                        'break_minutes': 30 if record['hours_worked'] > 6 else 0,
                        'is_vacation': record['record_type'] == 'vacation',
                        'is_sick': record['record_type'] == 'sick',
                        'hours_worked': record['hours_worked']
                    })
                else:
                    # Weekend or no record
                    weekday = date_obj.weekday()
                    if weekday < 5:  # Monday to Friday
                        time_data.append({
                            'date': date_obj.strftime("%d.%m.%Y"),
                            'start_time': '-',
                            'end_time': '-',
                            'total_minutes': 0,
                            'break_minutes': 0,
                            'is_vacation': False,
                            'is_sick': False,
                            'hours_worked': 0
                        })
            
            return time_data
    
    def _calculate_end_time(self, start_time: str, hours_worked: float) -> str:
        """
        Calculate end time based on start time and hours worked.
        
        Args:
            start_time: Start time in HH:MM format
            hours_worked: Number of hours worked
            
        Returns:
            End time in HH:MM format
        """
        if hours_worked == 0:
            return '-'
            
        start_hour, start_minute = map(int, start_time.split(':'))
        start_datetime = datetime(2000, 1, 1, start_hour, start_minute)
        
        # Add worked hours plus break time
        break_time = 0.5 if hours_worked > 6 else 0  # 30 minutes break for >6 hours
        end_datetime = start_datetime + timedelta(hours=hours_worked + break_time)
        
        return end_datetime.strftime("%H:%M")
    
    def calculate_summary(self, time_records: List[Dict]) -> Dict[str, float]:
        """
        Calculate summary statistics from time records.
        
        Args:
            time_records: List of time record dictionaries
            
        Returns:
            Dictionary containing summary statistics
        """
        total_hours = sum(record['hours_worked'] for record in time_records)
        vacation_days = sum(1 for record in time_records if record['is_vacation'])
        sick_days = sum(1 for record in time_records if record['is_sick'])
        total_break_minutes = sum(record['break_minutes'] for record in time_records)
        
        return {
            'total_hours': total_hours,
            'vacation_days': vacation_days,
            'sick_days': sick_days,
            'total_break_minutes': total_break_minutes
        }
    
    def generate_latex_content(self, employee_id: int, year: int, month: int) -> str:
        """
        Generate the complete LaTeX content with data populated.
        
        Args:
            employee_id: Employee ID from the database
            year: Year for the report
            month: Month for the report (1-12)
            
        Returns:
            Complete LaTeX content as string
        """
        # Read the template
        with open(self.template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Get data
        company_info = self.get_company_info()
        employee_info = self.get_employee_info(employee_id)
        time_records = self.get_time_records(employee_id, year, month)
        summary = self.calculate_summary(time_records)
        
        month_name = calendar.month_name[month]
        report_period = f"{month_name} {year}"
        
        # Replace DATA0 - Company Information
        data0_replacement = f"""\\newcommand{{\\companyname}}{{{company_info['company_name']}}} % Company name
\\newcommand{{\\companystreet}}{{{company_info['company_street']}}} % Street address
\\newcommand{{\\companycity}}{{{company_info['company_city']}}} % City with ZIP
\\newcommand{{\\companyphone}}{{{company_info['company_phone']}}} % Phone number
\\newcommand{{\\companyemail}}{{{company_info['company_email']}}} % Email address
\\newcommand{{\\companylogo}}{{{company_info['company_logo']}}} % Path to logo file"""
        
        # Replace DATA1 - Employee Information
        data1_replacement = f"""\\newcommand{{\\employeename}}{{{employee_info['name']}}} % Employee name
\\newcommand{{\\employeenumber}}{{{employee_info['employee_number']}}} % Personnel number
\\newcommand{{\\reportperiod}}{{{report_period}}} % Reporting period"""
        
        # Replace DATA2 - Company Colors
        data2_replacement = f"""\\definecolor{{primary}}{{HTML}}{{{company_info['primary_color']}}}  % Company primary color
\\definecolor{{secondary}}{{HTML}}{{{company_info['secondary_color']}}} % Company secondary color
\\definecolor{{tertiary}}{{HTML}}{{{company_info['tertiary_color']}}} % Company tertiary color"""
        
        # Replace DATA3 - Time Records Table Rows
        data3_rows = []
        for record in time_records:
            vacation_text = "Yes" if record['is_vacation'] else "No"
            sick_text = "Yes" if record['is_sick'] else "No"
            
            row = f"    {record['date']} & {record['start_time']} & {record['end_time']} & {record['total_minutes']} & {record['break_minutes']} & {vacation_text} & {sick_text} \\\\"
            data3_rows.append(row)
        
        data3_replacement = "\n".join(data3_rows)
        
        # Replace DATA4 - Summary Row
        total_minutes = int(summary['total_hours'] * 60)
        data4_replacement = f"    \\multicolumn{{3}}{{|l|}}{{\\textbf{{Total}}}} & {total_minutes} & {summary['total_break_minutes']} & {summary['vacation_days']} days & {summary['sick_days']} days \\\\"
        
        # Replace DATA5 - Summary Statistics
        data5_replacement = f"""\\textbf{{Total Working Hours:}} & {summary['total_hours']:.2f} hours \\\\
    \\textbf{{Vacation Days Used:}} & {summary['vacation_days']} days \\\\
    \\textbf{{Sick Leave Taken:}} & {summary['sick_days']} days \\\\[0.5cm]"""
        
        # Perform replacements
        replacements = [
            (f"% ___DATA0___\n\\newcommand{{\\companyname}}{{My Company GmbH}} % Company name\n\\newcommand{{\\companystreet}}{{Businessstraße 123}} % Street address\n\\newcommand{{\\companycity}}{{10115 Berlin}} % City with ZIP\n\\newcommand{{\\companyphone}}{{+49-30-1234567}} % Phone number\n\\newcommand{{\\companyemail}}{{contact@mycompany.com}} % Email address\n\\newcommand{{\\companylogo}}{{company_logo.png}} % Path to logo file", f"% ___DATA0___\n{data0_replacement}"),
            (f"% ___DATA1___\n\\newcommand{{\\employeename}}{{Max Mustermann}} % Employee name\n\\newcommand{{\\employeenumber}}{{10042}} % Personnel number\n\\newcommand{{\\reportperiod}}{{February 2025}} % Reporting period", f"% ___DATA1___\n{data1_replacement}"),
            (f"% ___DATA2___\n\\definecolor{{primary}}{{HTML}}{{2B579A}}  % Company primary color\n\\definecolor{{secondary}}{{HTML}}{{00A4EF}} % Company secondary color\n\\definecolor{{tertiary}}{{HTML}}{{00A4EF}} % Company tertiary color", f"% ___DATA2___\n{data2_replacement}"),
            (f"    % ___DATA3___\n    01.01.2023 & 09:00 & 17:00 & 480 & 30 & No & No \\\\\n    02.01.2023 & 08:30 & 16:45 & 495 & 45 & No & No \\\\\n    03.01.2023 & - & - & 0 & 0 & Yes & No \\\\", f"    % ___DATA3___\n{data3_replacement}"),
            (f"    % ___DATA4___\n    \\multicolumn{{3}}{{|l|}}{{\\textbf{{Total}}}} & 975 & 75 & 0 days & 0 days \\\\", f"    % ___DATA4___\n{data4_replacement}"),
            (f"    % ___DATA5___\n    \\textbf{{Total Working Hours:}} & 16.25 hours \\\\\n    \\textbf{{Vacation Days Used:}} & 0 days \\\\\n    \\textbf{{Sick Leave Taken:}} & 0 days \\\\[0.5cm]", f"    % ___DATA5___\n    {data5_replacement}")
        ]
        
        result = template
        for old_text, new_text in replacements:
            result = result.replace(old_text, new_text)
        
        return result
    
    def save_report(self, employee_id: int, year: int, month: int, output_path: str) -> None:
        """
        Generate and save the LaTeX report to a file.
        
        Args:
            employee_id: Employee ID from the database
            year: Year for the report
            month: Month for the report (1-12)
            output_path: Path where the generated LaTeX file should be saved
        """
        latex_content = self.generate_latex_content(employee_id, year, month)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
    def compile_tex_to_pdf(self, tex_path: str, output_dir: str = None, delete_tex: bool = False, 
                          delete_aux_files: bool = True) -> str:
        """
        Compile a LaTeX file to PDF using pdflatex.
        
        Args:
            tex_path: Path to the .tex file
            output_dir: Directory where PDF should be saved (default: same as tex file)
            delete_tex: Whether to delete the .tex file after compilation
            delete_aux_files: Whether to delete auxiliary files (.aux, .log, etc.)
            
        Returns:
            Path to the generated PDF file
            
        Raises:
            FileNotFoundError: If LaTeX compiler is not found
            subprocess.CalledProcessError: If compilation fails
        """
        if not os.path.exists(tex_path):
            raise FileNotFoundError(f"LaTeX file not found: {tex_path}")
        
        # Determine output directory
        if output_dir is None:
            output_dir = os.path.dirname(tex_path)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Get file names
        tex_filename = os.path.basename(tex_path)
        tex_name_without_ext = os.path.splitext(tex_filename)[0]
        pdf_path = os.path.join(output_dir, f"{tex_name_without_ext}.pdf")
        
        try:
            # Check if pdflatex is available
            subprocess.run(['pdflatex', '--version'], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise FileNotFoundError(
                "pdflatex not found. Please install a LaTeX distribution "
                "(e.g., TeX Live, MiKTeX) to compile PDF reports."
            )
        
        # Create temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy tex file to temp directory
            temp_tex_path = os.path.join(temp_dir, tex_filename)
            shutil.copy2(tex_path, temp_tex_path)
            
            # Copy any additional files that might be needed (like logo)
            tex_dir = os.path.dirname(tex_path)
            for file in os.listdir(tex_dir):
                if file.endswith(('.png', '.jpg', '.jpeg', '.pdf', '.eps')):
                    src_file = os.path.join(tex_dir, file)
                    dst_file = os.path.join(temp_dir, file)
                    if os.path.isfile(src_file):
                        shutil.copy2(src_file, dst_file)
            
            try:
                # Run pdflatex twice to resolve references
                for run in range(2):
                    result = subprocess.run([
                        'pdflatex',
                        '-interaction=nonstopmode',
                        '-output-directory', temp_dir,
                        temp_tex_path
                    ], capture_output=True, text=True, cwd=temp_dir)
                    
                    if result.returncode != 0:
                        # Print error details
                        print(f"LaTeX compilation failed (run {run + 1}):")
                        print("STDOUT:", result.stdout)
                        print("STDERR:", result.stderr)
                        
                        # Try to find and print relevant error lines
                        if result.stdout:
                            lines = result.stdout.split('\n')
                            error_lines = [line for line in lines if 'Error' in line or '!' in line]
                            if error_lines:
                                print("Key errors:")
                                for line in error_lines[:5]:  # Show first 5 errors
                                    print(f"  {line}")
                        
                        raise subprocess.CalledProcessError(
                            result.returncode, 
                            result.args,
                            f"LaTeX compilation failed. Check the .tex file for syntax errors."
                        )
                
                # Copy the generated PDF to the output directory
                temp_pdf_path = os.path.join(temp_dir, f"{tex_name_without_ext}.pdf")
                if os.path.exists(temp_pdf_path):
                    shutil.copy2(temp_pdf_path, pdf_path)
                else:
                    raise FileNotFoundError("PDF was not generated despite successful compilation")
                
            except subprocess.CalledProcessError as e:
                raise subprocess.CalledProcessError(
                    e.returncode, e.cmd, 
                    f"Failed to compile {tex_path} to PDF. Error: {e}"
                )
        
        # Clean up files if requested
        if delete_aux_files:
            aux_extensions = ['.aux', '.log', '.out', '.toc', '.nav', '.snm', '.fls', '.fdb_latexmk']
            for ext in aux_extensions:
                aux_file = os.path.join(output_dir, f"{tex_name_without_ext}{ext}")
                if os.path.exists(aux_file):
                    try:
                        os.remove(aux_file)
                    except OSError:
                        pass  # Ignore errors when deleting auxiliary files
        
        if delete_tex:
            try:
                os.remove(tex_path)
                print(f"Deleted LaTeX file: {tex_path}")
            except OSError as e:
                print(f"Warning: Could not delete LaTeX file {tex_path}: {e}")
        
        print(f"PDF generated successfully: {pdf_path}")
        return pdf_path

    def generate_pdf_report(self, employee_id: int, year: int, month: int, output_path: str,
                           delete_tex: bool = True, delete_aux_files: bool = True) -> str:
        """
        Generate a complete PDF report directly from database data.
        
        Args:
            employee_id: Employee ID from the database
            year: Year for the report
            month: Month for the report (1-12)
            output_path: Path where the generated PDF should be saved (with .pdf extension)
            delete_tex: Whether to delete the intermediate .tex file
            delete_aux_files: Whether to delete auxiliary LaTeX files
            
        Returns:
            Path to the generated PDF file
        """
        # Ensure output path has .pdf extension
        if not output_path.endswith('.pdf'):
            output_path += '.pdf'
        
        # Create temporary .tex file
        output_dir = os.path.dirname(output_path) or '.'
        pdf_name = os.path.basename(output_path)
        tex_name = pdf_name.replace('.pdf', '.tex')
        temp_tex_path = os.path.join(output_dir, tex_name)
        
        try:
            # Generate LaTeX content and save to temporary file
            latex_content = self.generate_latex_content(employee_id, year, month)
            
            with open(temp_tex_path, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            # Compile to PDF
            pdf_path = self.compile_tex_to_pdf(
                tex_path=temp_tex_path,
                output_dir=output_dir,
                delete_tex=delete_tex,
                delete_aux_files=delete_aux_files
            )
            
            # Rename PDF to desired output path if different
            final_pdf_path = os.path.join(output_dir, pdf_name)
            if pdf_path != final_pdf_path:
                shutil.move(pdf_path, final_pdf_path)
                pdf_path = final_pdf_path
            
            return pdf_path
            
        except Exception as e:
            # Clean up temporary tex file if something went wrong
            if os.path.exists(temp_tex_path):
                try:
                    os.remove(temp_tex_path)
                except OSError:
                    pass
            raise e

# Example usage:
if __name__ == "__main__":
    # Initialize the ReportManager
    report_manager = ReportManager(
        db_path="/home/zarathustra/repos/ChronoStaff/data/employee_time.db",
        template_path="resources/templates/time_report_2.tex"
    )
    
    try:
        # Option 1: Generate LaTeX file only
        report_manager.save_report(
            employee_id=2,
            year=2025,
            month=5,
            output_path="generated_report.tex"
        )
        
        # Option 2: Generate PDF directly (deletes .tex file by default)
        pdf_path = report_manager.generate_pdf_report(
            employee_id=2,
            year=2025,
            month=1,
            output_path="may_2025_report.pdf",
            delete_tex=True,  # Delete .tex file after compilation
            delete_aux_files=True  # Delete auxiliary files (.aux, .log, etc.)
        )
        print(f"PDF report saved to: {pdf_path}")
        
        # Option 3: Compile existing .tex file to PDF
        # pdf_path = report_manager.compile_tex_to_pdf(
        #     tex_path="existing_report.tex",
        #     delete_tex=False,  # Keep the .tex file
        #     delete_aux_files=True
        # )
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure you have LaTeX installed (e.g., TeX Live or MiKTeX)")
    except Exception as e:
        print(f"Error generating report: {e}")