import cv2
import numpy as np
import asyncio
import winrt.windows.media.ocr as ocr
import winrt.windows.graphics.imaging as imaging
import winrt.windows.storage.streams as streams
import winrt.windows.globalization as glob

async def run_ocr(img, lang_tag="zh-Hant"):
    if len(img.shape) == 2:
        rgba = cv2.cvtColor(img, cv2.COLOR_GRAY2RGBA)
    else:
        rgba = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
    h, w = rgba.shape[:2]
    img_bytes = rgba.tobytes()
    writer = streams.DataWriter()
    writer.write_bytes(bytearray(img_bytes))
    bitmap = imaging.SoftwareBitmap(imaging.BitmapPixelFormat.RGBA8, w, h)
    bitmap.copy_from_buffer(writer.detach_buffer())
    lang = glob.Language(lang_tag)
    eng = ocr.OcrEngine.try_create_from_language(lang)
    result = await eng.recognize_async(bitmap)
    return result.text

def preprocess_yellow_and_time_color_masked(img, scale=2):
    if img is None:
        return None
        
    if scale > 1:
        h, w = img.shape[:2]
        img = cv2.resize(img, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)
        
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Yellow Mask
    lower_yellow = np.array([10, 40, 75])
    upper_yellow = np.array([36, 255, 255])
    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    # White Mask
    lower_white = np.array([0, 0, 110])
    upper_white = np.array([180, 45, 255])
    white_mask = cv2.inRange(hsv, lower_white, upper_white)
    
    combined_mask = np.zeros_like(yellow_mask)
    split_col = int(w * 0.65)
    
    combined_mask[:, :split_col] = yellow_mask[:, :split_col]
    combined_mask[:, split_col:] = cv2.bitwise_or(yellow_mask[:, split_col:], white_mask[:, split_col:])
    
    # Mask original color image
    masked_color = cv2.bitwise_and(img, img, mask=combined_mask)
    
    return masked_color

async def main():
    from PIL import Image, ImageDraw, ImageFont
    
    bg = Image.new("RGB", (600, 120), (20, 20, 20))
    draw = ImageDraw.Draw(bg)
    font = ImageFont.truetype("msjh.ttc", 18)
    
    # Draw yellow text and gray timestamp with anti-aliasing
    draw.text((20, 20), "好友王小明已登入。", fill=(240, 200, 80), font=font)
    draw.text((500, 20), "20:08", fill=(200, 200, 200), font=font)
    
    cv_img = cv2.cvtColor(np.array(bg), cv2.COLOR_RGB2BGR)
    
    processed = preprocess_yellow_and_time_color_masked(cv_img, scale=2)
    result_text = await run_ocr(processed)
    
    def to_ascii_repr(text):
        return text.encode('ascii', 'backslashreplace').decode('ascii')
        
    print("--- OCR Result with Mask-on-Color Preprocessing ---")
    print(to_ascii_repr(result_text))

if __name__ == "__main__":
    asyncio.run(main())
