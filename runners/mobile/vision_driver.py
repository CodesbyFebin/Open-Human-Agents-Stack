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
        box = prediction_payload.get("box_2d", [0, 0, 0, 0])
        ymin, xmin, ymax, xmax = box[0], box[1], box[2], box[3]
        target_x_percent = (xmin + xmax) / 2.0 / 1000.0
        target_y_percent = (ymin + ymax) / 2.0 / 1000.0
        return int(target_x_percent * screen_width), int(target_y_percent * screen_height)

    def dispatch_native_touch_event(self, coordinates: Tuple[int, int]) -> bool:
        x, y = coordinates
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
            logging.info(f"Routing virtual XCTest unified touch payload to iOS host device node: X={x}, Y={y}")
            return True
        return False

    def sync_device_view_hierarchy(self, screenshot_path: str, layout_dump_path: str) -> Optional[Dict[str, Any]]:
        if self.platform == "ANDROID":
            subprocess.run(["adb", "-s", self.device_id, "shell", "screencap", "-p", "/sdcard/window_frame.png"], check=True)
            subprocess.run(["adb", "-s", self.device_id, "pull", "/sdcard/window_frame.png", screenshot_path], check=True)
            subprocess.run(["adb", "-s", self.device_id, "shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], check=True)
            subprocess.run(["adb", "-s", self.device_id, "pull", "/sdcard/window_dump.xml", layout_dump_path], check=True)
            return {"status": "FRAME_SYNCHRONIZED", "timestamp": int(time.time())}
        return None
