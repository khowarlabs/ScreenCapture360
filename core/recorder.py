"""
core/recorder.py
Background recording thread — captures frames from a monitor or application
window and audio from the microphone, muxing them into an MP4 using PyAV.
"""
import threading
import time
from datetime import datetime
from pathlib import Path
import queue

import av
import cv2
import mss
import numpy as np
import pygetwindow as gw
import sounddevice as sd
from PyQt6.QtCore import QThread, pyqtSignal


class RecorderThread(QThread):
    """
    QThread that captures screen frames and microphone audio, muxing them
    into a single MP4 file using PyAV.
    """

    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, capture_config: dict, fps: int = 15, parent=None) -> None:
        super().__init__(parent)
        self._config = capture_config
        self._fps = fps
        self._pause_event = threading.Event()
        self._stop_event = threading.Event()
        self._pause_event.set()
        
        self._mic_enabled = True
        self._audio_queue = queue.Queue()
        self._output_path = self._build_output_path()

    def pause(self) -> None:
        self._pause_event.clear()

    def resume(self) -> None:
        self._pause_event.set()

    def toggle_mic(self, enabled: bool) -> None:
        """Enable or disable microphone audio mid-recording."""
        self._mic_enabled = enabled

    def stop_recording(self) -> None:
        self._stop_event.set()
        self._pause_event.set()

    @staticmethod
    def _build_output_path() -> str:
        videos_dir = Path.home() / "Videos"
        videos_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return str(videos_dir / f"record_{timestamp}.mp4")

    def _get_capture_region(self) -> dict | None:
        if self._config["type"] == "monitor":
            return self._config["monitor"]

        title = self._config["window_title"]
        windows = gw.getWindowsWithTitle(title)
        if not windows:
            return None
        win = windows[0]
        if win.width <= 0 or win.height <= 0:
            return None
        return {
            "left": win.left,
            "top": win.top,
            "width": win.width,
            "height": win.height,
        }

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for sounddevice.InputStream."""
        if status:
            print(f"Audio status: {status}")
        # If mic is disabled, we push zeros to keep the stream moving but silent
        if not self._mic_enabled:
            self._audio_queue.put(np.zeros_like(indata))
        else:
            self._audio_queue.put(indata.copy())

    def run(self) -> None:  # noqa: max-complexity
        container = None
        v_stream = None
        a_stream = None
        audio_input = None

        try:
            # Audio setup
            sample_rate = 44100
            channels = 1
            audio_input = sd.InputStream(
                samplerate=sample_rate,
                channels=channels,
                callback=self._audio_callback
            )
            audio_input.start()

            frame_interval = 1.0 / self._fps
            start_time = time.perf_counter()
            pts_video = 0
            pts_audio = 0

            with mss.mss() as sct:
                while not self._stop_event.is_set():
                    loop_start = time.perf_counter()

                    self._pause_event.wait()
                    if self._stop_event.is_set():
                        break

                    region = self._get_capture_region()
                    if region is None:
                        break

                    # Capture frame
                    screenshot = sct.grab(region)
                    img = np.array(screenshot)
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                    # Lazy init container
                    if container is None:
                        h, w = img.shape[:2]
                        # Ensure dimensions are even (H.264 requirement)
                        w = w if w % 2 == 0 else w - 1
                        h = h if h % 2 == 0 else h - 1
                        img = img[:h, :w]

                        container = av.open(self._output_path, mode='w')
                        
                        # Video stream
                        v_stream = container.add_stream('libx264', rate=self._fps)
                        v_stream.codec_context.width = w
                        v_stream.codec_context.height = h
                        v_stream.codec_context.pix_fmt = 'yuv420p'
                        v_stream.codec_context.options = {'preset': 'ultrafast', 'crf': '23'}

                        # Audio stream
                        a_stream = container.add_stream('aac', rate=sample_rate)
                        a_stream.codec_context.layout = 'mono'
                        a_stream.codec_context.format = 'fltp'
                        a_stream.codec_context.sample_rate = sample_rate

                    # Process Video Frame
                    frame = av.VideoFrame.from_ndarray(img, format='bgr24')
                    frame.pts = pts_video
                    pts_video += 1
                    for packet in v_stream.encode(frame):
                        container.mux(packet)

                    # Process Audio from Queue
                    while not self._audio_queue.empty():
                        data = self._audio_queue.get()
                        # Convert float32 to av.AudioFrame
                        # sounddevice gives (N, channels), need (channels, N) for PyAV fltp
                        data = data.T.astype(np.float32)
                        a_frame = av.AudioFrame.from_ndarray(data, format='fltp', layout='mono')
                        a_frame.sample_rate = sample_rate
                        a_frame.pts = pts_audio
                        pts_audio += a_frame.samples
                        for packet in a_stream.encode(a_frame):
                            container.mux(packet)

                    # Throttle
                    elapsed = time.perf_counter() - loop_start
                    sleep_for = frame_interval - elapsed
                    if sleep_for > 0:
                        time.sleep(sleep_for)

            # Flush encoders
            if v_stream:
                for packet in v_stream.encode():
                    container.mux(packet)
            if a_stream:
                for packet in a_stream.encode():
                    container.mux(packet)

            if container:
                container.close()

            self.finished.emit(self._output_path)

        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            if audio_input:
                audio_input.stop()
                audio_input.close()
