# runners/mobile/vision_driver.py
# Mobile-Use vision layout and touch dispatcher

import logging
import subprocess
import time
from typing import Dict, Any, Tuple, Optional

logging.basicConfig(level=logging.INFO, format='[MOBILE_VISION_DRV] %(asctime)s - %(levelname)s - %(message)s')

class MobileVisionDriver:
    def __init__(self, target_device_id: str, platform_type: str = "ANDROID"):
        self.device_id = target_device_id
        self.platform = platform_type.upper()
        if self.platform not in ["ANDROID", "IOS"]:
            raise ValueError("Unsupported execution matrix platform specified.")

    def parse_vision_element_bounds(self, prediction_payload: Dict[str, Any], screen_width: int, screen_height: int) -> Tuple[int, int]:
        box = prediction_payload.get("box_2d")
        if not isinstance(box, (list, tuple)) or len(box) != 4:
            raise ValueError("A four-coordinate box_2d is required")
        if not all(isinstance(value, (int, float)) and 0 <= value <= 1000 for value in box):
            raise ValueError("Coordinates must be normalized to 0..1000")
        ymin, xmin, ymax, xmax = box
        if not (xmin < xmax and ymin < ymax and screen_width > 0 and screen_height > 0):
            raise ValueError("Invalid bounds or viewport")
        x = min(screen_width - 1, int((xmin + xmax) * screen_width / 2000))
        y = min(screen_height - 1, int((ymin + ymax) * screen_height / 2000))
        return x, y

    def dispatch_native_touch_event(self, coordinates: Tuple[int, int]) -> bool:
        x, y = coordinates
        if not (isinstance(x, int) and isinstance(y, int) and x >= 0 and y >= 0):
            raise ValueError("Invalid touch coordinates")
        if self.platform == "ANDROID":
            cmd = ["adb", "-s", self.device_id, "shell", "input", "tap", str(x), str(y)]
            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
                if result.returncode == 0:
                    logging.info(f"Successfully piped physical input touch instruction at target bounds: X={x}, Y={y}")
                    return True
                logging.error(f"ADB execution pipeline threw a platform parameter exception: {result.stderr}")
            except subprocess.TimeoutExpired:
                logging.error("Android bridge execution loop hung indefinitely.")
        elif self.platform == "IOS":
            logging.warning("iOS touch relay is not implemented; no event dispatched")
            return False
        return False

    def sync_device_view_hierarchy(self, screenshot_path: str, layout_dump_path: str) -> Optional[Dict[str, Any]]:
        if self.platform == "ANDROID":
            subprocess.run(["adb", "-s", self.device_id, "shell", "screencap", "-p", "/sdcard/window_frame.png"], check=True)
            subprocess.run(["adb", "-s", self.device_id, "pull", "/sdcard/window_frame.png", screenshot_path], check=True)
            subprocess.run(["adb", "-s", self.device_id, "shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], check=True)
            subprocess.run(["adb", "-s", self.device_id, "pull", "/sdcard/window_dump.xml", layout_dump_path], check=True)
            return {"status": "FRAME_SYNCHRONIZED", "timestamp": int(time.time())}
        return None
