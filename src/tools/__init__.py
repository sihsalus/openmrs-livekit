"""Tools module for Nebu agent function calling

Now includes intelligent tool dispatching via dispatcher.py and setup.py.

Usage:
    from src.tools import get_tools, init_dispatcher
    
    # Initialize dispatcher once during agent setup
    init_dispatcher(settings)
    
    # Get tools for agent (now with dispatcher registry)
    tools = get_tools(settings)
"""

from src.config import Settings

from .datetime_tool import get_current_datetime
from .dispatcher import get_dispatcher, get_registry
from .fun_fact_tool import get_fun_fact
from .games import end_game, start_riddles, start_story, start_trivia
from .setup import get_tools_from_registry, setup_tool_registry
from .weather_tool import get_weather


def init_dispatcher(settings: Settings) -> None:
    """Initialize the tool dispatcher and registry.
    
    Should be called once early in agent lifecycle before tools are used.
    """
    setup_tool_registry(settings)


def get_tools(settings: Settings) -> list:
    """
    Get available tools for the agent.
    
    Intelligently routes through dispatcher if registry is initialized,
    otherwise falls back to legacy list-building for compatibility.
    """
    registry = get_registry()
    if registry.list_all():
        # Use dispatcher-based tools (registry already initialized)
        return get_tools_from_registry(settings)
    else:
        # Fallback to legacy behavior if dispatcher not initialized
        # (This maintains backward compatibility)
        tools = [
            get_current_datetime,
            get_weather,
            get_fun_fact,
            # start_trivia, start_riddles, start_story, end_game — disabled: Groq rejects no-param tool schemas
        ]

        if settings.web_search_provider is not None and settings.web_search_parental_consent:
            from .web_search_tool import make_web_search

            tools.append(make_web_search(settings))

        if settings.enable_openmrs_tools:
            from .openmrs_tools import make_openmrs_tools

            tools.extend(make_openmrs_tools(settings))

        return tools


__all__ = [
    "get_current_datetime",
    "get_weather",
    "get_fun_fact",
    "start_trivia",
    "start_riddles",
    "start_story",
    "end_game",
    "get_tools",
    "init_dispatcher",
    "get_dispatcher",
    "get_registry",
    "setup_tool_registry",
    "get_tools_from_registry",
]
