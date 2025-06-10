import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import calendar
import subprocess
import os
import tempfile
import shutil
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class ReportManager:
    """
    Manages the generation of time reports from database data.
    Supports multiple templates and languages: English/German, Default/LaTeX B&W/LaTeX Color.
    """
    
    # Template constants
    TEMPLATE_DEFAULT = "default"
    TEMPLATE_LATEX_BW = "latex_bw"
    TEMPLATE_LATEX_COLOR = "latex_color"
    
    # Language constants
    LANG_ENGLISH = "en"
    LANG_GERMAN = "de"
        
    def __init__(self, db_path: str, templates_dir: str = None):
        """
        Initialize the ReportManager.
        
        Args:
            db_path: Path to the SQLite database file
            templates_dir: Directory containing LaTeX template files
        """
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.templates_dir = os.path.join(self.script_dir, "resources", "templates")
        self.db_path = db_path
        self.use_reportlab = REPORTLAB_AVAILABLE 

    def is_reportlab_available(self) -> bool:
        """Check if reportlab is available for PDF generation."""
        return REPORTLAB_AVAILABLE

    def get_report_settings(self) -> Dict[str, str]:
        """
        Get report template settings from the database.

        Returns:
            Dictionary containing report settings
        """
        with self.connect_db() as conn:
            cursor = conn.cursor()

            # Try to get from report_settings table first
            try:
                cursor.execute("SELECT lang, template, default_output_path FROM report_settings WHERE id = 1")
                row = cursor.fetchone()

                if row:
                    # Map database template values to our constants - FIXED MAPPING
                    db_template = row[1] or 'default'  # Default to 'default' if None
                    print(f"Database template value: '{db_template}'")  # Debug print

                    # CORRECTED mapping logic
                    if db_template == 'default':
                        template = self.TEMPLATE_DEFAULT
                    elif db_template == 'color':
                        template = self.TEMPLATE_LATEX_COLOR
                    elif db_template == 'black-white':
                        template = self.TEMPLATE_LATEX_BW
                    else:
                        # Fallback to default for unknown values
                        template = self.TEMPLATE_DEFAULT
                        print(f"Warning: Unknown template value '{db_template}', using default")

                    print(f"Mapped to template constant: '{template}'")  # Debug print

                    return {
                        'template': template,
                        'lang': row[0] or 'en',
                        'default_output_path': row[2] or './reports/',
                        'templates_dir': self.templates_dir
                    }
                else:
                    # Fallback to settings table for backward compatibility
                    cursor.execute("SELECT key, value FROM settings WHERE key LIKE 'report_%'")
                    settings = dict(cursor.fetchall())

                    # Check if we have a report_template setting
                    if 'report_template' in settings:
                        template = settings['report_template']
                    else:
                        # Default to reportlab template
                        template = self.TEMPLATE_DEFAULT

                    return {
                        'template': template,
                        'templates_dir': settings.get('report_templates_dir', self.templates_dir)
                    }

            except sqlite3.OperationalError:
                # Settings table might not exist or have the columns
                # Return default settings
                return {
                    'template': self.TEMPLATE_DEFAULT,
                    'templates_dir': self.templates_dir
                }

    def get_template_path(self, template_type: str, language: str = "en") -> str:
        """
        Get the file path for a specific template and language.
        
        Args:
            template_type: Type of template (default, latex_bw, latex_color)
            language: Language code ('en' or 'de')
            
        Returns:
            Path to the template file
            
        Raises:
            ValueError: If template type is not supported
        """
        if template_type == self.TEMPLATE_DEFAULT:
            return None  # Uses reportlab, no template file needed
        
        # Determine template filename based on type and language
        if template_type == self.TEMPLATE_LATEX_BW:
            if language == self.LANG_GERMAN:
                filename = "time_report_1_german.tex"
            else:
                filename = "time_report_1.tex"
        elif template_type == self.TEMPLATE_LATEX_COLOR:
            if language == self.LANG_GERMAN:
                filename = "time_report_2_german.tex"
            else:
                filename = "time_report_2.tex"
        else:
            raise ValueError(f"Unsupported template type: {template_type}")
        
        template_path = os.path.join(self.templates_dir, filename)
        
        # Fallback to English if German template doesn't exist
        if language == self.LANG_GERMAN and not os.path.exists(template_path):
            print(f"Warning: German template {filename} not found, falling back to English")
            if template_type == self.TEMPLATE_LATEX_BW:
                filename = "time_report_1.tex"
            elif template_type == self.TEMPLATE_LATEX_COLOR:
                filename = "time_report_2.tex"
            template_path = os.path.join(self.templates_dir, filename)
        
        return template_path

    def get_localized_strings(self, language: str = "en") -> Dict[str, str]:
        """
        Get localized strings for report generation.
        
        Args:
            language: Language code ('en' or 'de')
            
        Returns:
            Dictionary of localized strings
        """
        if language == self.LANG_GERMAN:
            return {
                'company_title': 'MONATLICHER ARBEITSZEITBERICHT',
                'company_info_title': 'Firmeninformationen',
                'employee_info_title': 'Mitarbeiterinformationen',
                'monthly_summary_title': 'Monatliche Zusammenfassung',
                'detailed_records_title': 'Detaillierte Zeiterfassung',
                'company_label': 'Firma:',
                'address_label': 'Adresse:',
                'phone_label': 'Telefon:',
                'email_label': 'Email:',
                'name_label': 'Name:',
                'employee_id_label': 'Mitarbeiter-ID:',
                'report_period_label': 'Berichtszeitraum:',
                'metric_label': 'Kennzahl',
                'value_label': 'Wert',
                'total_hours_label': 'Gesamtarbeitsstunden:',
                'vacation_days_label': 'Urlaubstage genommen:',
                'sick_days_label': 'Krankheitstage:',
                'break_time_label': 'Gesamte Pausenzeit:',
                'date_header': 'Datum',
                'start_header': 'Beginn',
                'end_header': 'Ende',
                'hours_header': 'Stunden',
                'break_header': 'Pause',
                'vacation_header': 'Urlaub',
                'sick_header': 'Krank',
                'yes': 'Ja',
                'no': 'Nein',
                'hours_unit': 'Stunden',
                'days_unit': 'Tage',
                'minutes_unit': 'Minuten',
                'day_singular': 'Tag',
                'days_plural': 'Tage',
                'generated_on': 'Erstellt am:',
                'confidential': 'Vertraulich - Nur für den internen Gebrauch',
                'no_records': 'Keine Zeiterfassung für diesen Zeitraum gefunden.'
            }
        else:  # English (default)
            return {
                'company_title': 'MONTHLY TIME REPORT',
                'company_info_title': 'Company Information',
                'employee_info_title': 'Employee Information',
                'monthly_summary_title': 'Monthly Summary',
                'detailed_records_title': 'Detailed Time Records',
                'company_label': 'Company:',
                'address_label': 'Address:',
                'phone_label': 'Phone:',
                'email_label': 'Email:',
                'name_label': 'Name:',
                'employee_id_label': 'Employee ID:',
                'report_period_label': 'Report Period:',
                'metric_label': 'Metric',
                'value_label': 'Value',
                'total_hours_label': 'Total Working Hours:',
                'vacation_days_label': 'Vacation Days Used:',
                'sick_days_label': 'Sick Leave Taken:',
                'break_time_label': 'Total Break Time:',
                'date_header': 'Date',
                'start_header': 'Start',
                'end_header': 'End',
                'hours_header': 'Hours',
                'break_header': 'Break',
                'vacation_header': 'Vacation',
                'sick_header': 'Sick',
                'yes': 'Yes',
                'no': 'No',
                'hours_unit': 'hours',
                'days_unit': 'days',
                'minutes_unit': 'minutes',
                'day_singular': 'day',
                'days_plural': 'days',
                'generated_on': 'Report generated on',
                'confidential': 'Confidential - For internal use only',
                'no_records': 'No time records found for this period.'
            }

    def get_localized_month_name(self, month: int, language: str = "en") -> str:
        """
        Get localized month name.
        
        Args:
            month: Month number (1-12)
            language: Language code ('en' or 'de')
            
        Returns:
            Localized month name
        """
        if language == self.LANG_GERMAN:
            german_months = [
                '', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
                'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'
            ]
            return german_months[month]
        else:
            return calendar.month_name[month]

    def generate_latex_content_localized(self, employee_id: int, year: int, month: int, 
                                       template_path: str, language: str = "en") -> str:
        """
        Generate the complete LaTeX content with data populated and localized text.
        
        Args:
            employee_id: Employee ID from the database
            year: Year for the report
            month: Month for the report (1-12)
            template_path: Path to the LaTeX template file
            language: Language code ('en' or 'de')
            
        Returns:
            Complete LaTeX content as string
        """
        # Read the template
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Get data
        company_info = self.get_company_info()
        employee_info = self.get_employee_info(employee_id)
        time_records = self.get_time_records(employee_id, year, month)
        summary = self.calculate_summary(time_records)
        strings = self.get_localized_strings(language)
        
        # Get localized month name
        month_name = self.get_localized_month_name(month, language)
        report_period = f"{month_name} {year}"
        
        # Replace DATA0 - Company Information (same as before)
        data0_replacement = f"""\\newcommand{{\\companyname}}{{{company_info['company_name']}}} % Company name
\\newcommand{{\\companystreet}}{{{company_info['company_street']}}} % Street address
\\newcommand{{\\companycity}}{{{company_info['company_city']}}} % City with ZIP
\\newcommand{{\\companyphone}}{{{company_info['company_phone']}}} % Phone number
\\newcommand{{\\companyemail}}{{{company_info['company_email']}}} % Email address
\\newcommand{{\\companylogo}}{{{company_info['company_logo']}}} % Path to logo file"""
        
        # Replace DATA1 - Employee Information (same as before)
        data1_replacement = f"""\\newcommand{{\\employeename}}{{{employee_info['name']}}} % Employee name
\\newcommand{{\\employeenumber}}{{{employee_info['employee_number']}}} % Personnel number
\\newcommand{{\\reportperiod}}{{{report_period}}} % Reporting period"""
        
        # Replace DATA2 - Company Colors (same as before)
        data2_replacement = f"""\\definecolor{{primary}}{{HTML}}{{{company_info['primary_color']}}}  % Company primary color
\\definecolor{{secondary}}{{HTML}}{{{company_info['secondary_color']}}} % Company secondary color
\\definecolor{{tertiary}}{{HTML}}{{{company_info['tertiary_color']}}} % Company tertiary color"""
        
        # Replace DATA3 - Time Records Table Rows (localized)
        data3_rows = []
        for record in time_records:
            vacation_text = strings['yes'] if record['is_vacation'] else strings['no']
            sick_text = strings['yes'] if record['is_sick'] else strings['no']
            
            row = f"    {record['date']} & {record['start_time']} & {record['end_time']} & {record['total_minutes']} & {record['break_minutes']} & {vacation_text} & {sick_text} \\\\"
            data3_rows.append(row)
        
        data3_replacement = "\n".join(data3_rows)
        
        # Replace DATA4 - Summary Row (localized)
        total_minutes = int(summary['total_hours'] * 60)
        
        # Localized day/days text
        vacation_count = summary['vacation_days']
        sick_count = summary['sick_days']
        
        if language == self.LANG_GERMAN:
            vacation_text = f"{vacation_count} {'Tag' if vacation_count == 1 else 'Tage'}"
            sick_text = f"{sick_count} {'Tag' if sick_count == 1 else 'Tage'}"
        else:
            vacation_text = f"{vacation_count} {'day' if vacation_count == 1 else 'days'}"
            sick_text = f"{sick_count} {'day' if sick_count == 1 else 'days'}"
            
        data4_replacement = f"    \\multicolumn{{3}}{{|l|}}{{\\textbf{{{'Gesamt' if language == 'de' else 'Total'}}}}} & {total_minutes} & {summary['total_break_minutes']} & {vacation_text} & {sick_text} \\\\"
        
        # Replace DATA5 - Summary Statistics (localized)
        if language == self.LANG_GERMAN:
            vacation_text_summary = f"{summary['vacation_days']} {'Tag' if summary['vacation_days'] == 1 else 'Tage'}"
            sick_text_summary = f"{summary['sick_days']} {'Tag' if summary['sick_days'] == 1 else 'Tage'}"
            
            data5_replacement = f"""\\textbf{{Gesamtarbeitsstunden:}} & {summary['total_hours']:.2f} Stunden \\\\
    \\textbf{{Genommene Urlaubstage:}} & {vacation_text_summary} \\\\
    \\textbf{{Krankenstandstage:}} & {sick_text_summary} \\\\[0.5cm]"""
        else:
            vacation_text_summary = f"{summary['vacation_days']} {'day' if summary['vacation_days'] == 1 else 'days'}"
            sick_text_summary = f"{summary['sick_days']} {'day' if summary['sick_days'] == 1 else 'days'}"
            
            data5_replacement = f"""\\textbf{{Total Working Hours:}} & {summary['total_hours']:.2f} hours \\\\
    \\textbf{{Vacation Days Used:}} & {vacation_text_summary} \\\\
    \\textbf{{Sick Leave Taken:}} & {sick_text_summary} \\\\[0.5cm]"""
        
        # Perform replacements using more precise matching
        result = template
        
        # Replace DATA0
        old_data0 = """% ___DATA0___
\\newcommand{\\companyname}{My Company GmbH} % Company name
\\newcommand{\\companystreet}{Businessstraße 123} % Street address
\\newcommand{\\companycity}{10115 Berlin} % City with ZIP
\\newcommand{\\companyphone}{+49-30-1234567} % Phone number
\\newcommand{\\companyemail}{contact@mycompany.com} % Email address
\\newcommand{\\companylogo}{company_logo.png} % Path to logo file"""
        
        # Try to find the German template version first
        if language == self.LANG_GERMAN:
            german_data0 = """% ___DATA0___
\\newcommand{\\companyname}{Meine Firma GmbH} % Company name
\\newcommand{\\companystreet}{Geschäftsstraße 123} % Street address
\\newcommand{\\companycity}{10115 Berlin} % City with ZIP
\\newcommand{\\companyphone}{+49-30-1234567} % Phone number
\\newcommand{\\companyemail}{contact@meinefirma.com} % Email address
\\newcommand{\\companylogo}{company_logo.png} % Path to logo file"""
            if german_data0 in result:
                result = result.replace(german_data0, f"% ___DATA0___\n{data0_replacement}")
            else:
                result = result.replace(old_data0, f"% ___DATA0___\n{data0_replacement}")
        else:
            result = result.replace(old_data0, f"% ___DATA0___\n{data0_replacement}")
        
        # Replace DATA1 - handle both English and German templates
        old_data1_en = """% ___DATA1___
\\newcommand{\\employeename}{Max Mustermann} % Employee name
\\newcommand{\\employeenumber}{10042} % Personnel number
\\newcommand{\\reportperiod}{February 2025} % Reporting period"""
        
        old_data1_de = """% ___DATA1___
\\newcommand{\\employeename}{Max Mustermann} % Employee name
\\newcommand{\\employeenumber}{10042} % Personnel number
\\newcommand{\\reportperiod}{Februar 2025} % Reporting period"""
        
        if old_data1_de in result:
            result = result.replace(old_data1_de, f"% ___DATA1___\n{data1_replacement}")
        else:
            result = result.replace(old_data1_en, f"% ___DATA1___\n{data1_replacement}")
        
        # Replace DATA2
        old_data2 = """% ___DATA2___
\\definecolor{primary}{HTML}{2B579A}  % Company primary color
\\definecolor{secondary}{HTML}{00A4EF} % Company secondary color
\\definecolor{tertiary}{HTML}{00A4EF} % Company tertiary color"""
        result = result.replace(old_data2, f"% ___DATA2___\n{data2_replacement}")
        
        # Replace DATA3 - handle different sample data in templates
        old_data3_patterns = [
            """    % ___DATA3___
    01.01.2023 & 09:00 & 17:00 & 480 & 30 & No & No \\\\
    02.01.2023 & 08:30 & 16:45 & 495 & 45 & No & No \\\\
    03.01.2023 & - & - & 0 & 0 & Yes & No \\\\""",
            """    % ___DATA3___
    01.01.2023 & 09:00 & 17:00 & 480 & 30 & Nein & Nein \\\\
    02.01.2023 & 08:30 & 16:45 & 495 & 45 & Nein & Nein \\\\
    03.01.2023 & - & - & 0 & 0 & Ja & Nein \\\\"""
        ]
        
        for pattern in old_data3_patterns:
            if pattern in result:
                result = result.replace(pattern, f"    % ___DATA3___\n{data3_replacement}")
                break
        
        # Replace DATA4 - handle different summary patterns
        old_data4_patterns = [
            """    % ___DATA4___
    \\multicolumn{3}{|l|}{\\textbf{Total}} & 975 & 75 & 1 day & 0 days \\\\""",
            """    % ___DATA4___
    \\multicolumn{3}{|l|}{\\textbf{Gesamt}} & 975 & 75 & 0 Tage & 0 Tage \\\\"""
        ]
        
        for pattern in old_data4_patterns:
            if pattern in result:
                result = result.replace(pattern, f"    % ___DATA4___\n{data4_replacement}")
                break
        
        # Replace DATA5 - handle both English and German patterns
        old_data5_patterns = [
            """    % ___DATA5___
    \\textbf{Total Working Hours:} & 16.25 hours \\\\
    \\textbf{Vacation Days Used:} & 1 day \\\\
    \\textbf{Sick Leave Taken:} & 0 days \\\\[0.5cm]""",
            """    % ___DATA5___
    \\textbf{Gesamtarbeitsstunden:} & 16,25 Stunden \\\\
    \\textbf{Genommene Urlaubstage:} & 0 Tage \\\\
    \\textbf{Krankenstandstage:} & 0 Tage \\\\[0.5cm]"""
        ]
        
        for pattern in old_data5_patterns:
            if pattern in result:
                result = result.replace(pattern, f"    % ___DATA5___\n    {data5_replacement}")
                break
        
        return result

    def generate_reportlab_pdf_localized(self, employee_id: int, year: int, month: int, 
                                       output_path: str, language: str = "en") -> str:
        """
        Generate PDF report using reportlab with localization support.
        
        Args:
            employee_id: Employee ID from the database
            year: Year for the report
            month: Month for the report (1-12)
            output_path: Path where the PDF should be saved
            language: Language code ('en' or 'de')
            
        Returns:
            Path to the generated PDF file
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab library not installed. Install with: pip install reportlab")
        
        try:
            # Get data for the report
            company_info = self.get_company_info()
            employee_info = self.get_employee_info(employee_id)
            time_records = self.get_time_records(employee_id, year, month)
            summary = self.calculate_summary(time_records)
            strings = self.get_localized_strings(language)
            
            # Get localized month name
            month_name = self.get_localized_month_name(month, language)
            
            # Ensure output path has .pdf extension
            if not output_path.endswith('.pdf'):
                output_path += '.pdf'
            
            # Create PDF document
            doc = SimpleDocTemplate(output_path, pagesize=A4,
                                  rightMargin=72, leftMargin=72,
                                  topMargin=72, bottomMargin=18)
            
            # Get styles
            styles = getSampleStyleSheet()
            story = []
            
            # Custom styles (same as before)
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#' + company_info.get('primary_color', '1E40AF')),
                spaceAfter=30,
                alignment=1,  # Center alignment
                fontName='Helvetica-Bold'
            )
            
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#' + company_info.get('secondary_color', '3B82F6')),
                spaceAfter=20,
                alignment=1,
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading3'],
                fontSize=12,
                textColor=colors.HexColor('#' + company_info.get('primary_color', '1E40AF')),
                spaceAfter=12,
                spaceBefore=20,
                fontName='Helvetica-Bold'
            )
            
            # Title section (localized)
            story.append(Paragraph(strings['company_title'], title_style))
            story.append(Paragraph(f"{month_name} {year}", subtitle_style))
            story.append(Spacer(1, 20))
            
            # Company Information (localized)
            story.append(Paragraph(strings['company_info_title'], heading_style))
            company_data = [
                [strings['company_label'], company_info.get('company_name', 'N/A')],
                [strings['address_label'], f"{company_info.get('company_street', 'N/A')}, {company_info.get('company_city', 'N/A')}"],
                [strings['phone_label'], company_info.get('company_phone', 'N/A')],
                [strings['email_label'], company_info.get('company_email', 'N/A')]
            ]
            
            company_table = Table(company_data, colWidths=[1.5*inch, 4*inch])
            company_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(company_table)
            story.append(Spacer(1, 20))
            
            # Employee Information (localized)
            story.append(Paragraph(strings['employee_info_title'], heading_style))
            emp_data = [
                [strings['name_label'], employee_info.get('name', 'N/A')],
                [strings['employee_id_label'], employee_info.get('employee_number', 'N/A')],
                [strings['report_period_label'], f"{month_name} {year}"]
            ]
            
            emp_table = Table(emp_data, colWidths=[1.5*inch, 4*inch])
            emp_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(emp_table)
            story.append(Spacer(1, 20))
            
            # Monthly Summary (localized)
            story.append(Paragraph(strings['monthly_summary_title'], heading_style))
            summary_data = [
                [strings['metric_label'], strings['value_label']],
                [strings['total_hours_label'], f"{summary.get('total_hours', 0):.2f} {strings['hours_unit']}"],
                [strings['vacation_days_label'], f"{summary.get('vacation_days', 0)} {strings['days_unit']}"],
                [strings['sick_days_label'], f"{summary.get('sick_days', 0)} {strings['days_unit']}"],
                [strings['break_time_label'], f"{summary.get('total_break_minutes', 0)} {strings['minutes_unit']}"]
            ]
            
            primary_color = '#' + company_info.get('primary_color', '1E40AF')
            summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(primary_color)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F0F8FF')),
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Detailed Time Records (localized)
            if time_records and len(time_records) > 0:
                story.append(Paragraph(strings['detailed_records_title'], heading_style))
                
                # Create table headers (localized)
                table_data = [[strings['date_header'], strings['start_header'], strings['end_header'], 
                             strings['hours_header'], strings['break_header'], 
                             strings['vacation_header'], strings['sick_header']]]
                
                # Add time records
                for record in time_records:
                    vacation = strings['yes'] if record.get('is_vacation', False) else strings['no']
                    sick = strings['yes'] if record.get('is_sick', False) else strings['no']
                    hours = f"{record.get('hours_worked', 0):.1f}h" if record.get('hours_worked', 0) > 0 else "-"
                    break_time = f"{record.get('break_minutes', 0)}min" if record.get('break_minutes', 0) > 0 else "-"
                    
                    # Format date to be more readable
                    date_str = record.get('date', '')
                    if date_str and len(date_str) > 8:  # Assuming format like "01.01.2023"
                        date_str = date_str[:5]  # Take just "01.01"
                    
                    table_data.append([
                        date_str,
                        record.get('start_time', '-'),
                        record.get('end_time', '-'),
                        hours,
                        break_time,
                        vacation,
                        sick
                    ])
                
                # Create table with appropriate column widths
                col_widths = [0.8*inch, 0.7*inch, 0.7*inch, 0.6*inch, 0.6*inch, 0.7*inch, 0.5*inch]
                records_table = Table(table_data, colWidths=col_widths)
                records_table.setStyle(TableStyle([
                    # Header row styling
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(primary_color)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    
                    # Data rows styling
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                    ('TOPPADDING', (0, 1), (-1, -1), 6),
                    
                    # Alternate row colors
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8F9FA'), colors.white]),
                ]))
                story.append(records_table)
            else:
                story.append(Paragraph(strings['no_records'], styles['Normal']))
            
            # Footer (localized)
            story.append(Spacer(1, 30))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=1
            )
            story.append(Paragraph(f"{strings['generated_on']} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
            story.append(Paragraph(strings['confidential'], footer_style))
            
            # Build PDF
            doc.build(story)
            print(f"Localized ReportLab PDF generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            raise Exception(f"Error generating localized PDF with reportlab: {str(e)}")


    def generate_pdf_report(self, employee_id: int, year: int, month: int, output_path: str,
                           delete_tex: bool = True, delete_aux_files: bool = True) -> str:
        """
        Generate a complete PDF report with language support from database settings.
        
        Args:
            employee_id: Employee ID from the database
            year: Year for the report  
            month: Month for the report (1-12)
            output_path: Path where the generated PDF should be saved (with .pdf extension)
            delete_tex: Whether to delete the intermediate .tex file (LaTeX only)
            delete_aux_files: Whether to delete auxiliary LaTeX files (LaTeX only)
            
        Returns:
            Path to the generated PDF file
        """
        # Get report settings from database (including language)
        settings = self.get_report_settings()
        template_type = settings['template']
        language = settings.get('lang', 'en')  # Get language from settings
        
        print(f"Generating report using template: {template_type}, language: {language}")
        
        # Generate report based on template type
        if template_type == self.TEMPLATE_DEFAULT:
            if not REPORTLAB_AVAILABLE:
                print("Warning: reportlab not available, falling back to LaTeX black/white template")
                return self._generate_latex_pdf(employee_id, year, month, output_path, 
                                               self.TEMPLATE_LATEX_BW, language, delete_tex, delete_aux_files)
            return self.generate_reportlab_pdf_localized(employee_id, year, month, output_path, language)
        
        elif template_type in [self.TEMPLATE_LATEX_BW, self.TEMPLATE_LATEX_COLOR]:
            return self._generate_latex_pdf(employee_id, year, month, output_path, 
                                          template_type, language, delete_tex, delete_aux_files)
        else:
            raise ValueError(f"Unsupported template type in database: {template_type}")

    def _generate_latex_pdf(self, employee_id: int, year: int, month: int, output_path: str,
                           template_type: str, language: str = "en", delete_tex: bool = True, delete_aux_files: bool = True) -> str:
        """
        Generate PDF using LaTeX template with language support.
        
        Args:
            employee_id: Employee ID from the database
            year: Year for the report
            month: Month for the report (1-12)
            output_path: Path where the PDF should be saved
            template_type: Type of LaTeX template to use
            language: Language code ('en' or 'de')
            delete_tex: Whether to delete the .tex file after compilation
            delete_aux_files: Whether to delete auxiliary files
            
        Returns:
            Path to the generated PDF file
        """
        # Get template path with language support
        template_path = self.get_template_path(template_type, language)
        if not template_path or not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        print(f"Using template: {template_path}")
        
        # Ensure output path has .pdf extension
        if not output_path.endswith('.pdf'):
            output_path += '.pdf'
        
        # Create temporary .tex file
        output_dir = os.path.dirname(output_path) or '.'
        pdf_name = os.path.basename(output_path)
        tex_name = pdf_name.replace('.pdf', '.tex')
        temp_tex_path = os.path.join(output_dir, tex_name)
        
        try:
            # Generate LaTeX content with localization
            latex_content = self.generate_latex_content_localized(employee_id, year, month, template_path, language)
            
            with open(temp_tex_path, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            print(f"Generated LaTeX file: {temp_tex_path}")
            
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

    def set_report_template(self, template_type: str) -> None:
        """
        Set the report template in the database settings.
        
        Args:
            template_type: Type of template (default, latex_bw, latex_color)
            
        Raises:
            ValueError: If template type is not supported
        """
        if template_type not in [self.TEMPLATE_DEFAULT, self.TEMPLATE_LATEX_BW, self.TEMPLATE_LATEX_COLOR]:
            raise ValueError(f"Unsupported template type: {template_type}")
        
        with self.connect_db() as conn:
            cursor = conn.cursor()
            
            # Map our template constants to database values
            db_template_value = 'color'  # default
            if template_type == self.TEMPLATE_LATEX_BW:
                db_template_value = 'black-white'
            elif template_type == self.TEMPLATE_LATEX_COLOR:
                db_template_value = 'color'
            elif template_type == self.TEMPLATE_DEFAULT:
                db_template_value = 'default'
            
            try:
                # Try to update report_settings table first
                cursor.execute('''
                    INSERT OR REPLACE INTO report_settings (id, template, updated_at) 
                    VALUES (1, ?, CURRENT_TIMESTAMP)
                ''', (db_template_value,))
                
                conn.commit()
                print(f"Report template set to: {template_type} (database value: {db_template_value})")
                
            except sqlite3.OperationalError:
                # Fallback to settings table for backward compatibility
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                ''')
                
                cursor.execute('''
                    INSERT OR REPLACE INTO settings (key, value) 
                    VALUES ('report_template', ?)
                ''', (template_type,))
                
                conn.commit()
                print(f"Report template set to: {template_type} (fallback to settings table)")

    def get_available_templates(self) -> List[Dict[str, str]]:
        """
        Get list of available report templates with language support.
        
        Returns:
            List of template dictionaries with id, name, description, and language support
        """
        templates = [
            {
                'id': self.TEMPLATE_DEFAULT,
                'name': 'Default (ReportLab)',
                'description': 'Modern PDF report using ReportLab library',
                'available': REPORTLAB_AVAILABLE,
                'languages': ['en', 'de']  # ReportLab supports both languages
            },
            {
                'id': self.TEMPLATE_LATEX_BW,
                'name': 'LaTeX Black & White',
                'description': 'Professional black and white report using LaTeX',
                'available': self._is_latex_available(),
                'languages': self._get_available_languages_for_template(self.TEMPLATE_LATEX_BW)
            },
            {
                'id': self.TEMPLATE_LATEX_COLOR,
                'name': 'LaTeX Color',
                'description': 'Colorful professional report using LaTeX',
                'available': self._is_latex_available(),
                'languages': self._get_available_languages_for_template(self.TEMPLATE_LATEX_COLOR)
            }
        ]
        return templates

    def _is_latex_available(self) -> bool:
        """Check if LaTeX is available for PDF generation."""
        try:
            subprocess.run(['pdflatex', '--version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def connect_db(self) -> sqlite3.Connection:
        """Create and return a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def get_available_employees(self) -> List[Dict[str, any]]:
        """
        Get list of all active employees for selection.
        
        Returns:
            List of employee dictionaries with id, name, and employee_id
        """
        with self.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, employee_id 
                FROM employees 
                WHERE active = 1 
                ORDER BY name
            """)
            
            employees = []
            for row in cursor.fetchall():
                employees.append({
                    'id': row['id'],
                    'name': row['name'],
                    'employee_id': row['employee_id']
                })
            return employees
    
    def get_available_months_for_employee(self, employee_id: int) -> List[Dict[str, any]]:
        """
        Get available months with data for a specific employee.
        
        Args:
            employee_id: Employee ID from the database
            
        Returns:
            List of dictionaries with year, month, month_name, and record_count
        """
        with self.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT 
                    strftime('%Y', date) as year,
                    strftime('%m', date) as month,
                    COUNT(*) as record_count
                FROM time_records 
                WHERE employee_id = ?
                GROUP BY strftime('%Y', date), strftime('%m', date)
                ORDER BY year DESC, month DESC
            """, (employee_id,))
            
            months = []
            for row in cursor.fetchall():
                year = int(row['year'])
                month = int(row['month'])
                month_name = calendar.month_name[month]
                
                months.append({
                    'year': year,
                    'month': month,
                    'month_name': month_name,
                    'display_name': f"{month_name} {year}",
                    'record_count': row['record_count']
                })
            return months
    
    def get_company_info(self) -> Dict[str, str]:
        """
        Retrieve company information from company_data table.
        
        Returns:
            Dictionary containing company information
        """
        with self.connect_db() as conn:
            cursor = conn.cursor()
            
            # Try to get from company_data table first
            cursor.execute("SELECT * FROM company_data LIMIT 1")
            company_row = cursor.fetchone()
            
            if company_row:
                # Convert company_data to expected format
                company_info = {
                    'company_name': company_row['companyname'],
                    'company_street': company_row['companystreet'] or 'Businessstraße 123',
                    'company_city': company_row['companycity'] or '10115 Berlin', 
                    'company_phone': company_row['companyphone'] or '+49-30-1234567',
                    'company_email': company_row['companyemail'] or 'contact@mycompany.com',
                    'company_logo': 'company_logo.png',  # Default logo
                    'primary_color': (company_row['company_color_1'] or '#2B579A').replace('#', ''),
                    'secondary_color': (company_row['company_color_2'] or '#00A4EF').replace('#', ''),
                    'tertiary_color': (company_row['company_color_3'] or '#00A4EF').replace('#', '')
                }
            else:
                # Fallback to settings table
                cursor.execute("SELECT key, value FROM settings")
                settings = dict(cursor.fetchall())
                
                company_info = {
                    'company_name': settings.get('company_name', 'My Company GmbH'),
                    'company_street': settings.get('company_street', 'Businessstraße 123'),
                    'company_city': settings.get('company_city', '10115 Berlin'),
                    'company_phone': settings.get('company_phone', '+49-30-1234567'),
                    'company_email': settings.get('company_email', 'contact@mycompany.com'),
                    'company_logo': settings.get('company_logo', 'company_logo.png'),
                    'primary_color': settings.get('primary_color', '2B579A'),
                    'secondary_color': settings.get('secondary_color', '00A4EF'),
                    'tertiary_color': settings.get('tertiary_color', '00A4EF')
                }
                
            return company_info
    
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
        Works with the updated schema that has multiple start/end time pairs.
        Now properly handles multi-period days by showing overall timespan and correct breaks.

        Args:
            employee_id: Employee ID from the database
            year: Year for the report
            month: Month for the report (1-12)

        Returns:
            List of time record dictionaries
        """
        print(f"DEBUG: Getting time records for employee {employee_id}, {year}-{month:02d}")

        with self.connect_db() as conn:
            cursor = conn.cursor()

            # Get all days in the month
            days_in_month = calendar.monthrange(year, month)[1]
            start_date = f"{year}-{month:02d}-01"
            end_date = f"{year}-{month:02d}-{days_in_month:02d}"

            cursor.execute("""
                SELECT date, start_time_1, end_time_1, start_time_2, end_time_2, 
                       start_time_3, end_time_3, hours_worked, overtime_hours, 
                       record_type, notes, total_break_time, total_time_present
                FROM time_records 
                WHERE employee_id = ? 
                AND date BETWEEN ? AND ?
                ORDER BY date
            """, (employee_id, start_date, end_date))

            records = cursor.fetchall()
            print(f"DEBUG: Found {len(records)} records in database")

            # Convert to list of dictionaries and fill missing dates
            time_data = []
            record_dict = {record['date']: record for record in records}

            for day in range(1, days_in_month + 1):
                date_str = f"{year}-{month:02d}-{day:02d}"
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                weekday = date_obj.weekday()  # 0=Monday, 6=Sunday

                if date_str in record_dict:
                    record = record_dict[date_str]
                    print(f"DEBUG: Processing record for {date_str}")

                    # Handle different record types
                    record_type = record['record_type'] if 'record_type' in record.keys() else 'work'
                    if record_type == 'vacation':
                        time_data.append({
                            'date': date_obj.strftime("%d.%m.%Y"),
                            'start_time': '-',
                            'end_time': '-',
                            'total_minutes': 0,
                            'break_minutes': 0,
                            'is_vacation': True,
                            'is_sick': False,
                            'hours_worked': 0
                        })
                    elif record['record_type'] == 'sick':
                        time_data.append({
                            'date': date_obj.strftime("%d.%m.%Y"),
                            'start_time': '-',
                            'end_time': '-',
                            'total_minutes': 0,
                            'break_minutes': 0,
                            'is_vacation': False,
                            'is_sick': True,
                            'hours_worked': 0
                        })
                    elif record['record_type'] == 'holiday':
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
                    else:
                        # Regular work day - handle multi-period correctly
                        hours_worked = record['hours_worked'] if record['hours_worked'] else 0

                        if hours_worked > 0:
                            # Use the new multi-period calculation method
                            start_time, end_time, break_minutes = self._calculate_multi_period_times(record)
                        else:
                            start_time, end_time, break_minutes = '-', '-', 0

                        time_data.append({
                            'date': date_obj.strftime("%d.%m.%Y"),
                            'start_time': start_time,
                            'end_time': end_time,
                            'total_minutes': int(hours_worked * 60),
                            'break_minutes': break_minutes,
                            'is_vacation': False,
                            'is_sick': False,
                            'hours_worked': hours_worked
                        })
                else:
                    # No record for this date
                    if weekday < 5:  # Monday to Friday - show as potential work day
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
                    # Skip weekends (don't add to table)

            print(f"DEBUG: Returning {len(time_data)} time records for report")
            return time_data

    def _format_time(self, time_str: str) -> str:
        """
        Format time string to HH:MM format.
        
        Args:
            time_str: Time string in various formats
            
        Returns:
            Time string in HH:MM format
        """
        if not time_str or time_str == '-':
            return '-'
        
        try:
            # Handle different time formats
            if ':' in time_str:
                parts = time_str.split(':')
                hour = int(parts[0])
                minute = int(parts[1])
                return f"{hour:02d}:{minute:02d}"
            else:
                return time_str
        except (ValueError, IndexError):
            return '-'
    
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
            
        try:
            start_hour, start_minute = map(int, start_time.split(':'))
            start_datetime = datetime(2000, 1, 1, start_hour, start_minute)
            
            # Add worked hours plus break time
            break_time = 0.5 if hours_worked > 6 else 0  # 30 minutes break for >6 hours
            end_datetime = start_datetime + timedelta(hours=hours_worked + break_time)
            
            return end_datetime.strftime("%H:%M")
        except (ValueError, TypeError):
            return '-'
    
    def calculate_summary(self, time_records: List[Dict]) -> Dict[str, float]:
        """
        Calculate summary statistics from time records.

        Args:
            time_records: List of time record dictionaries

        Returns:
            Dictionary containing summary statistics
        """
        print("DEBUG: Calculating summary statistics")

        total_hours = sum(record['hours_worked'] for record in time_records)
        vacation_days = sum(1 for record in time_records if record['is_vacation'])
        sick_days = sum(1 for record in time_records if record['is_sick'])
        total_break_minutes = sum(record['break_minutes'] for record in time_records)

        print(f"DEBUG: Summary - Total hours: {total_hours:.2f}")
        print(f"DEBUG: Summary - Vacation days: {vacation_days}")
        print(f"DEBUG: Summary - Sick days: {sick_days}")
        print(f"DEBUG: Summary - Total break minutes: {total_break_minutes}")

        return {
            'total_hours': total_hours,
            'vacation_days': vacation_days,
            'sick_days': sick_days,
            'total_break_minutes': total_break_minutes
        }


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
            if tex_dir:  # Only if tex_dir is not empty
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

    def get_available_pdf_methods(self) -> Dict[str, bool]:
        """
        Check which PDF generation methods are available.
        
        Returns:
            Dictionary with method names and availability status
        """
        methods = {
            'reportlab': REPORTLAB_AVAILABLE,
            'latex': self._is_latex_available()
        }
        return methods

    def _get_available_languages_for_template(self, template_type: str) -> List[str]:
        """
        Check which languages are available for a specific template.
        
        Args:
            template_type: Template type to check
            
        Returns:
            List of available language codes
        """
        available_languages = []
        
        for lang in [self.LANG_ENGLISH, self.LANG_GERMAN]:
            template_path = self.get_template_path(template_type, lang)
            if template_path and os.path.exists(template_path):
                available_languages.append(lang)
        
        return available_languages

    def _calculate_multi_period_times(self, record) -> Tuple[str, str, int]:
        """
        Calculate overall start time, end time, and break minutes for multi-period records.

        Args:
            record: Database record with multiple time periods

        Returns:
            Tuple of (start_time, end_time, break_minutes)
        """
        # Convert sqlite3.Row to dict if needed
        if hasattr(record, 'keys'):
            record_dict = {key: record[key] for key in record.keys()}
        else:
            record_dict = record

        print(f"DEBUG: Calculating multi-period times for date {record_dict.get('date', 'unknown')}")

        # Collect all valid time periods
        periods = []
        for i in range(1, 4):  # Check periods 1, 2, 3
            start_col = f'start_time_{i}'
            end_col = f'end_time_{i}'
            start_time = record_dict.get(start_col)
            end_time = record_dict.get(end_col)

            if start_time and end_time and start_time != '-' and end_time != '-':
                periods.append((start_time, end_time))
                print(f"DEBUG: Found period {i}: {start_time} - {end_time}")

        if not periods:
            print("DEBUG: No valid periods found")
            return '-', '-', 0

        # Sort periods by start time to handle them in chronological order
        periods.sort(key=lambda x: self._time_to_minutes(x[0]))
        print(f"DEBUG: Sorted periods: {periods}")

        # Overall start is the earliest start time
        overall_start = periods[0][0]
        # Overall end is the latest end time
        overall_end = periods[-1][1]

        print(f"DEBUG: Overall timespan: {overall_start} - {overall_end}")

        # Calculate total working minutes from the database field
        hours_worked = record_dict.get('hours_worked', 0) or 0
        total_work_minutes = int(hours_worked * 60)
        print(f"DEBUG: Total work hours from DB: {hours_worked:.2f} ({total_work_minutes} minutes)")

        # Calculate total span in minutes
        total_span_minutes = self._time_to_minutes(overall_end) - self._time_to_minutes(overall_start)
        print(f"DEBUG: Total time span: {total_span_minutes} minutes")

        # Calculate break time as the difference between span and work time
        calculated_break_minutes = total_span_minutes - total_work_minutes

        # Get actual break time from database
        actual_break_hours = record_dict.get('total_break_time', 0) or 0
        actual_break_minutes = int(actual_break_hours * 60)
        print(f"DEBUG: Actual break time from DB: {actual_break_hours:.2f} hours ({actual_break_minutes} minutes)")
        print(f"DEBUG: Calculated break time: {calculated_break_minutes} minutes")

        # Use the larger of calculated break time or legal minimum
        legal_minimum_break = self._get_legal_minimum_break(hours_worked)
        print(f"DEBUG: Legal minimum break: {legal_minimum_break} minutes")

        # Use actual break time if available, otherwise use calculated or legal minimum
        if actual_break_minutes > 0:
            final_break_minutes = actual_break_minutes
            print(f"DEBUG: Using actual break time: {final_break_minutes} minutes")
        else:
            final_break_minutes = max(calculated_break_minutes, legal_minimum_break)
            print(f"DEBUG: Using calculated/legal minimum break: {final_break_minutes} minutes")

        return overall_start, overall_end, final_break_minutes    
        
    def _time_to_minutes(self, time_str: str) -> int:
        """
        Convert time string to minutes since midnight.

        Args:
            time_str: Time in HH:MM format

        Returns:
            Minutes since midnight
        """
        if not time_str or time_str == '-':
            return 0

        try:
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return hours * 60 + minutes
        except (ValueError, IndexError):
            print(f"DEBUG: Error parsing time '{time_str}', returning 0")
            return 0

    def _get_legal_minimum_break(self, hours_worked: float) -> int:
        """
        Get legal minimum break time based on hours worked (German labor law).
        
        Args:
            hours_worked: Number of hours worked
            
        Returns:
            Minimum break time in minutes
        """
        if hours_worked > 9:
            return 45  # 45 minutes for >9 hours
        elif hours_worked > 6:
            return 30  # 30 minutes for 6-9 hours
        else:
            return 0   # No mandatory break for ≤6 hours
