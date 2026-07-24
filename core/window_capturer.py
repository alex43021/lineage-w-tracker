import ctypes
import logging
import numpy as np
import cv2
import mss
import win32gui
import win32ui
import win32con
from ctypes import wintypes

logger = logging.getLogger(__name__)

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
                    # Match game title but ignore the capturer UI itself
                    if window_title in title and "對話擷取" not in title and "控制台" not in title:
                        # Extra filtering: ensure it's a real game window本體
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
        Background capture using PrintWindow API.
        Returns BGR cv2 image of the client area, or None on failure.
        """
        if not hwnd or not win32gui.IsWindow(hwnd):
            return None

        # 1. Get window geometry
        try:
            win_rect = win32gui.GetWindowRect(hwnd)
            win_w = win_rect[2] - win_rect[0]
            win_h = win_rect[3] - win_rect[1]
            if win_w <= 0 or win_h <= 0:
                return None

            # 2. Get client area size
            client_rect = win32gui.GetClientRect(hwnd)
            client_w = client_rect[2] - client_rect[0]
            client_h = client_rect[3] - client_rect[1]
            if client_w <= 0 or client_h <= 0:
                return None
        except Exception:
            return None

        hwnd_dc = None
        mfc_dc = None
        save_dc = None
        save_bitmap = None
        old_bmp = None
        try:
            # 3. Get window DC & create compatible memory DC
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            if not hwnd_dc:
                return None

            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()

            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, win_w, win_h)

            old_bmp = save_dc.SelectObject(save_bitmap)

            # Paint background black before calling PrintWindow to prevent visual artifacts
            save_dc.PatBlt((0, 0), (win_w, win_h), win32con.BLACKNESS)

            # PrintWindow with flag=3 (PW_CLIENTONLY | PW_RENDERFULLCONTENT) for DX11/12
            PrintWindow = ctypes.windll.user32.PrintWindow
            PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, ctypes.c_uint]
            PrintWindow.restype = wintypes.BOOL
            result = PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)

            if not result:
                return None

            # 4. Extract bitmap bits
            bmp_info = save_bitmap.GetInfo()
            bmp_str = save_bitmap.GetBitmapBits(True)
            img = np.frombuffer(bmp_str, dtype=np.uint8).reshape(
                (bmp_info["bmHeight"], bmp_info["bmWidth"], 4)
            )
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            # 5. Crop client area only
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
            if save_dc is not None:
                if old_bmp is not None:
                    try: save_dc.SelectObject(old_bmp)
                    except: pass
                try: save_dc.DeleteDC()
                except: pass
            if save_bitmap is not None:
                try: win32gui.DeleteObject(save_bitmap.GetHandle())
                except: pass
            if mfc_dc is not None:
                try: mfc_dc.DeleteDC()
                except: pass
            if hwnd_dc is not None:
                try: win32gui.ReleaseDC(hwnd, hwnd_dc)
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
                # PrintWindow succeeded and is not black. Crop region if requested.
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
        # Note: Game window must be visible on the screen (not minimized or completely obscured)
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
            self.close()  # Reset mss instance on failure
            return None
