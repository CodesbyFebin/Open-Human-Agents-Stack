from unittest.mock import patch, Mock

import pytest

from runners.mobile.vision_driver import MobileVisionDriver


def test_bounds_are_strict_and_centered():
    driver = MobileVisionDriver("emulator-5554")
    assert driver.parse_vision_element_bounds({"box_2d": [100, 200, 300, 400]}, 1000, 500) == (300, 100)
    for bounds in ([0, 0, 0, 100], [-1, 0, 10, 10], [0, 0, 2000, 10], [0, 0]):
        with pytest.raises(ValueError):
            driver.parse_vision_element_bounds({"box_2d": bounds}, 1000, 500)


def test_ios_never_reports_success_for_unimplemented_touch():
    driver = MobileVisionDriver("ios-test", "IOS")
    assert driver.dispatch_native_touch_event((20, 30)) is False


def test_android_touch_argv_is_fixed_without_shell():
    driver = MobileVisionDriver("emulator-5554", "ANDROID")
    with patch("runners.mobile.vision_driver.subprocess.run", return_value=Mock(returncode=0)) as run:
        assert driver.dispatch_native_touch_event((12, 34)) is True
    args = run.call_args.args[0]
    assert args == ["adb", "-s", "emulator-5554", "shell", "input", "tap", "12", "34"]
    assert run.call_args.kwargs.get("shell") is None
