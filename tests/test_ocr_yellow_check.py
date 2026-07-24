import cv2
import numpy as np
import asyncio
import winrt.windows.media.ocr as ocr
import winrt.windows.graphics.imaging as imaging
import winrt.windows.storage.streams as streams
import winrt.windows.globalization as glob

async def run_ocr_and_filter(img, scale=2):
    # Upscale
    h, w = img.shape[:2]
    img_up = cv2.resize(img, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)
    
    rgba = cv2.cvtColor(img_up, cv2.COLOR_BGR2RGBA)
    img_bytes = rgba.tobytes()
    writer = streams.DataWriter()
    writer.write_bytes(bytearray(img_bytes))
    bitmap = imaging.SoftwareBitmap(imaging.BitmapPixelFormat.RGBA8, w * scale, h * scale)
    bitmap.copy_from_buffer(writer.detach_buffer())
    
    lang = glob.Language("zh-Hant")
    eng = ocr.OcrEngine.try_create_from_language(lang)
    result = await eng.recognize_async(bitmap)
    
    # Original HSV for yellow check
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array([10, 40, 75])
    upper_yellow = np.array([36, 255, 255])
    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    filtered_lines = []
    
    for line_obj in result.lines:
        line_text = line_obj.text.strip()
        if not line_text:
            continue
            
        # Calculate bounding box of the line in original image coords
        min_y = int(min(w.bounding_rect.y for w in line_obj.words) / scale)
        max_y = int(max(w.bounding_rect.y + w.bounding_rect.height for w in line_obj.words) / scale)
        
        # Ensure coordinates are within bounds
        min_y = max(0, min_y)
        max_y = min(h, max_y)
        
        # Slice the yellow mask for this line
        line_yellow_mask = yellow_mask[min_y:max_y, :]
        yellow_count = cv2.countNonZero(line_yellow_mask)
        
        is_yellow = yellow_count > 10
        print(f"Line: '{line_text}' | MinY: {min_y}, MaxY: {max_y} | Yellow Pixels: {yellow_count} | Keep: {is_yellow}")
        
        if is_yellow:
            filtered_lines.append(line_text)
            
    return filtered_lines

async def main():
    from PIL import Image, ImageDraw, ImageFont
    
    bg = Image.new("RGB", (600, 120), (20, 20, 20))
    draw = ImageDraw.Draw(bg)
    font = ImageFont.truetype("msjh.ttc", 18)
    
    # Line 1 (Yellow system message): "獲得了 紅狼巴伯特"
    draw.text((20, 20), "獲得了 紅狼巴伯特", fill=(240, 200, 80), font=font)
    draw.text((500, 20), "20:16", fill=(200, 200, 200), font=font)
    
    # Line 2 (White player message): "玩家A: 打架打起來！"
    draw.text((20, 70), "玩家A: 打架打起來！", fill=(240, 240, 240), font=font)
    draw.text((500, 70), "20:17", fill=(200, 200, 200), font=font)
    
    cv_img = cv2.cvtColor(np.array(bg), cv2.COLOR_RGB2BGR)
    
    print("Running OCR with Post-Filter...")
    results = await run_ocr_and_filter(cv_img)
    print("Final Filtered Lines:", results)

if __name__ == "__main__":
    asyncio.run(main())
