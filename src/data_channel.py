"""
data_channel.py — Publish structured messages to the frontend via LiveKit data channel.

The frontend ESM subscribes to DataReceived events and parses JSON messages
with a `type` field. Supported types:
- transcript: a speech transcript (doctor or patient)
- translation: a translated transcript
- draft: an encounter draft object
- status: pipeline step status update
- error: an error message
"""

from __future__ import annotations

import json
import logging

from livekit import rtc

logger = logging.getLogger("nebu.data_channel")


async def publish_message(room: rtc.Room, msg_type: str, payload: dict[str, object]) -> None:
    message = json.dumps({"type": msg_type, "payload": payload})
    try:
        await room.local_participant.publish_data(
            message.encode("utf-8"),
            reliable=True,
            topic="agent-data",
        )
    except Exception as e:
        logger.warning("Failed to publish data message: %s", e)


async def publish_transcript(
    room: rtc.Room,
    role: str,
    language: str,
    text: str,
    redacted: str | None = None,
) -> None:
    await publish_message(room, "transcript", {
        "role": role,
        "language": language,
        "text": text,
        "redacted": redacted or text,
    })


async def publish_translation(
    room: rtc.Room,
    role: str,
    source_language: str,
    target_language: str,
    text: str,
) -> None:
    await publish_message(room, "translation", {
        "role": role,
        "language": target_language,
        "text": text,
        "sourceLanguage": source_language,
    })


async def publish_draft(room: rtc.Room, draft: dict[str, object]) -> None:
    await publish_message(room, "draft", draft)


async def publish_status(room: rtc.Room, step: str, message: str = "") -> None:
    await publish_message(room, "status", {
        "step": step,
        "message": message,
    })


async def publish_error(room: rtc.Room, message: str) -> None:
    await publish_message(room, "error", {"message": message})
