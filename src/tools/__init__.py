"""Tools module — clinical encounter tools for OpenMRS."""

from src.config import Settings

from .datetime_tool import get_current_datetime
from .openmrs_tools import make_openmrs_tools


def get_tools(settings: Settings) -> list:
    tools = [get_current_datetime]
    if settings.enable_openmrs_tools:
        tools.extend(make_openmrs_tools(settings))
    return tools
