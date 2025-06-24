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
try:
    from ttkthemes import ThemedTk, ThemedStyle
    THEMES_AVAILABLE = True
    print("✅ ttkthemes loaded successfully")
except ImportError:
    print("❌ ttkthemes not found. Install with: pip install ttkthemes")
    THEMES_AVAILABLE = False
    ThemedTk = tk.Tk
    ThemedStyle = ttk.Style
from gui_management import *


root = tk.Tk()
app = EmployeeTimeApp(root)
root.mainloop()