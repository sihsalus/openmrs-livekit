"""Local TTS provider using Piper (subprocess-based, CPU)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from livekit.agents import tts, utils

from src.logger import get_logger

logger = get_logger("nebu.local_tts")

PIPER_SAMPLE_RATE = 22050


@dataclass
class PiperConfig:
    piper_binary: str = "/srv/piper/piper/piper"
    model_path: str = "/srv/piper/voices/es_MX-claude-high.onnx"
    speaker_id: int | None = None
    length_scale: float = 1.0
    sentence_silence: float = 0.2


class PiperTTS(tts.TTS):
    """LiveKit TTS adapter for Piper (local CPU inference via subprocess)."""

    def __init__(self, *, config: PiperConfig | None = None) -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=PIPER_SAMPLE_RATE,
            num_channels=1,
        )
        self._config = config or PiperConfig()

    def synthesize(self, text: str) -> tts.ChunkedStream:
        return PiperChunkedStream(tts=self, text=text, config=self._config)


class PiperChunkedStream(tts.ChunkedStream):
    def __init__(self, *, tts: PiperTTS, text: str, config: PiperConfig) -> None:
        super().__init__(tts=tts, input_text=text)
        self._config = config

    async def _run(self) -> None:
        cmd = [
            self._config.piper_binary,
            "--model",
            self._config.model_path,
            "--output-raw",
            "--length-scale",
            str(self._config.length_scale),
            "--sentence-silence",
            str(self._config.sentence_silence),
        ]
        if self._config.speaker_id is not None:
            cmd += ["--speaker", str(self._config.speaker_id)]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate(input=self._input_text.encode("utf-8"))

        if proc.returncode != 0:
            err_msg = stderr.decode(errors="replace")
            logger.error("Piper failed", extra={"returncode": proc.returncode, "stderr": err_msg})
            return

        frame = utils.AudioFrame(
            data=stdout,
            sample_rate=PIPER_SAMPLE_RATE,
            num_channels=1,
            samples_per_channel=len(stdout) // 2,
        )
        self._event_ch.send_nowait(tts.SynthesizedAudio(frame=frame, request_id=self._request_id))
