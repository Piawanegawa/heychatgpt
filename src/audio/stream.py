"""Utility to capture audio using PortAudio with a selectable input device.

This module wraps :mod:`pyaudio` to provide an iterator over raw 16-bit
PCM audio frames.  The default configuration captures mono audio at
16 kHz which matches the requirements of most wake-word engines.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator
import array

try:
    import pyaudio  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pyaudio = None


@dataclass
class AudioStream:
    """Simple PortAudio microphone stream.

    Parameters
    ----------
    device_index:
        Index of the input device to use.  ``0`` selects the default
        device.  See :func:`pyaudio.PyAudio.get_device_info_by_index`
        for details on available devices.
    rate:
        Sample rate in Hertz.  ``16000`` is a sensible default for most
        speech related models.
    channels:
        Number of audio channels, default is ``1`` (mono).
    frames_per_buffer:
        Number of samples read per call.
    """

    device_index: int = 0
    rate: int = 16000
    channels: int = 1
    frames_per_buffer: int = 512

    _pa: pyaudio.PyAudio | None = None
    _stream: pyaudio.Stream | None = None

    def __enter__(self) -> "AudioStream":
        if pyaudio is None:  # pragma: no cover - handled at runtime
            raise RuntimeError("pyaudio is required for AudioStream")
        self._pa = pyaudio.PyAudio()
        self._stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.frames_per_buffer,
            input_device_index=self.device_index,
        )
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._stream is not None:
            self._stream.stop_stream()
            self._stream.close()
        if self._pa is not None:
            self._pa.terminate()

    # ------------------------------------------------------------------
    def frames(self) -> Iterator[array.array]:
        """Yield successive PCM frames from the stream.

        Each item yielded is an :class:`array.array` of type ``"h"``
        containing 16-bit signed integers.
        """

        if not self._stream:
            raise RuntimeError("AudioStream is not open")
        while True:
            data = self._stream.read(self.frames_per_buffer)
            yield array.array("h", data)
