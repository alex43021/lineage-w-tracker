import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class OCREngine:
    def __init__(self, lang=None):
        self.lang = lang
        self.paddle_ocr = None

    @staticmethod
    def get_available_languages():
        """
        Returns a list of supported OCR languages.
        """
        return [
            ("zh-Hant", "繁體中文 (Traditional Chinese)"),
            ("zh-Hans", "简体中文 (Simplified Chinese)"),
            ("en-US", "English (United States)"),
            ("ko-KR", "한국어 (Korean)"),
        ]

    def preprocess_image(self, img, threshold_val=150, scale=2, use_binarization=False, use_yellow_filter=True, for_ocr=True):
        """
        Preprocess the chat screenshot to maximize OCR accuracy:
        1. Resize (upscale) by `scale` factor.
        2. Apply color masking or binarization.
        """
        if img is None:
            return None

        # 1. Resize to enlarge text (makes OCR of small fonts much more reliable)
        if scale > 1:
            h, w = img.shape[:2]
            img = cv2.resize(img, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)

        if use_yellow_filter:
            # Yellow-only + Timestamp mask:
            # Left 65%: Keep only yellow system words (H: 10-36, S: 40-255, V: 75-255)
            # Right 35%: Keep yellow OR white/grey timestamps (V >= 80, S <= 55)
            h, w = img.shape[:2]
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            lower_yellow = np.array([10, 40, 75])
            upper_yellow = np.array([36, 255, 255])
            yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
            
            lower_white = np.array([0, 0, 80])
            upper_white = np.array([180, 55, 255])
            white_mask = cv2.inRange(hsv, lower_white, upper_white)
            
            combined_mask = np.zeros_like(yellow_mask)
            split_col = int(w * 0.65) # Left 65% keeps only yellow, right 35% keeps yellow or white/gray
            
            combined_mask[:, :split_col] = yellow_mask[:, :split_col]
            combined_mask[:, split_col:] = cv2.bitwise_or(yellow_mask[:, split_col:], white_mask[:, split_col:])
            
            # Apply mask to the original color image to preserve anti-aliased text boundaries and colors
            masked_color = cv2.bitwise_and(img, img, mask=combined_mask)
            return masked_color

        if not use_binarization:
            return img

        # 2. Convert to Grayscale & Binary Thresholding (optional)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, threshold_val, 255, cv2.THRESH_BINARY)
        return thresh

    def recognize_text(self, img, threshold_val=150, scale=2, use_binarization=False, use_yellow_filter=True, engine_type="paddleocr"):
        """
        Preprocesses the image and performs OCR using PaddleOCR.
        Returns:
            dict containing:
                'text': Full recognized text as a single string.
                'lines': List of recognized lines (text only).
        """
        try:
            # Lazy initialize PaddleOCR in the worker thread (prevents UI freeze during startup)
            if self.paddle_ocr is None:
                logger.info("Initializing PaddleOCR with flagship Chinese model (ch)...")
                from paddleocr import PaddleOCR
                self.paddle_ocr = PaddleOCR(
                    use_angle_cls=False, 
                    lang="ch",
                    show_log=False,
                    enable_mkldnn=False
                )

            proc_img = self.preprocess_image(
                img, 
                threshold_val=threshold_val, 
                scale=scale, 
                use_binarization=use_binarization,
                use_yellow_filter=use_yellow_filter,
                for_ocr=True
            )
            if proc_img is None:
                return {"text": "", "lines": []}

            # Check if there is enough active text content (non-black pixels) to run OCR
            gray_proc = cv2.cvtColor(proc_img, cv2.COLOR_BGR2GRAY)
            non_zero_count = cv2.countNonZero(gray_proc)
            del gray_proc

            if non_zero_count < 150:
                del proc_img
                return {"text": "", "lines": []}

            # Run PaddleOCR
            result = self.paddle_ocr.ocr(proc_img, cls=False)
            del proc_img
            
            text_lines = []
            if result and result[0]:
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                lower_yellow = np.array([5, 20, 50])
                upper_yellow = np.array([45, 255, 255])
                yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
                del hsv

                for line_data in result[0]:
                    line_text = line_data[1][0].strip()
                    if not line_text:
                        continue
                    
                    # Convert to Traditional Chinese using zhconv
                    try:
                        import zhconv
                        line_text = zhconv.convert(line_text, 'zh-hant')
                    except Exception as e:
                        logger.error(f"zhconv convert failed: {e}")
                    
                    if use_yellow_filter:
                        try:
                            # Bounding box coords format in PaddleOCR: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                            box = line_data[0]
                            ys = [pt[1] for pt in box]
                            min_y = int(min(ys) / scale)
                            max_y = int(max(ys) / scale)
                            
                            min_y = max(0, min_y)
                            max_y = min(img.shape[0], max_y)
                            
                            line_yellow_mask = yellow_mask[min_y:max_y, :]
                            yellow_count = cv2.countNonZero(line_yellow_mask)
                            
                            if yellow_count < 15:
                                continue
                        except Exception as e:
                            logger.error(f"PaddleOCR yellow count check failed: {e}")
                            
                    text_lines.append(line_text)
                
                del yellow_mask
            
            full_text = " ".join(text_lines)
            return {
                "text": full_text,
                "lines": text_lines
            }
        except Exception as e:
            logger.error(f"PaddleOCR recognition failed: {e}")
            return {"text": "", "lines": []}
