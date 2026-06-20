"""Tools module for Nebu agent function calling"""

from src.config import Settings

from .datetime_tool import get_current_datetime
from .fun_fact_tool import get_fun_fact
from .games import end_game, start_riddles, start_story, start_trivia
from .weather_tool import get_weather


def get_tools(settings: Settings) -> list:
    """Construye la lista de tools según la configuración activa."""
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
]
