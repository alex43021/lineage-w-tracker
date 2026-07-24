import asyncio
import winrt.windows.media.ocr as ocr
import winrt.windows.graphics.imaging as imaging
import winrt.windows.storage.streams as streams
import winrt.windows.globalization as glob
import numpy as np
import cv2

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

async def main():
    from PIL import Image, ImageDraw, ImageFont
    
    bg = Image.new("RGB", (600, 100), (20, 20, 20))
    draw = ImageDraw.Draw(bg)
    
    fonts = ["msjh.ttc", "mingliu.ttc", "arial.ttf"]
    font = None
    for f in fonts:
        try:
            font = ImageFont.truetype(f, 20)
            break
        except:
            continue
            
    # Draw Chinese text
    draw.text((20, 30), "巴風特已在說話頻道出現，請大家前往擊敗！", fill=(240, 200, 80), font=font)
    cv_img = cv2.cvtColor(np.array(bg), cv2.COLOR_RGB2BGR)
    
    # Preprocess
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]
    gray_up = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    _, thresh_150 = cv2.threshold(gray_up, 150, 255, cv2.THRESH_BINARY)
    _, thresh_100 = cv2.threshold(gray_up, 100, 255, cv2.THRESH_BINARY)

    def to_ascii_repr(text):
        return text.encode('ascii', 'backslashreplace').decode('ascii')

    print("1. Raw Color:", to_ascii_repr(await run_ocr(cv_img)))
    print("2. Grayscale:", to_ascii_repr(await run_ocr(gray)))
    print("3. Grayscale Upscaled:", to_ascii_repr(await run_ocr(gray_up)))
    print("4. Binarized (150, scale=2):", to_ascii_repr(await run_ocr(thresh_150)))
    print("5. Binarized (100, scale=2):", to_ascii_repr(await run_ocr(thresh_100)))

if __name__ == "__main__":
    asyncio.run(main())
