import sys
import asyncio
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QThread, QTimer
import winrt.windows.media.ocr as ocr
import winrt.windows.graphics.imaging as imaging
import winrt.windows.storage.streams as streams
import numpy as np
import cv2

class TestWorker(QThread):
    def __init__(self):
        super().__init__()
        
    def run(self):
        print("QThread run() started.")
        
        # Create a dummy image
        img = np.zeros((100, 300, 3), dtype=np.uint8)
        cv2.putText(img, "QTHREAD OCR SUCCESS", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        rgba = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
        h, w = rgba.shape[:2]
        img_bytes = rgba.tobytes()
        
        writer = streams.DataWriter()
        writer.write_bytes(bytearray(img_bytes))
        
        bitmap = imaging.SoftwareBitmap(imaging.BitmapPixelFormat.RGBA8, w, h)
        bitmap.copy_from_buffer(writer.detach_buffer())
        
        eng = ocr.OcrEngine.try_create_from_user_profile_languages()
        
        async def recognize():
            print("QThread: Awaiting recognize_async...")
            res = await eng.recognize_async(bitmap)
            print("QThread: Awaiting completed.")
            return res
            
        try:
            print("QThread: Calling asyncio.run...")
            result = asyncio.run(recognize())
            print("QThread: asyncio.run finished. Text:", result.text)
        except Exception as e:
            print("QThread Error:", e)

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = TestWorker()
        self.worker.finished.connect(self.worker_finished)
        self.worker.start()
        
    def worker_finished(self):
        print("QThread finished.")
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TestWindow()
    sys.exit(app.exec())
