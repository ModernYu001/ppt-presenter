from __future__ import annotations

import threading
import time

from app.integrations.powerpoint_com import PowerPointController


class PresentationService:
    def __init__(self):
        self.controller = PowerPointController()
        self.state = {
            **self.controller.capabilities(),
            "status": "idle",
            "current_slide": None,
            "deck_path": None,
            "last_generated_slide": None,
            "last_narration": "",
            "auto_mode": False,
            "speaking": False,
            "error": "",
        }
        self._runner = None
        self._stop_flag = False
        self._spoken_slides = set()

    def get_state(self):
        try:
            self.state["current_slide"] = self.controller.current_slide_index()
        except Exception:
            pass
        self.state.update(self.controller.capabilities())
        return self.state

    def open_ppt(self, path: str):
        self.controller.open(path)
        self.state["deck_path"] = path
        if self.controller.supports_slideshow_control:
            self.state["status"] = "ready"
            self.state["current_slide"] = None
        else:
            self.state["status"] = "opened-external"
            self.state["current_slide"] = None
        self.state["error"] = ""
        self._spoken_slides.clear()
        return self.get_state()

    def start_slideshow(self):
        if not self.controller.supports_slideshow_control:
            raise RuntimeError("Slide show control is unavailable on this platform")
        self.controller.start_slideshow()
        self.state["status"] = "presenting"
        self.state["current_slide"] = self.controller.current_slide_index()
        self.state["error"] = ""
        self._spoken_slides.clear()
        return self.get_state()

    def next_slide(self):
        if not self.controller.supports_slideshow_control:
            raise RuntimeError("Slide show control is unavailable on this platform")
        self.state["current_slide"] = self.controller.next_slide()
        return self.get_state()

    def previous_slide(self):
        if not self.controller.supports_slideshow_control:
            raise RuntimeError("Slide show control is unavailable on this platform")
        self.state["current_slide"] = self.controller.previous_slide()
        return self.get_state()

    def set_last_narration(self, slide_index: int, text: str):
        self.state["last_generated_slide"] = slide_index
        self.state["last_narration"] = text
        return self.state

    def start_auto_mode(self, runner):
        if not self.controller.supports_slideshow_control:
            raise RuntimeError("Auto presentation requires Windows PowerPoint slide show control")
        if self._runner and self._runner.is_alive():
            self.state["auto_mode"] = True
            return self.state
        self._stop_flag = False
        self.state["auto_mode"] = True
        self.state["error"] = ""
        self._runner = threading.Thread(target=self._loop, args=(runner,), daemon=True)
        self._runner.start()
        return self.state

    def stop_auto_mode(self):
        self._stop_flag = True
        self.state["auto_mode"] = False
        self.state["speaking"] = False
        return self.state

    def mark_slide_unspoken(self, slide_index: int):
        self._spoken_slides.discard(int(slide_index))
        return self.state

    def _loop(self, runner):
        while not self._stop_flag:
            try:
                slide_index = self.controller.current_slide_index()
                self.state["current_slide"] = slide_index
                if slide_index and int(slide_index) not in self._spoken_slides:
                    self.state["speaking"] = True
                    runner(int(slide_index))
                    self.state["speaking"] = False
                    self._spoken_slides.add(int(slide_index))
                time.sleep(0.8)
            except Exception as exc:
                self.state["error"] = str(exc)
                self.state["speaking"] = False
                time.sleep(1.5)
