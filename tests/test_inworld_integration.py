"""
Integration test for Inworld TTS API.

Requires INWORLD_API_KEY environment variable to be set.
Run with: python -m pytest tests/test_inworld_integration.py -v -s
"""

import asyncio
import os

import aiohttp
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("INWORLD_API_KEY"),
    reason="INWORLD_API_KEY not set",
)


@pytest.fixture
async def http_session():
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest.fixture
def tts(http_session):
    from livekit.plugins import inworld

    return inworld.TTS(
        api_key=os.environ["INWORLD_API_KEY"],
        voice=os.getenv("INWORLD_VOICE_ID", "default-oklrorszoxbwzfdj8zjhng__nebu_nino"),
        model=os.getenv("INWORLD_MODEL", "inworld-tts-1.5-mini"),
        speaking_rate=float(os.getenv("INWORLD_SPEAKING_RATE", "1.0")),
        temperature=float(os.getenv("INWORLD_TEMPERATURE", "1.1")),
        http_session=http_session,
    )


@pytest.mark.asyncio
async def test_synthesize_returns_audio(tts):
    """Test that a simple synthesis call returns audio frames."""
    stream = tts.synthesize("Hola, soy Nebu. ¿Cómo estás hoy?")
    frames = []
    async for event in stream:
        if hasattr(event, "frame") and event.frame is not None:
            frames.append(event.frame)

    assert len(frames) > 0, "Expected at least one audio frame"
    total_bytes = sum(len(f.data) for f in frames)
    assert total_bytes > 0, "Expected non-empty audio data"
    print(f"\n  OK: {len(frames)} frames, {total_bytes} bytes total")


@pytest.mark.asyncio
async def test_synthesize_short_text(tts):
    """Test synthesis with very short text."""
    stream = tts.synthesize("Hola")
    frames = []
    async for event in stream:
        if hasattr(event, "frame") and event.frame is not None:
            frames.append(event.frame)

    assert len(frames) > 0, "Short text should still produce audio"
    print(f"\n  OK: {len(frames)} frames for short text")


@pytest.mark.asyncio
async def test_synthesize_long_text(tts):
    """Test synthesis with a longer paragraph."""
    text = (
        "Esta es una prueba más larga para verificar que el servicio de Inworld "
        "puede manejar textos extensos sin problemas. Nebu es un agente de voz "
        "interactivo diseñado para el aprendizaje de los niños."
    )
    stream = tts.synthesize(text)
    frames = []
    async for event in stream:
        if hasattr(event, "frame") and event.frame is not None:
            frames.append(event.frame)

    assert len(frames) > 0, "Long text should produce audio"
    total_bytes = sum(len(f.data) for f in frames)
    print(f"\n  OK: {len(frames)} frames, {total_bytes} bytes for long text")


@pytest.mark.asyncio
async def test_streaming_tts(tts):
    """Test streaming TTS produces incremental audio chunks."""
    stream = tts.stream()
    stream.push_text("Hola, esta es una prueba de streaming. ")
    stream.push_text("Nebu está aprendiendo contigo. ")
    stream.flush()
    stream.end_input()

    frames = []
    async for event in stream:
        if hasattr(event, "frame") and event.frame is not None:
            frames.append(event.frame)

    assert len(frames) > 0, "Streaming should produce audio frames"
    total_bytes = sum(len(f.data) for f in frames)
    print(f"\n  OK: streaming produced {len(frames)} frames, {total_bytes} bytes")


@pytest.mark.asyncio
async def test_concurrent_synthesis(tts):
    """Test that multiple concurrent synthesis requests work."""
    texts = [
        "Primera oración de prueba.",
        "Segunda oración diferente.",
        "Tercera y última prueba.",
    ]

    async def synth(text):
        stream = tts.synthesize(text)
        frames = []
        async for event in stream:
            if hasattr(event, "frame") and event.frame is not None:
                frames.append(event.frame)
        return len(frames)

    results = await asyncio.gather(*[synth(t) for t in texts])
    for i, count in enumerate(results):
        assert count > 0, f"Concurrent request {i} produced no frames"
    print(f"\n  OK: concurrent results = {results} frames each")


@pytest.mark.asyncio
async def test_sample_rate(tts):
    """Verify the TTS reports expected sample rate."""
    assert tts.sample_rate == 24000, f"Expected 24000 Hz, got {tts.sample_rate}"
    print(f"\n  OK: sample_rate = {tts.sample_rate}")
