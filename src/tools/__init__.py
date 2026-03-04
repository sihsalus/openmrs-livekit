"""Tools module for Nebu agent function calling"""
from src.config import get_settings

from .datetime_tool import get_current_datetime
from .fun_fact_tool import get_fun_fact
from .games import end_game, start_riddles, start_story, start_trivia
from .weather_tool import get_weather

ALL_TOOLS = [
    get_current_datetime,
    get_weather,
    get_fun_fact,
    start_trivia,
    start_riddles,
    start_story,
    end_game,
]

# Registrar búsqueda web solo si hay proveedor configurado Y consentimiento parental
_settings = get_settings()
if _settings.web_search_provider is not None and _settings.web_search_parental_consent:
    from .web_search_tool import web_search
    ALL_TOOLS.append(web_search)

__all__ = [
    "get_current_datetime", "get_weather", "get_fun_fact",
    "start_trivia", "start_riddles", "start_story", "end_game",
    "ALL_TOOLS",
]
