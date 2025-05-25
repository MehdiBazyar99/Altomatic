import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon # Make sure QIcon is imported
from pyqt_ui import MainWindow
import os # To construct path to icon

def main():
    app = QApplication(sys.argv)
    
    # Construct path to icon relative to the script's directory
    # Assuming main.py is in the root of the project and altomatic_icon.ico is also there.
    # If your structure is different, adjust this path.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_dir, "altomatic_icon.ico")

    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        print(f"Warning: Application icon not found at {icon_path}", file=sys.stderr)
        # You could fall back to a default system icon or no icon if preferred.

    # app.setOrganizationName("YourOrgName") # Optional
    app.setApplicationName("Altomatic")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
