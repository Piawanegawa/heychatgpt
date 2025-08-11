"""Wake-word detection with interchangeable backends.

Two backends are provided:

``porcupine``
    Uses `pvporcupine` for robust on-device wake word detection.
``sapi``
    Uses the Windows Speech API through the :mod:`speech_recognition`
    package to spot the keyword in partial transcription results.

Both backends honour a simple debounce so that at least five seconds
must pass between detections.  When the global logging level is set to
``DEBUG`` a message is written when the wake word is detected.
"""
from __future__ import annotations

from typing import Callable, Optional, TYPE_CHECKING
import logging
import time

from .stream import AudioStream

try:  # Optional dependencies
    import pvporcupine  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pvporcupine = None

try:
    import speech_recognition as sr  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    sr = None

if TYPE_CHECKING:  # pragma: no cover
    from config import Settings


class WakeWordDetector:
    """Detect a wake word using one of the supported backends."""

    debounce_seconds = 5.0

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.debug = self.logger.isEnabledFor(logging.DEBUG)
        self._last_trigger = 0.0
        backend = settings.stt_backend
        if backend == "porcupine":
            if pvporcupine is None:  # pragma: no cover - runtime dependency
                raise RuntimeError("pvporcupine is required for this backend")
            self._engine = pvporcupine.create(
                keywords=[settings.wake_word.lower()],
                sensitivities=[settings.porcupine_sensitivity],
            )
            self.sample_rate = self._engine.sample_rate
            self.frame_length = self._engine.frame_length
            self.backend = "porcupine"
        elif backend == "sapi":
            if sr is None:  # pragma: no cover - runtime dependency
                raise RuntimeError("SpeechRecognition is required for this backend")
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone(device_index=settings.device_index)
            self.keyword = settings.wake_word.lower()
            self.backend = "sapi"
        else:
            raise ValueError(f"Unknown backend: {backend}")

    # ------------------------------------------------------------------
    def _debounced(self) -> bool:
        now = time.monotonic()
        if now - self._last_trigger < self.debounce_seconds:
            return False
        self._last_trigger = now
        return True

    # ------------------------------------------------------------------
    def listen(self, callback: Optional[Callable[[], None]] = None) -> None:
        """Block until the wake word is detected.

        Parameters
        ----------
        callback:
            Optional callable invoked when the wake word is detected.
        """

        if self.backend == "porcupine":
            with AudioStream(
                device_index=self.settings.device_index,
                rate=self.sample_rate,
                frames_per_buffer=self.frame_length,
            ) as stream:
                for frame in stream.frames():
                    if self._engine.process(frame) >= 0 and self._debounced():
                        if self.debug:
                            self.logger.debug("Wake word detected (porcupine)")
                        if callback:
                            callback()
                        return
        else:  # sapi backend
            while True:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, phrase_time_limit=5)
                try:
                    result = self.recognizer.recognize_sphinx(
                        audio, keyword_entries=[(self.keyword, 1.0)]
                    )
                except sr.UnknownValueError:  # type: ignore[attr-defined]
                    continue
                if self.keyword in result.lower() and self._debounced():
                    if self.debug:
                        self.logger.debug("Wake word detected (sapi)")
                    if callback:
                        callback()
                    return
