import ctypes
from ctypes import wintypes
import logging
import numpy as np
import cv2
import mss
import win32gui
import win32con

logger = logging.getLogger(__name__)

# Win32 GDI CTypes API Function Setup
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

user32.GetWindowDC.argtypes = [wintypes.HWND]
user32.GetWindowDC.restype = wintypes.HDC

user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.ReleaseDC.restype = ctypes.c_int

gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC

gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP

gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.SelectObject.restype = wintypes.HGDIOBJ

gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.DeleteDC.restype = wintypes.BOOL

gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteObject.restype = wintypes.BOOL

gdi32.PatBlt.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.DWORD]
gdi32.PatBlt.restype = wintypes.BOOL

user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, ctypes.c_uint]
user32.PrintWindow.restype = wintypes.BOOL

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ('biSize', wintypes.DWORD),
        ('biWidth', wintypes.LONG),
        ('biHeight', wintypes.LONG),
        ('biPlanes', wintypes.WORD),
        ('biBitCount', wintypes.WORD),
        ('biCompression', wintypes.DWORD),
        ('biSizeImage', wintypes.DWORD),
        ('biXPelsPerMeter', wintypes.LONG),
        ('biYPelsPerMeter', wintypes.LONG),
        ('biClrUsed', wintypes.DWORD),
        ('biClrImportant', wintypes.DWORD)
    ]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ('bmiHeader', BITMAPINFOHEADER),
        ('bmiColors', wintypes.DWORD * 3)
    ]

gdi32.GetDIBits.argtypes = [
    wintypes.HDC,
    wintypes.HBITMAP,
    ctypes.c_uint,
    ctypes.c_uint,
    ctypes.c_void_p,
    ctypes.POINTER(BITMAPINFO),
    ctypes.c_uint
]
gdi32.GetDIBits.restype = ctypes.c_int

class WindowCapturer:
    def __init__(self):
        self._sct = None

    def get_sct(self):
        """Lazy initialization of mss instance."""
        if self._sct is None:
            self._sct = mss.mss()
        return self._sct

    def close(self):
        """Close mss instance to release resources."""
        if self._sct is not None:
            try:
                self._sct.close()
            except Exception:
                pass
            self._sct = None

    @staticmethod
    def find_all_windows(window_title="天堂W"):
        """Find all windows matching the title, excluding this utility console."""
        def callback(hwnd, windows):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if window_title in title and "對話擷取" not in title and "控制台" not in title:
                        if window_title == "天堂W":
                            is_real_game = (title == "天堂W" or title.startswith("天堂W l ") or title.startswith("天堂W | "))
                            if not is_real_game:
                                return True
                        windows.append({"hwnd": hwnd, "title": title})
            except Exception:
                pass
            return True

        windows = []
        win32gui.EnumWindows(callback, windows)
        return windows

    def get_client_rect(self, hwnd):
        """Get window client area rect (left, top, right, bottom) in screen coordinates."""
        if not hwnd or not win32gui.IsWindow(hwnd):
            return None
        try:
            client_rect = win32gui.GetClientRect(hwnd)
            left_top = win32gui.ClientToScreen(hwnd, (client_rect[0], client_rect[1]))
            right_bottom = win32gui.ClientToScreen(hwnd, (client_rect[2], client_rect[3]))
            return (left_top[0], left_top[1], right_bottom[0], right_bottom[1])
        except Exception as e:
            logger.error(f"Failed to get client rect: {e}")
            return None

    def capture_printwindow(self, hwnd):
        """
        Background capture using PrintWindow API with pure CTypes GDI.
        Guarantees ZERO GDI handle leaks over long-running 100+ hour sessions.
        """
        if not hwnd or not win32gui.IsWindow(hwnd):
            return None

        try:
            win_rect = win32gui.GetWindowRect(hwnd)
            win_w = win_rect[2] - win_rect[0]
            win_h = win_rect[3] - win_rect[1]
            if win_w <= 0 or win_h <= 0:
                return None

            client_rect = win32gui.GetClientRect(hwnd)
            client_w = client_rect[2] - client_rect[0]
            client_h = client_rect[3] - client_rect[1]
            if client_w <= 0 or client_h <= 0:
                return None
        except Exception:
            return None

        hwnd_dc = None
        mem_dc = None
        bitmap = None
        old_bmp = None
        try:
            hwnd_dc = user32.GetWindowDC(hwnd)
            if not hwnd_dc:
                return None

            mem_dc = gdi32.CreateCompatibleDC(hwnd_dc)
            if not mem_dc:
                return None

            bitmap = gdi32.CreateCompatibleBitmap(hwnd_dc, win_w, win_h)
            if not bitmap:
                return None

            old_bmp = gdi32.SelectObject(mem_dc, bitmap)

            # Paint background black before calling PrintWindow to prevent visual artifacts
            gdi32.PatBlt(mem_dc, 0, 0, win_w, win_h, 0x00000042) # BLACKNESS

            # PrintWindow with flag=3 (PW_CLIENTONLY | PW_RENDERFULLCONTENT)
            res = user32.PrintWindow(hwnd, mem_dc, 3)
            if not res:
                return None

            # Prepare BITMAPINFO for raw DIB extraction
            bmi = BITMAPINFO()
            bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmi.bmiHeader.biWidth = win_w
            bmi.bmiHeader.biHeight = -win_h  # Top-down uncompressed DIB
            bmi.bmiHeader.biPlanes = 1
            bmi.bmiHeader.biBitCount = 32
            bmi.bmiHeader.biCompression = 0  # BI_RGB

            buffer = ctypes.create_string_buffer(win_w * win_h * 4)
            lines = gdi32.GetDIBits(mem_dc, bitmap, 0, win_h, buffer, ctypes.byref(bmi), 0)
            if lines == 0:
                return None

            img = np.frombuffer(buffer, dtype=np.uint8).reshape((win_h, win_w, 4))
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            # Crop client area
            left_top_screen = win32gui.ClientToScreen(hwnd, (0, 0))
            offset_x = max(0, min(left_top_screen[0] - win_rect[0], win_w - 1))
            offset_y = max(0, min(left_top_screen[1] - win_rect[1], win_h - 1))
            crop_w = min(client_w, win_w - offset_x)
            crop_h = min(client_h, win_h - offset_y)

            return img_bgr[offset_y:offset_y+crop_h, offset_x:offset_x+crop_w]

        except Exception as e:
            logger.error(f"PrintWindow capture exception: {e}")
            return None
        finally:
            if old_bmp:
                try: gdi32.SelectObject(mem_dc, old_bmp)
                except: pass
            if bitmap:
                try: gdi32.DeleteObject(bitmap)
                except: pass
            if mem_dc:
                try: gdi32.DeleteDC(mem_dc)
                except: pass
            if hwnd_dc:
                try: user32.ReleaseDC(hwnd, hwnd_dc)
                except: pass

    def capture_client_area(self, hwnd, region=None):
        """
        Capture the client area or a specific subregion.
        Tries background PrintWindow first. If it yields a black frame (mean pixel value < 5),
        automatically falls back to screen capture via mss.
        `region`: Tuple of (x, y, w, h) relative to the client area top-left.
        Returns BGR cv2 image, or None on failure.
        """
        if not hwnd or not win32gui.IsWindow(hwnd):
            return None

        rect = self.get_client_rect(hwnd)
        if not rect:
            return None

        win_left, win_top, win_right, win_bottom = rect
        client_w = win_right - win_left
        client_h = win_bottom - win_top

        # 1. Try PrintWindow
        img_bgr = self.capture_printwindow(hwnd)
        if img_bgr is not None:
            mean_val = float(np.mean(img_bgr))
            if mean_val >= 5.0:
                if region:
                    rx, ry, rw, rh = region
                    fh, fw = img_bgr.shape[:2]
                    rx = max(0, min(rx, fw - 1))
                    ry = max(0, min(ry, fh - 1))
                    rw = max(1, min(rw, fw - rx))
                    rh = max(1, min(rh, fh - ry))
                    img_bgr = img_bgr[ry:ry+rh, rx:rx+rw]
                return img_bgr
            else:
                logger.debug("PrintWindow output is mostly black. Falling back to mss.")

        # 2. Fallback to mss (Screen capture)
        monitor = {
            "left": win_left,
            "top": win_top,
            "width": client_w,
            "height": client_h
        }

        if region:
            rx, ry, rw, rh = region
            monitor["left"] += rx
            monitor["top"] += ry
            monitor["width"] = max(1, min(rw, client_w - rx))
            monitor["height"] = max(1, min(rh, client_h - ry))

        try:
            sct = self.get_sct()
            sct_img = sct.grab(monitor)
            img = np.array(sct_img)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img_bgr
        except Exception as e:
            logger.error(f"mss capture failed: {e}")
            self.close()
            return None
