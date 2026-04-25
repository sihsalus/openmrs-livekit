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

from src.prompt_budget import truncate_to_tokens


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
    max_tokens = min(48, max(24, getattr(settings, "llm_max_input_tokens", 76) // 2))
    return truncate_to_tokens(prompt, max_tokens)
