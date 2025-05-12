"""
audio_analyzer.py  – safe‑fallback version
• If a device called “Stereo Mix” exists, use it.
• Otherwise leave PortAudio’s default input unchanged.
• You can still pass an explicit `device` index/name from the UI.
"""

import warnings
import threading
from typing import Any, Dict, Optional

import numpy as np
import sounddevice as sd
from sounddevice import PortAudioError   # only used for caller-side handling


# ---------------------------------------------------------------------------
# Prefer “Stereo Mix”, but don’t crash if it isn’t there
# ---------------------------------------------------------------------------
preferred = next(
    (i for i, d in enumerate(sd.query_devices()) if "Stereo Mix" in d["name"]),
    None,
)

if preferred is not None:
    sd.default.device = (preferred, None)      # (input, output) tuple
    print(f"✓ Using input device: Stereo Mix  (index {preferred})")
else:
    warnings.warn("Stereo Mix not found – using system‑default input device")


# ---------------------------------------------------------------------------
class AudioAnalyzer:
    """
    Real‑time audio capture + basic FFT analyser.
    Call start() / stop(), then read get_audio_data().
    """

    def __init__(
        self,
        sample_rate: int = 44100,
        chunk_size: int = 8192,
        device: Optional[int | str] = None,
    ):
        self.sample_rate = sample_rate
        self.chunk_size  = chunk_size
        self.device      = device            # may be None → use default

        # shared state
        self.volume         = 0.0
        self.dominant_freq  = 0.0
        self.fft_data: list[float] = []

        # open PortAudio stream (caller may need to catch PortAudioError)
        self._stream = sd.InputStream(
            callback=self._callback,
            channels=1,
            samplerate=self.sample_rate,
            blocksize=self.chunk_size,
            device=self.device,
        )

        self._thread = threading.Thread(target=self._stream.start, daemon=True)

    # -----------------------------------------------------------------------
    # PortAudio callback – runs in its own thread
    # -----------------------------------------------------------------------
    def _callback(self, indata, frames, time, status):
        signal = indata[:, 0]

        # --- volume (RMS → dBFS) ------------------------------------------
        rms       = np.sqrt(np.mean(signal ** 2))
        self.volume = 20 * np.log10(max(rms, 1e-10))

        # --- FFT with Hann window -----------------------------------------
        window = np.hanning(len(signal))
        windowed = signal * window
        fft      = np.abs(np.fft.rfft(windowed))
        self.fft_data = fft

        # --- dominant frequency (parabolic interp for sub‑bin accuracy) ----
        peak_bin = int(np.argmax(fft))

        if 1 <= peak_bin < len(fft) - 1:
            alpha, beta, gamma = fft[peak_bin - 1 : peak_bin + 2]
            p = 0.5 * (alpha - gamma) / (alpha - 2 * beta + gamma)
            peak_bin += p                                         # fractional shift

        self.dominant_freq = peak_bin * self.sample_rate / self.chunk_size

    # -----------------------------------------------------------------------
    # public helpers
    # -----------------------------------------------------------------------
    def start(self) -> None:
        """Begin capturing (non‑blocking)."""
        self._thread.start()

    def stop(self) -> None:
        """Gracefully stop the PortAudio stream."""
        try:
            self._stream.stop()
            self._stream.close()
        except Exception as exc:
            print("AudioAnalyzer › error while stopping stream:", exc)

    def get_audio_data(self) -> Dict[str, Any]:
        """Return the latest analysis snapshot."""
        return {
            "volume": self.volume,
            "dominant_freq": self.dominant_freq,
            "fft": self.fft_data,
            "sample_rate": self.sample_rate,
        }
