"""
Tool registration and setup for the dispatcher.

Initializes the ToolRegistry with metadata for all available tools and
registers their callables with the dispatcher.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.config import Settings
from src.logger import get_logger
from src.tools.dispatcher import ToolMetadata, get_dispatcher, get_registry

if TYPE_CHECKING:
    from livekit.agents import RunContext

logger = get_logger("nebu.tools.setup")


def setup_tool_registry(settings: Settings) -> None:
    """
    Initialize and populate the tool registry based on settings.

    This should be called once during agent initialization before get_tools() is called.
    """
    registry = get_registry()

    # DateTime tool — informational, low priority
    from src.tools.datetime_tool import get_current_datetime

    registry.register(
        ToolMetadata(
            name="get_current_datetime",
            categories=["informational", "utility"],
            keywords=["time", "date", "hour", "today", "now", "current"],
            priority=1,
            description="Get current date and time",
            fallback_tools=[],
        ),
        get_current_datetime,
    )

    # Weather tool — informational
    from src.tools.weather_tool import get_weather

    registry.register(
        ToolMetadata(
            name="get_weather",
            categories=["informational", "utility"],
            keywords=["weather", "rain", "sunny", "temperature", "climate"],
            priority=1,
            description="Get weather information",
            fallback_tools=["web_search"],
        ),
        get_weather,
    )

    # Fun fact tool — entertainment, low priority
    from src.tools.fun_fact_tool import get_fun_fact

    registry.register(
        ToolMetadata(
            name="get_fun_fact",
            categories=["entertainment", "utility"],
            keywords=["fact", "trivia", "interesting", "know", "tell"],
            priority=1,
            description="Get a fun fact",
            fallback_tools=[],
        ),
        get_fun_fact,
    )

    # Web search — general queries, medium priority
    if settings.web_search_provider is not None and settings.web_search_parental_consent:
        from src.tools.web_search_tool import make_web_search

        web_search_fn = make_web_search(settings)
        registry.register(
            ToolMetadata(
                name="web_search",
                categories=["informational", "search"],
                keywords=["search", "find", "look", "how", "what", "where", "when", "why"],
                priority=2,
                description="Search the web for information",
                fallback_tools=[],
            ),
            web_search_fn,
        )

    # OpenMRS clinical tools — highest priority for clinical context
    if settings.enable_openmrs_tools:
        from src.tools.openmrs_tools import (
            make_openmrs_tools,
            record_clinical_fact,
            search_patient,
            show_encounter_draft,
        )

        # Register each OpenMRS tool individually with metadata
        registry.register(
            ToolMetadata(
                name="search_patient",
                categories=["clinical", "openmrs", "search"],
                keywords=["patient", "search", "find", "name", "person", "clinic"],
                priority=8,
                description="Search for a patient in OpenMRS",
                fallback_tools=[],
            ),
            search_patient,
        )

        registry.register(
            ToolMetadata(
                name="record_clinical_fact",
                categories=["clinical", "openmrs", "documentation"],
                keywords=[
                    "symptom",
                    "vital",
                    "sign",
                    "medication",
                    "allergy",
                    "diagnosis",
                    "procedure",
                    "record",
                    "note",
                ],
                priority=9,
                description="Record a clinical fact to the encounter draft",
                fallback_tools=[],
            ),
            record_clinical_fact,
        )

        registry.register(
            ToolMetadata(
                name="show_encounter_draft",
                categories=["clinical", "openmrs", "review"],
                keywords=["encounter", "draft", "review", "summary", "facts", "show", "list"],
                priority=7,
                description="Show the current encounter draft",
                fallback_tools=[],
            ),
            show_encounter_draft,
        )

        logger.info("OpenMRS clinical tools registered")

    # Log registry summary
    summary = get_dispatcher().get_registry_summary()
    logger.info("Tool registry initialized", extra={"summary": summary})


def get_tools_from_registry(settings: Settings) -> list:
    """
    Build tool list from the dispatcher registry.

    This replaces the old get_tools() and automatically initializes the registry
    if needed.
    """
    # Ensure registry is set up
    registry = get_registry()
    if not registry.list_all():
        setup_tool_registry(settings)

    # Return all registered tools as @function_tool decorated functions
    tools = []
    for metadata in registry.list_all():
        callable_fn = registry.get_callable(metadata.name)
        if callable_fn is not None:
            tools.append(callable_fn)

    logger.info("Returning tools from dispatcher", extra={"count": len(tools)})
    return tools
