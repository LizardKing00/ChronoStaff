# Chrono Staff – Employee Time Tracking System

**Chrono Staff** is a feature-rich, cross-platform desktop application developed in Python using Tkinter, designed for efficient employee time tracking and reporting. It provides a robust and intuitive graphical interface for managing employees, tracking work hours, and generating detailed reports.

---

## 🧩 Features Overview

🎥 GUI Demonstration
<table> <tr> <td><strong>🏢 Employee Management</strong></td> <td><strong>📅 Time Tracking</strong></td> </tr> <tr> <td><img src="resources/demo_employees.gif" alt="Employee Management GIF" width="400"/></td> <td><img src="resources/demo_tracking.gif" alt="Time Tracking GIF" width="400"/></td> </tr> <tr> <td><strong>📊 Reports Generation</strong></td> <td><strong>⚙️ Settings Configuration</strong></td> </tr> <tr> <td><img src="resources/demo_reports.gif" alt="Reports Tab GIF" width="400"/></td> <td><img src="resources/demo_settings.gif" alt="Settings GIF" width="400"/></td> </tr> </table>

### 🔧 Employee Management

* **Employee CRUD Interface**: Add, edit, deactivate/reactivate, and permanently delete employees.
* **Customizable Data**: Track position, hourly rate, work hours per week, vacation/sick days, and contact info.
* **Status Filters**: Toggle between active and inactive employees.
* **Details View**: View comprehensive employee details including statistics, remaining vacation/sick days, and current status.

### ⏱️ Time Tracking

* **Calendar-based Input**: Select dates via spinboxes or a calendar popup.
* **Track Time by Type**: Categorize hours as *work*, *vacation*, *sick*, or *holiday*.
* **Notes Support**: Add context-rich notes to any time entry.
* **Real-Time Summary**: Monthly overview of worked hours, overtime, and leave statistics.
* **Duplicate Detection**: Detect and consolidate duplicate entries per day intelligently.

### 📈 Reports & Analytics

* **Multi-format Reporting**: Generate reports for monthly, yearly, or custom periods.
* **Multi-language Support**: Generate reports in English or German.
* **LaTeX Export Templates**: Select from two customizable LaTeX templates: *color* or *black & white*.
* **Real-time Output Display**: View generated report content within the GUI before export.

### 📤 Data Export

* **Batch Export to JSON**: Export individual or multiple employees' data, with optional inclusion of inactive entries and time records.
* **Preview Before Export**: Validate the data before finalizing export to ensure accuracy.

### ⚙️ Settings & Customization

* **Company Branding**: Configure company name, address, contact info, and brand colors.
* **App Defaults**: Set standard hours/day, vacation and sick days, and overtime thresholds.
* **Template Config**: Choose default language, template style, and output directory for PDF reports.
* **Settings Persistence**: Save, load, and reset settings for consistency across sessions.

### 📂 Modular Architecture

* Decoupled components include:

  * `calendar_popup` for date selection
  * `database_management` for data access and manipulation
  * `date_management` for date handling logic

---

## 🗣️ Language & Templates

* Report language: `English (en)` or `German (de)`
* Template options:

  * `Color` (styled)
  * `Black & White` (minimal)

Templates are intended to be fully customizable by modifying the underlying LaTeX files @ `./resources/templates`

---

## 🖥️ User Interface

* Built using **Tkinter** for maximum cross-platform compatibility.
* Organized with tabbed layout:

  * **Employees**
  * **Time Tracking**
  * **Reports**
  * **Data Export**
  * **Settings**
  * **Employee Details**

Each section is independently scrollable and supports real-time updates.

---

## 📌 Use Case Scenarios

Ideal for small to mid-sized teams or HR departments looking for a lightweight, local solution for time tracking and payroll preparation. Great for freelancers and contractors who wish to generate accurate timesheets for monthly billing.


