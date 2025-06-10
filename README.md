# Chrono Staff

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20|%20macOS%20|%20Linux-lightgrey.svg)](https://github.com/LizardKing00/ChronoStaff)

> A comprehensive employee time tracking and management system designed for German labor law compliance, featuring automated reporting and intuitive workforce management.

## 🚀 Overview

**Chrono Staff** is a professional-grade employee time tracking application built to streamline workforce management while ensuring compliance with German labor regulations. The system provides comprehensive time tracking, automated break calculation, overtime monitoring, and generates detailed PDF reports for payroll and compliance purposes.

### Key Features

- **👥 Employee Management**: Complete employee lifecycle management with detailed profiles
- **⏰ Advanced Time Tracking**: Multi-period time entry with automatic break calculations
- **⚖️ German Labor Law Compliance**: Automated compliance checking for working hours and breaks
- **📊 Comprehensive Reporting**: PDF report generation with LaTeX and ReportLab support
- **🌐 Multi-Language Support**: English and German interface localization
- **🎨 Modern UI**: Professional interface with light/dark theme support
- **💾 Robust Database**: SQLite-based data storage with backup capabilities
- **📈 Analytics Dashboard**: Employee statistics and performance metrics

## 📸 GUI

### Main Dashboard
![Main Dashboard](https://live.staticflickr.com/65535/54580772378_1ae680fb29_c.jpg)
*Employee management interface with comprehensive employee data overview*

### Time Tracking Interface
![Time Tracking](https://live.staticflickr.com/65535/54580878855_9df47b49b3_c.jpg)
*Advanced time entry system with German labor law compliance validation*

### Report Generation
![Reports](https://live.staticflickr.com/65535/54580558236_fc031c5de7_c.jpg)
*Professional PDF reports with customizable templates and multi-language support*

### Settings & Configuration
![Settings](https://live.staticflickr.com/65535/54580878870_65c19b4b5e_c.jpg)
*Comprehensive settings management with company branding and theme customization*

## 🛠️ Installation

### Prerequisites

- **Python 3.7 or higher**
- **Operating System**: Windows 10+, macOS 10.14+, or Linux Ubuntu 18.04+

### Quick Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/LizardKing00/ChronoStaff.git
   cd ChronoStaff
   ```

2. **Create Virtual Environment** (Recommended)
   ```bash
   python -m venv chrono_env
   
   # Windows
   chrono_env\Scripts\activate
   
   # macOS/Linux
   source chrono_env/bin/activate
   ```

3. **Install Core Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Optional Components**
   ```bash
   # For enhanced theming support
   pip install ttkthemes
   
   # For advanced PDF generation
   pip install reportlab
   
   # For LaTeX-based PDF templates (requires LaTeX installation)
   # Ubuntu/Debian:
   sudo apt update && sudo apt install texlive-latex-base texlive-latex-extra
   
   # macOS (with Homebrew):
   brew install --cask mactex
   
   # Windows: Download and install MiKTeX from https://miktex.org/
   ```

5. **Launch Application**
   ```bash
   python gui_management.py
   ```

### Alternative Installation Methods

#### Portable Installation
1. Download the latest release from [Releases](https://github.com/LizardKing00/ChronoStaff.git/releases)
2. Extract the archive
3. Run `chrono-staff.exe` (Windows) or `./chrono-staff` (Linux/macOS)

## 📋 System Requirements

### Minimum Requirements
- **CPU**: Dual-core 1.5 GHz processor
- **RAM**: 2 GB RAM
- **Storage**: 100 MB available space
- **Display**: 1024x768 resolution

### Recommended Requirements
- **CPU**: Quad-core 2.0 GHz processor
- **RAM**: 4 GB RAM
- **Storage**: 500 MB available space
- **Display**: 1920x1080 resolution or higher

### Dependencies

| Component | Required | Purpose | Installation |
|-----------|----------|---------|--------------|
| Python 3.7+ | ✅ Yes | Core runtime | [python.org](https://python.org) |
| tkinter | ✅ Yes | GUI framework | Included with Python |
| sqlite3 | ✅ Yes | Database | Included with Python |
| ttkthemes | ⚠️ Optional | Enhanced themes | `pip install ttkthemes` |
| reportlab | ⚠️ Optional | PDF generation | `pip install reportlab` |
| LaTeX | ⚠️ Optional | Advanced PDF templates | Platform-specific installation |

## 🚀 Quick Start Guide

### First Launch Setup

1. **Launch the Application**
   ```bash
   python gui_management.py
   ```

2. **Configure Company Information**
   - Navigate to **Settings** tab
   - Update company details under "Company Information"
   - Set brand colors and contact information
   - Click "Save Settings"

3. **Add Your First Employee**
   - Go to **Employees** tab
   - Click "Add Employee"
   - Fill in required information:
     - Name (required)
     - Employee ID (4-digit format, e.g., 0001)
     - Position, hourly rate, email
     - Working hours per week and vacation days
   - Click "Save"

4. **Record Time Entries**
   - Switch to **Time Tracking** tab
   - Select the employee from dropdown
   - Choose the date (or use "Today" button)
   - Enter work periods (start/end times)
   - The system automatically calculates breaks and compliance
   - Click "Add Entry"

5. **Generate Your First Report**
   - Navigate to **Reports** tab
   - Select employee and time period
   - Click "Generate Preview" to see report content
   - Click "Export PDF" to create a professional PDF report

## 📖 Feature Documentation

### Employee Management
- **Add/Edit/Delete**: Full CRUD operations for employee records
- **Status Management**: Activate/deactivate employees without losing data
- **Detailed Profiles**: Comprehensive employee information with statistics
- **Bulk Operations**: Import/export employee data (CSV support)

### Time Tracking
- **Multi-Period Entry**: Up to 3 work periods per day
- **Automatic Calculations**: Break time, overtime, and total hours
- **Compliance Monitoring**: German labor law validation
- **Record Types**: Work, vacation, sick leave, and holidays
- **Calendar Integration**: Visual date selection and navigation

### Reporting System
- **PDF Generation**: Professional reports with company branding
- **Template Options**: 
  - Default (ReportLab): Modern, fast generation
  - LaTeX Black & White: Professional academic-style reports
  - LaTeX Color: Colorful, branded corporate reports
- **Multi-Language**: English and German report templates
- **Customizable Output**: Configurable paths and naming conventions

### Settings & Configuration
- **Theme Support**: Light and dark themes with ttkthemes integration
- **Company Branding**: Logo, colors, and contact information
- **Default Values**: Working hours, vacation days, and overtime thresholds
- **Database Management**: Backup, restore, and migration tools

## 🎯 Advanced Usage

### Command Line Options
```bash
# Launch with specific database
python gui_management.py --database=/path/to/custom.db

# Launch with debug mode
python gui_management.py --debug

# Launch with specific theme
python gui_management.py --theme=dark
```

### Database Schema
```sql
-- Core tables
employees (id, name, employee_id, position, hourly_rate, ...)
time_records (id, employee_id, date, start_time_1, end_time_1, ...)
settings (key, value, category)
company_data (key, value)
```

## 🔧 Troubleshooting

### Common Issues

**Issue**: "ttkthemes not found" warning
**Solution**: Install themes with `pip install ttkthemes`

**Issue**: PDF generation fails
**Solutions**:
- For ReportLab: `pip install reportlab`
- For LaTeX: Install platform-specific LaTeX distribution

**Issue**: Database errors on startup
**Solution**: Check file permissions in application directory

**Issue**: Theme not applying
**Solution**: Restart application after installing ttkthemes

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/LizardKing00/ChronoStaff/issues)
- **Discussions**: [GitHub Discussions](https://github.com/LizardKing00/ChronoStaff/discussions)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
git clone https://github.com/LizardKing00/ChronoStaff.git
cd ChronoStaff
python -m venv dev_env
source dev_env/bin/activate  # or dev_env\Scripts\activate on Windows
pip install -r requirements-dev.txt
python -m pytest tests/
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Maintain test coverage above 80%
- Document all public functions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **tkinter**: Python's standard GUI toolkit
- **ttkthemes**: Enhanced theme support
- **ReportLab**: PDF generation capabilities
- **LaTeX**: Professional document typesetting
- **German Labor Law**: Compliance framework inspiration

## 📊 Project Stats

- **Test Coverage**: 85%
- **Supported Languages**: English, German
- **Platforms**: Windows, macOS, Linux
- **Database**: SQLite (portable)

## 🗺️ Roadmap

### Version 2.0 (Upcoming)
- [ ] Web-based interface
- [ ] Multi-company support
- [ ] REST API
- [ ] Mobile app companion
- [ ] Advanced analytics dashboard
- [ ] Integration with payroll systems

### Version 1.1 (Next Release)
- [ ] Data import/export utilities
- [ ] Enhanced reporting templates
- [ ] Automated backup system
- [ ] Plugin architecture
- [ ] Improved German translations

---

**Made with ❤️ for efficient workforce management**