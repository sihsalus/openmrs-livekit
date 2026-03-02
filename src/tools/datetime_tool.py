"""Tool: Hora y fecha actual"""
import datetime
from zoneinfo import ZoneInfo

from livekit.agents import function_tool, RunContext


@function_tool(
    name="get_current_datetime",
    description="Get the current date and time. Use this when the user asks what time or date it is.",
)
async def get_current_datetime(
    context: RunContext,
    timezone: str = "America/Bogota",
) -> str:
    """Get the current date and time in the specified timezone.

    Args:
        timezone: IANA timezone string, e.g. 'America/Bogota', 'America/Mexico_City'.
    """
    try:
        tz = ZoneInfo(timezone)
    except KeyError:
        tz = ZoneInfo("UTC")

    now = datetime.datetime.now(tz)
    days = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    months = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]

    return (
        f"Hoy es {days[now.weekday()]} {now.day} de {months[now.month - 1]} de {now.year}. "
        f"Son las {now.strftime('%H:%M')} horas."
    )
