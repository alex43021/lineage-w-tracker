import sys
import os
import traceback

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def test_start():
    app = QApplication(sys.argv)
    
    try:
        print("Instantiating MainWindow...")
        window = MainWindow()
        
        # Set a dummy valid HWND so IsWindow check passes (we can use the desktop window handle!)
        import win32gui
        desktop_hwnd = win32gui.GetDesktopWindow()
        window.settings["hwnd"] = desktop_hwnd
        print(f"Set dummy hwnd: {desktop_hwnd}")
        
        print("Calling start_monitoring()...")
        window.start_monitoring()
        print("start_monitoring() executed successfully!")
        
        # Clean up worker
        if window.worker:
            window.worker.stop()
            
    except Exception as e:
        print("CRITICAL ERROR:")
        traceback.print_exc()

if __name__ == "__main__":
    test_start()
