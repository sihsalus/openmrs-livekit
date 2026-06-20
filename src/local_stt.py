"""Local STT provider using faster-whisper for CPU inference."""

from __future__ import annotations

import asyncio
import io
import wave
from dataclasses import dataclass

from livekit.agents import stt, utils

from src.logger import get_logger

logger = get_logger("nebu.local_stt")


@dataclass
class WhisperConfig:
    model_size: str = "medium"
    language: str = "es"
    compute_type: str = "int8"
    beam_size: int = 5
    device: str = "cpu"


class WhisperSTT(stt.STT):
    """LiveKit STT adapter for faster-whisper (local CPU inference)."""

    def __init__(self, *, config: WhisperConfig | None = None) -> None:
        super().__init__(
            capabilities=stt.STTCapabilities(streaming=False, interim_results=False),
        )
        self._config = config or WhisperConfig()
        self._model = None

    def _ensure_model(self):
        if self._model is not None:
            return
        from faster_whisper import WhisperModel

        logger.info(
            "Loading whisper model",
            extra={
                "model": self._config.model_size,
                "device": self._config.device,
                "compute_type": self._config.compute_type,
            },
        )
        self._model = WhisperModel(
            self._config.model_size,
            device=self._config.device,
            compute_type=self._config.compute_type,
        )

    async def _recognize_impl(
        self,
        buffer: utils.AudioBuffer,
        *,
        language: str | None = None,
    ) -> stt.SpeechEvent:
        self._ensure_model()
        frames = utils.merge_frames(buffer)
        wav_bytes = io.BytesIO()
        with wave.open(wav_bytes, "wb") as wf:
            wf.setnchannels(frames.num_channels)
            wf.setsampwidth(2)
            wf.setframerate(frames.sample_rate)
            wf.writeframes(frames.data)
        wav_bytes.seek(0)

        loop = asyncio.get_running_loop()
        lang = language or self._config.language
        segments, info = await loop.run_in_executor(
            None,
            lambda: self._model.transcribe(
                wav_bytes,
                language=lang,
                beam_size=self._config.beam_size,
            ),
        )
        text = " ".join(seg.text.strip() for seg in segments)
        return stt.SpeechEvent(
            type=stt.SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[stt.SpeechData(text=text, language=lang)],
        )
