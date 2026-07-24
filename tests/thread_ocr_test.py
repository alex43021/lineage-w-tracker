import threading
import asyncio
import time
import winrt.windows.media.ocr as ocr
import winrt.windows.graphics.imaging as imaging
import winrt.windows.storage.streams as streams
import numpy as np
import cv2

def run_ocr_in_thread():
    print("Thread started.")
    
    # 1. Create a dummy image
    img = np.zeros((100, 300, 3), dtype=np.uint8)
    cv2.putText(img, "THREAD OCR TEST", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    rgba = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
    h, w = rgba.shape[:2]
    img_bytes = rgba.tobytes()
    
    writer = streams.DataWriter()
    writer.write_bytes(bytearray(img_bytes))
    
    bitmap = imaging.SoftwareBitmap(imaging.BitmapPixelFormat.RGBA8, w, h)
    bitmap.copy_from_buffer(writer.detach_buffer())
    
    eng = ocr.OcrEngine.try_create_from_user_profile_languages()
    if not eng:
        print("Failed to create OCR engine in thread.")
        return
        
    async def recognize():
        print("Awaiting recognize_async...")
        res = await eng.recognize_async(bitmap)
        print("Awaiting finished.")
        return res
        
    try:
        print("Calling asyncio.run...")
        result = asyncio.run(recognize())
        print("asyncio.run finished. Text:", result.text)
    except Exception as e:
        print("Error inside thread:", e)

if __name__ == "__main__":
    t = threading.Thread(target=run_ocr_in_thread)
    t.start()
    t.join()
    print("Done.")
