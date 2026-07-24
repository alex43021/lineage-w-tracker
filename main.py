import sys
import os
import logging
import ctypes
import warnings

# Suppress urllib3 version mismatch warnings
warnings.filterwarnings("ignore", category=UserWarning)

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

# Enable DPI awareness to make sure Win32 API returns actual physical pixel coordinates
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

def main():
    # Setup logging
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "app.log"), encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Lineage W Chat Capture & Boss Tracker...")

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Uncaught exception encountered:", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

    # Create PySide6 Application
    app = QApplication(sys.argv)
    
    # Instantiate Main UI
    window = MainWindow(settings_path="config/settings.json")
    window.show()
    
    # Run loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
