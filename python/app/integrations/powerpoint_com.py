from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class BasePowerPointController:
    platform = sys.platform
    open_strategy = "unsupported"
    supports_slideshow_control = False

    def open(self, path: str):
        raise NotImplementedError

    def start_slideshow(self):
        raise RuntimeError("Slide show control is not available on this platform")

    def current_slide_index(self) -> int | None:
        return None

    def next_slide(self):
        raise RuntimeError("Slide show control is not available on this platform")

    def previous_slide(self):
        raise RuntimeError("Slide show control is not available on this platform")

    def capabilities(self):
        return {
            "platform": self.platform,
            "open_strategy": self.open_strategy,
            "supports_slideshow_control": self.supports_slideshow_control,
        }


class WindowsPowerPointController(BasePowerPointController):
    """Windows PowerPoint COM controller."""

    platform = "win32"
    open_strategy = "powerpoint-com"
    supports_slideshow_control = True

    def __init__(self):
        self._app = None
        self._presentation = None
        self._slideshow = None

    def _ensure_windows(self):
        try:
            import win32com.client  # noqa: F401
        except Exception as exc:
            raise RuntimeError("PowerPoint COM is available only on Windows with pywin32 and PowerPoint installed") from exc

    def open(self, path: str):
        self._ensure_windows()
        import win32com.client

        if self._app is None:
            self._app = win32com.client.Dispatch("PowerPoint.Application")
            self._app.Visible = True
        self._presentation = self._app.Presentations.Open(path, WithWindow=True)
        return True

    def start_slideshow(self):
        if self._presentation is None:
            raise RuntimeError("No presentation opened")
        settings = self._presentation.SlideShowSettings
        self._slideshow = settings.Run()
        return True

    def current_slide_index(self) -> int | None:
        if self._slideshow is None:
            return None
        try:
            return int(self._slideshow.View.CurrentShowPosition)
        except Exception:
            return None

    def next_slide(self):
        if self._slideshow is None:
            raise RuntimeError("Slideshow not started")
        self._slideshow.View.Next()
        return self.current_slide_index()

    def previous_slide(self):
        if self._slideshow is None:
            raise RuntimeError("Slideshow not started")
        self._slideshow.View.Previous()
        return self.current_slide_index()


class MacPowerPointController(BasePowerPointController):
    """macOS controller that opens the deck in the default app without slideshow automation."""

    platform = "darwin"
    open_strategy = "open-command"
    supports_slideshow_control = False

    def __init__(self):
        self._presentation_path = None

    def open(self, path: str):
        ppt_path = Path(path).expanduser().resolve()
        if not ppt_path.exists():
            raise FileNotFoundError(f"PPT file not found: {ppt_path}")
        try:
            subprocess.Popen(["open", str(ppt_path)])
        except Exception as exc:
            raise RuntimeError(f"Failed to open presentation via macOS 'open': {exc}") from exc
        self._presentation_path = str(ppt_path)
        return True


class UnsupportedPowerPointController(BasePowerPointController):
    def open(self, path: str):
        raise RuntimeError("PowerPoint integration is only available on Windows and macOS")


def PowerPointController():
    if sys.platform == "win32":
        return WindowsPowerPointController()
    if sys.platform == "darwin":
        return MacPowerPointController()
    return UnsupportedPowerPointController()
