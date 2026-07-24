import asyncio
import winrt.windows.media.ocr as ocr
import winrt.windows.graphics.imaging as imaging
import winrt.windows.storage.streams as streams
import numpy as np
import cv2

async def run_ocr_test():
    # 1. Create a dummy black image with a white text
    img = np.zeros((100, 300, 3), dtype=np.uint8)
    cv2.putText(img, "HELLO WORLD", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    
    # Convert BGR to RGBA
    rgba = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
    h, w = rgba.shape[:2]
    img_bytes = rgba.tobytes()
    
    # Write to stream
    writer = streams.DataWriter()
    writer.write_bytes(bytearray(img_bytes))
    
    # SoftwareBitmap
    bitmap = imaging.SoftwareBitmap(imaging.BitmapPixelFormat.RGBA8, w, h)
    bitmap.copy_from_buffer(writer.detach_buffer())
    
    # Create OCR engine
    eng = ocr.OcrEngine.try_create_from_user_profile_languages()
    if not eng:
        print("Failed to create OCR engine.")
        return
        
    print("OcrEngine created. Running recognition...")
    # Await recognition
    result = await eng.recognize_async(bitmap)
    print("Recognized Text:", result.text)
    
    for line in result.lines:
        print("Line:", line.text)

if __name__ == "__main__":
    asyncio.run(run_ocr_test())
