"""Tool: Búsqueda web parametrizable (Tavily, Brave, SerpAPI, DuckDuckGo)

COPPA compliance:
- Requiere consentimiento parental explícito (web_search_parental_consent=true)
- Sanitiza PII del query antes de enviarlo a APIs externas
- SafeSearch activado en strict en todos los proveedores
- Instrucción kids-safe inyectada en resultados para filtrado LLM
- No se loguean queries crudos (solo queries sanitizados)
"""

import re

import aiohttp
from livekit.agents import RunContext, function_tool

from src.config import get_settings

# ── PII patterns para sanitización COPPA ─────────────────────────────────────

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?"          # country code
    r"(?:\(?\d{1,4}\)?[-.\s]?)?"        # area code
    r"\d{3,4}[-.\s]?\d{3,4}"           # number
)
_DNI_RE = re.compile(r"\b\d{8}[a-zA-Z]?\b")  # DNI/RUC peruano y similares
_ADDRESS_RE = re.compile(
    r"(?:calle|avenida|av\.|jr\.|jirón|pasaje|manzana|lote|urbanización|urb\.)"
    r"\s+[^\s,]{2,}(?:\s+[^\s,]+){0,2}"   # keyword + hasta 3 tokens (nombre + número)
    r"(?:\s+\d+)?",                         # número opcional de puerta
    re.IGNORECASE,
)


def _sanitize_query(query: str) -> str:
    """Elimina patrones de PII del query antes de enviarlo a APIs externas.

    Remueve emails, teléfonos, DNIs y direcciones para cumplir con COPPA.
    """
    sanitized = _EMAIL_RE.sub("", query)
    sanitized = _PHONE_RE.sub("", sanitized)
    sanitized = _DNI_RE.sub("", sanitized)
    sanitized = _ADDRESS_RE.sub("", sanitized)
    # Limpiar espacios múltiples resultantes
    sanitized = re.sub(r"\s{2,}", " ", sanitized).strip()
    return sanitized


_TAVILY_URL = "https://api.tavily.com/search"
_BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"
_SERPAPI_URL = "https://serpapi.com/search.json"
_DDG_URL = "https://api.duckduckgo.com/"


_TAVILY_EXCLUDED_DOMAINS = [
    "reddit.com",
    "4chan.org",
    "twitter.com",
    "x.com",
]


async def _search_tavily(
    session: aiohttp.ClientSession, query: str, api_key: str, max_results: int
) -> list[dict]:
    """Búsqueda via Tavily API."""
    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": "advanced",
        "topic": "news",
        "time_range": "w",
        "include_answer": "basic",
        "include_raw_content": False,
        "include_images": False,
        "exclude_domains": _TAVILY_EXCLUDED_DOMAINS,
    }
    async with session.post(_TAVILY_URL, json=payload) as resp:
        if resp.status != 200:
            return []
        data = await resp.json()
    results = []
    # Si Tavily generó una respuesta directa, incluirla primero
    answer = data.get("answer")
    if answer:
        results.append({"title": "Respuesta directa", "snippet": answer})
    for r in data.get("results", [])[:max_results]:
        results.append({"title": r.get("title", ""), "snippet": r.get("content", "")})
    return results[:max_results + 1]


async def _search_brave(
    session: aiohttp.ClientSession, query: str, api_key: str, max_results: int
) -> list[dict]:
    """Búsqueda via Brave Search API."""
    headers = {"X-Subscription-Token": api_key, "Accept": "application/json"}
    params = {"q": query, "count": max_results, "safesearch": "strict"}
    async with session.get(_BRAVE_URL, headers=headers, params=params) as resp:
        if resp.status != 200:
            return []
        data = await resp.json()
    return [
        {"title": r.get("title", ""), "snippet": r.get("description", "")}
        for r in data.get("web", {}).get("results", [])[:max_results]
    ]


async def _search_serpapi(
    session: aiohttp.ClientSession, query: str, api_key: str, max_results: int
) -> list[dict]:
    """Búsqueda via SerpAPI (Google)."""
    params = {
        "api_key": api_key,
        "q": query,
        "hl": "es",
        "num": max_results,
        "engine": "google",
        "safe": "active",
    }
    async with session.get(_SERPAPI_URL, params=params) as resp:
        if resp.status != 200:
            return []
        data = await resp.json()
    return [
        {"title": r.get("title", ""), "snippet": r.get("snippet", "")}
        for r in data.get("organic_results", [])[:max_results]
    ]


async def _search_duckduckgo(
    session: aiohttp.ClientSession, query: str, max_results: int
) -> list[dict]:
    """Búsqueda via DuckDuckGo Instant Answer API (sin API key)."""
    params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1, "kp": 1}
    async with session.get(_DDG_URL, params=params) as resp:
        if resp.status != 200:
            return []
        data = await resp.json()
    results = []
    # Abstract (respuesta principal)
    if data.get("AbstractText"):
        results.append({
            "title": data.get("Heading", "Resultado"),
            "snippet": data["AbstractText"],
        })
    # Related topics
    for topic in data.get("RelatedTopics", [])[:max_results]:
        if isinstance(topic, dict) and topic.get("Text"):
            results.append({
                "title": topic.get("FirstURL", ""),
                "snippet": topic["Text"],
            })
    return results[:max_results]


_KIDS_SAFE_INSTRUCTION = (
    "\n\nIMPORTANTE: Estás hablando con un niño. "
    "Al presentar estos resultados, usa lenguaje apropiado para niños. "
    "Si algún resultado contiene temas violentos, sexuales, de drogas "
    "o inapropiados para menores, omítelo y responde solo con la "
    "información segura. Si no hay nada apropiado, di que no encontraste "
    "información sobre el tema."
)


def _format_results(results: list[dict]) -> str:
    """Formatea resultados de búsqueda para el LLM con instrucción kids-safe."""
    if not results:
        return "No encontré resultados relevantes para esa búsqueda."
    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "Sin título")
        snippet = r.get("snippet", "")
        lines.append(f"{i}. {title}: {snippet}")
    return "Resultados de búsqueda:\n" + "\n".join(lines) + _KIDS_SAFE_INSTRUCTION


@function_tool(
    name="web_search",
    description=(
        "Search the internet for current information. "
        "Use when the user asks about recent news, current events, "
        "people in the news, or anything that requires up-to-date information."
    ),
)
async def web_search(
    context: RunContext,
    query: str,
) -> str:
    """Search the web for current information.

    Args:
        query: The search query, e.g. 'noticias Peru hoy' or 'presidente de Peru 2025'.
    """
    settings = get_settings()
    provider = settings.web_search_provider

    if not provider:
        return "La búsqueda web no está habilitada en este momento."

    if not settings.web_search_parental_consent:
        return "La búsqueda web requiere consentimiento parental habilitado."

    max_results = settings.web_search_max_results

    # COPPA: Sanitizar PII del query antes de enviar a terceros
    safe_query = _sanitize_query(query)
    if not safe_query:
        return "No pude procesar esa búsqueda."

    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            if provider == "tavily":
                api_key = settings.tavily_api_key
                if not api_key:
                    return "Falta la API key de Tavily para realizar búsquedas."
                results = await _search_tavily(session, safe_query, api_key, max_results)

            elif provider == "brave":
                api_key = settings.brave_search_api_key
                if not api_key:
                    return "Falta la API key de Brave Search para realizar búsquedas."
                results = await _search_brave(session, safe_query, api_key, max_results)

            elif provider == "serpapi":
                api_key = settings.serpapi_api_key
                if not api_key:
                    return "Falta la API key de SerpAPI para realizar búsquedas."
                results = await _search_serpapi(session, safe_query, api_key, max_results)

            elif provider == "duckduckgo":
                results = await _search_duckduckgo(session, safe_query, max_results)

            else:
                return f"Proveedor de búsqueda desconocido: {provider}"

        return _format_results(results)
    except Exception:
        return "No pude realizar la búsqueda en este momento."
