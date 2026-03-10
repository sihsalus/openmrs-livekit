"""
memory.py — Fetch cross-session memory context from the backend.

At session start, calls the backend's vector memory service to load:
- Recent conversation summaries (what the child talked about before)
- User knowledge (child's interests, fears, achievements)
- Relevant educational content
"""

from src.backend_client import backend_request
from src.config import Settings
from src.logger import get_logger

logger = get_logger("nebu.memory")


async def fetch_memory_context(
    toy_id: str,
    settings: Settings,
    job_logger,
    current_message: str = "inicio de sesión",
) -> str | None:
    """
    Call the backend to build semantic memory context for this toy/child.

    Returns a markdown string to inject into the system prompt, or None on failure.
    Timeout is aggressive (3s) to avoid delaying session startup.
    """
    if not toy_id:
        job_logger.debug("No toy_id available, skipping memory fetch")
        return None

    data = await backend_request(
        settings,
        "POST",
        "vector-memory/context/agent",
        job_logger,
        json={
            "toyId": toy_id,
            "currentMessage": current_message,
            "includePersonality": False,
            "includeMemories": True,
            "includeKnowledge": True,
            "memoriesLimit": 3,
            "knowledgeLimit": 2,
        },
        timeout_seconds=3,
        label="memory fetch",
    )

    if data is None:
        return None

    context = data.get("context", "")
    if context and context.strip():
        job_logger.info(
            "Memory context loaded",
            extra={"toy_id": toy_id, "context_len": len(context)},
        )
        return context.strip()

    job_logger.info("Memory context empty (new toy/child)")
    return None
