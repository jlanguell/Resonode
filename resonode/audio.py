"""Near-real-time utterance chunking — the seam from batch to streaming STT.

Discord delivers 48 kHz, 16-bit, stereo PCM per speaker. This buffers one
speaker's PCM and emits a complete 'utterance' when it detects a pause, so each
utterance can be transcribed as it finishes instead of waiting for !leave.
Energy(RMS)-based VAD via numpy (no native deps).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

DISCORD_RATE = 48000
DISCORD_CHANNELS = 2
SAMPLE_WIDTH = 2  # bytes (16-bit)


@dataclass
class UtteranceChunker:
    sample_rate: int = DISCORD_RATE
    channels: int = DISCORD_CHANNELS
    sample_width: int = SAMPLE_WIDTH
    silence_rms: float = 500.0       # below this RMS counts as silence
    min_silence_ms: float = 600.0    # pause length that closes an utterance
    min_utterance_ms: float = 400.0  # ignore blips shorter than this
    max_utterance_ms: float = 15000.0  # force-flush long monologues
    _buf: bytearray = field(default_factory=bytearray)
    _silence_ms: float = 0.0
    _voiced_ms: float = 0.0

    def _ms(self, nbytes: int) -> float:
        frames = nbytes / (self.channels * self.sample_width)
        return frames / self.sample_rate * 1000.0

    @property
    def has_pending(self) -> bool:
        """True once enough *voiced* audio is buffered to be worth transcribing."""
        return self._voiced_ms >= self.min_utterance_ms

    def feed(self, pcm: bytes) -> list[bytes]:
        """Feed a block of PCM; return any completed utterance buffers."""
        if not pcm:
            return []
        samples = np.frombuffer(pcm, dtype=np.int16).astype(np.float32)
        rms = float(np.sqrt(np.mean(np.square(samples)))) if samples.size else 0.0
        dur = self._ms(len(pcm))
        self._buf.extend(pcm)
        if rms < self.silence_rms:
            self._silence_ms += dur
        else:
            self._silence_ms = 0.0
            self._voiced_ms += dur
        ended = (
            self._silence_ms >= self.min_silence_ms and self._voiced_ms >= self.min_utterance_ms
        )
        if ended or self._ms(len(self._buf)) >= self.max_utterance_ms:
            return [self.flush()]
        return []

    def flush(self) -> bytes:
        data = bytes(self._buf)
        self._buf = bytearray()
        self._silence_ms = 0.0
        self._voiced_ms = 0.0
        return data
