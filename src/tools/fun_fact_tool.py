"""Tool: Datos curiosos dinámicos (sin lista estática).

Usa el VarietyEngine para:
- Rotar entre 12 categorías temáticas (animales, espacio, historia...)
- Nunca repetir la misma categoría consecutivamente
- Variar el estilo de entrega (secreto, desafío, asombro...)
- Inyectar los datos ya contados al prompt para que el LLM no repita

El LLM genera el contenido - tiene miles de datos curiosos en su entrenamiento.
Nosotros solo lo guiamos para que no se repita.
"""

from livekit.agents import RunContext, function_tool

from src.prompt_budget import estimate_tokens, truncate_to_tokens


def _truncate_fact_prompt(prompt: str, max_tokens: int) -> str:
    """Recorta preservando la sección del dato curioso, no solo el prefacio."""
    if estimate_tokens(prompt) <= max_tokens:
        return prompt

    marker = "## DATO CURIOSO"
    if marker not in prompt:
        return truncate_to_tokens(prompt, max_tokens)

    prefix, suffix = prompt.split(marker, 1)
    prefix_budget = min(18, max_tokens // 3)
    prefix_text = truncate_to_tokens(prefix.rstrip(), prefix_budget)
    remaining_tokens = max(8, max_tokens - estimate_tokens(prefix_text) - 1)
    suffix_text = truncate_to_tokens(f"{marker}{suffix}", remaining_tokens)
    return f"{prefix_text}\n...\n{suffix_text}"


@function_tool(
    name="get_fun_fact",
    description="Get a surprising real-world fun fact. Use when the user asks for something interesting, curious, or wants to learn something new. Always provide a unique, little-known fact.",
)
async def get_fun_fact(
    context: RunContext,
    topic: str = "",
) -> str:
    """Get a random fun fact, optionally about a specific topic.

    Args:
        topic: Optional topic hint (e.g. 'animals', 'space', 'science').
    """
    variety = context.session.userdata.get("variety")

    if variety is None:
        return "Cuenta un dato curioso REAL, poco conocido y sorprendente para un niño. Nada de chistes sobre redes sociales ni datos trillados. Maximo 2 oraciones."

    prompt = variety.build_fact_prompt(topic=topic)
    variety.tick()

    settings = context.session.userdata.get("settings")
    max_tokens = min(96, max(60, getattr(settings, "llm_max_input_tokens", 76)))
    return _truncate_fact_prompt(prompt, max_tokens)
