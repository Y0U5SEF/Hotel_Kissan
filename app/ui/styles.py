"""
Stylesheet definitions for the application
"""

# Style constants
ROOT = {
    'ui-min-height': '25px',
    'padding': '5px 15px;',
    'input-padding': '2px 5px',
    'background': '#FFFFFF',
    'tab-height': '32px'
}

MAIN_STYLESHEET = f"""
/* Main Window */
QMainWindow {{
    background-color: #f5f6fa;
}}

/* Top Bar */
#topBar {{
    background-color: #1a73e8;
    border-bottom: 1px solid #e0e0e0;
}}

#hotelName {{
    color: white;
    font-size: 18px;
    font-weight: bold;
}}

#userName {{
    color: white;
    font-size: 14px;
    font-weight: 500;
}}

#logoutButton {{
    background-color: transparent;
    border: none;
    border-radius: 16px;
    padding: 6px;
}}

#logoutButton:hover {{
    background-color: rgba(255, 255, 255, 0.1);
}}

#logoutButton:pressed {{
    background-color: rgba(255, 255, 255, 0.2);
}}

/* Navigation Panel */
#navPanel {{
    background-color: #ffffff;
    border-right: 1px solid #e0e0e0;
    padding: 0;
    margin: 0;
}}

/* Button Base Styles */
QPushButton {{
    font-weight: bold;
    padding: 0px 15px;
    border-radius: 5px;
    min-height: {ROOT['ui-min-height']};
    font-size: 12pt;
}}

/* Table Action Buttons (Buttons inside table rows) */
QPushButton#tableActionButton {{
    padding: 2px 10px;
    font-size: 12pt;
    height: 30px;
    border-radius: 5px;
}}

QPushButton#tableActionButton[action="edit"] {{
    background-color: #007bff;
    color: white;
    border: none;
}}

QPushButton#tableActionButton[action="delete"] {{
    background-color: #dc3545;
    color: white;
    border: none;
}}

QPushButton#tableActionButton[action="view"] {{
    background-color: #1a73e8;
    color: white;
    border: none;
}}

QPushButton#tableActionButton[action="extra"] {{
    background-color: #28a745;
    color: white;
    border: none;
}}

QPushButton#tableActionButton[action="checkout"] {{
    background-color: #6f42c1;
    color: white;
    border: none;
}}

/* Primary Action Buttons (Blue) */
QPushButton#actionButton {{
    background-color: #1a73e8;
    color: white;
    border: none;
    min-height: {ROOT['ui-min-height']};
    padding: {ROOT['padding']};
}}

QPushButton#actionButton:hover {{
    background-color: #1557b0;
}}

QPushButton#actionButton:pressed {{
    background-color: #0d47a1;
}}

/* Navigation Buttons (Blue) */
QPushButton#navButton {{
    background-color: #1a73e8;
    color: white;
    border: none;
    text-align: center;
    min-height: {ROOT['ui-min-height']};
    padding: 8px 16px;
}}

QPushButton#navButton:hover {{
    background-color: #1557b0;
}}

QPushButton#navButton:checked {{
    background-color: #0d47a1;
}}

QPushButton#navButton:disabled {{
    background-color: #90caf9;
    color: #e3f2fd;
}}

/* Delete Buttons (Red) */
QPushButton#deleteButton {{
    background-color: #dc3545;
    color: white;
    border: none;
    min-height: {ROOT['ui-min-height']};
    padding: 8px 16px;
}}

QPushButton#deleteButton:hover {{
    background-color: #c82333;
}}

QPushButton#deleteButton:pressed {{
    background-color: #bd2130;
}}

/* Edit Buttons (Blue) */
QPushButton#editButton {{
    background-color: #007bff;
    color: white;
    border: none;
    min-height: {ROOT['ui-min-height']};
    padding: 8px 16px;
}}

QPushButton#editButton:hover {{
    background-color: #0056b3;
}}

QPushButton#editButton:pressed {{
    background-color: #004085;
}}

/* Login Button (Special) */
QPushButton#loginButton {{
    background-color: #1a73e8;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 12px 24px;
    min-height: 45px;
    font-size: 16px;
}}

QPushButton#loginButton:hover {{
    background-color: #1557b0;
}}

QPushButton#loginButton:pressed {{
    background-color: #0d47a1;
}}

/* Quick Action Buttons (Dashboard) */
QPushButton#quickActionButton {{
    background-color: white;
    color: #1a73e8;
    border: 1px solid #1a73e8;
    border-radius: 4px;
    min-height: {ROOT['ui-min-height']};
    padding: 8px 16px;
}}

QPushButton#quickActionButton:hover {{
    background-color: #e8f0fe;
}}

QPushButton#quickActionButton:pressed {{
    background-color: #d2e3fc;
}}

/* Input Fields */
QLineEdit {{
    padding: {ROOT['input-padding']};
    border: 2px solid #dcdde1;
    border-radius: 5px;
    background-color: {ROOT['background']};
    min-height: {ROOT['ui-min-height']};
}}

QLineEdit:focus {{
    border-color: #3498db;
}}

QLineEdit#readOnlyInput {{
    padding: {ROOT['padding']};
    border: 2px solid #dcdde1;
    border-radius: 5px;
    background-color: #f5f6fa;
    color: #2c3e50;
    min-height: {ROOT['ui-min-height']};
}}

QLineEdit#readOnlyInput:focus {{
    border-color: #3498db;
}}

/* QDateEdit */
QDateEdit {{
    padding: {ROOT['padding']};
    border: 2px solid #dcdde1;
    border-radius: 5px;
    background-color: {ROOT['background']};
    min-height: {ROOT['ui-min-height']};
}}

QDateEdit::down-arrow {{
    image: url(:/icons/dropdown.png);
    width: 12px;
    height: 12px;
    border: none;
}}

/* ComboBox Styles */
QComboBox {{
    padding: {ROOT['padding']};
    border: 2px solid #dcdde1;
    border-radius: 5px;
    background-color: {ROOT['background']};
    min-height: {ROOT['ui-min-height']};
}}

QComboBox:focus {{
    border-color: #3498db;
}}

QComboBox:hover {{
    border-color: #3498db;
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    image: url(:/icons/dropdown.png);
    width: 12px;
    height: 12px;
}}

QComboBox QAbstractItemView {{
    border: 2px solid #dcdde1;
    border-radius: 5px;
    background-color: white;
    selection-background-color: #e8f0fe;
    selection-color: #1a73e8;
    padding: 4px;
}}

QComboBox QAbstractItemView::item {{
    padding: 8px;
    min-height: {ROOT['ui-min-height']};
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: #f5f6fa;
}}

/* Table Styles */
QTableWidget {{
    background-color: #fff;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    gridline-color: #e0e0e0;
    selection-background-color: #e0e0e0;
    selection-color: #212529;
    font-size: 12pt;
    font-weight: bold;
}}

QTableWidget::item:selected {{
    background-color: transparent;
    border: 2px solid lightblue;
}}

QTableWidget QHeaderView::section {{
    background-color: #f5f6fa;
    font-size: 14px;
    font-weight: bold;
    padding: 14px 8px;
    border: none;
    border-bottom: 2px solid #e0e0e0;
}}

/* Progress Bar */
QProgressBar#paymentProgress {{
    border: 2px solid #dcdde1;
    border-radius: 5px;
    text-align: center;
    background-color: #f5f6fa;
}}

QProgressBar#paymentProgress::chunk {{
    background-color: #2ecc71;
    border-radius: 3px;
}}

/* Labels */
QLabel#pageTitle {{
    font-size: 24px;
    font-weight: bold;
    color: #2c3e50;
}}

QLabel#sectionTitle {{
    font-size: 18px;
    font-weight: bold;
    color: #1a73e8;
    margin-bottom: 10px;
}}

/* Progress Steps */
QLabel#stepNumber {{
    background-color: #bdc3c7;
    color: white;
    border-radius: 5px;
    padding: 8px;
    font-weight: bold;
    font-size: 14px;
    min-width: 30px;
    min-height: {ROOT['ui-min-height']};
    text-align: center;
}}

QLabel#stepNumber[active="true"] {{
    background-color: #1a73e8;
}}

QLabel#stepNumber[completed="true"] {{
    background-color: #2ecc71;
}}

QLabel#stepName {{
    color: #7f8c8d;
    font-size: 14px;
    margin-left: 8px;
}}

QLabel#stepName[active="true"] {{
    color: #1a73e8;
    font-weight: bold;
}}

QLabel#stepName[completed="true"] {{
    color: #2ecc71;
}}

QLabel#paymentStatus {{
    font-size: 16px;
    font-weight: bold;
    color: #2c3e50;
}}

/* Progress Line */
QFrame#progressLine {{
    background-color: #dcdde1;
    min-height: 2px;
    border-radius: 1px;
}}

QFrame#progressLine[active="true"] {{
    background-color: #1a73e8;
}}

QFrame#progressLine[completed="true"] {{
    background-color: #2ecc71;
}}

/* Calendar Widget */
QCalendarWidget QWidget#qt_calendar_navigationbar {{
    min-height: 50px;
}}

QCalendarWidget QToolButton {{
    font-size:12pt;
    font-weight:bold;
}}

/* Spin Box */
QSpinBox, QDoubleSpinBox {{
    padding: {ROOT['padding']};
    border: 2px solid #dcdde1;
    border-radius: 5px;
    background-color: white;
    height: 30px;
    min-height: {ROOT['ui-min-height']};
}}

QSpinBox::up-button, QDoubleSpinBox::up-button {{
    image: url(:/icons/up.png);
    height: 20px;
    width: 25px;
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    image: url(:/icons/down.png);
    height: 20px;
    width: 25px;
}}

/* Scroll Areas and Scrollbars */
QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    border: none;
    background-color: #f5f6fa;
    width: 10px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background-color: #dcdde1;
    border-radius: 5px;
    min-height: 20px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    border: none;
    background-color: #f5f6fa;
    height: 10px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background-color: #dcdde1;
    border-radius: 5px;
    min-width: 20px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Header View */
QHeaderView::section {{
    background-color: #f5f6fa;
    padding: 8px;
    border: none;
    border-right: 1px solid #dcdde1;
    border-bottom: 1px solid #dcdde1;
}}

QHeaderView::section:checked {{
    background-color: #e9ecef;
}}

/* Sidebar Navigation Buttons */
QPushButton#sidebarButton {{
    background-color: transparent;
    color: #495057;
    border: none;
    text-align: left;
    min-height: {ROOT['tab-height']};
    padding: 12px 16px;
}}

QPushButton#sidebarButton:hover {{
    background-color: #f8f9fa;
    color: #1a73e8;
}}

QPushButton#sidebarButton:checked {{
    background-color: #e8f0fe;
    color: #1a73e8;
    font-weight: bold;
}}

QPushButton#sidebarButton QIcon {{
    width: 24px;
    height: 24px;
}}

/* Tab Widget Styles */
QTabWidget::pane {{
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    background-color: white;
}}

QTabWidget::tab-bar {{
    alignment: left;
}}

QTabBar::tab {{
    background-color: #f5f6fa;
    color: #495057;
    border: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 24px;
    margin-right: 4px;
    font-size: 12pt;
    font-weight: bold;
    min-height: {ROOT['tab-height']};
}}

QTabBar::tab:selected {{
    background-color: #1a73e8;
    color: white;
    font-weight: bold;
}}

QTabBar::tab:hover:!selected {{
    background-color: #e8f0fe;
    color: #1a73e8;
}}

QTabBar::tab:disabled {{
    color: #adb5bd;
}}

QTabBar::close-button {{
    image: url(:/icons/close.png);
    subcontrol-position: right;
}}

QTabBar::close-button:hover {{
    background-color: #dc3545;
    border-radius: 2px;
}}

/* Dialog Buttons */
QDialogButtonBox QPushButton#dialogOkButton {{
    background-color: #27ae60;
    color: white;
    min-width: 80px;
    padding: 0px 15px;
    border-radius: 4px;
    font-weight: bold;
    border: none;
}}

QDialogButtonBox QPushButton#dialogCancelButton {{
    background-color: #e74c3c;
    color: white;
    min-width: 80px;
    padding: 0px 15px;
    border-radius: 4px;
    font-weight: bold;
    border: none;
}}

QDialogButtonBox QPushButton#dialogOkButton:hover,
QDialogButtonBox QPushButton#dialogCancelButton:hover {{
    opacity: 0.9;
}}

QDialogButtonBox QPushButton#dialogOkButton:pressed,
QDialogButtonBox QPushButton#dialogCancelButton:pressed {{
    opacity: 0.8;
}}

/* Uppercase Text */
QLineEdit#uppercase {{
    text-transform: uppercase;
}}
""" 