"""Tools de juegos interactivos para Nebu.

Usa el VarietyEngine v3 (etnocacerista) para:
- Trivia: rota entre categorías con personalidad Nebu (mood + rapport)
- Adivinanzas: registra las contadas, genera con mood apropiado
- Cuentos: rota entre temas con personalidad y time-awareness
- Resetea combo de facts cuando se entra a un juego

Usa session.userdata["base_instructions"] como prompt base para:
- Siempre partir del prompt original (default o personalizado)
- Nunca appendar infinitamente al prompt actual
- Restaurar correctamente al terminar un juego
"""
from livekit.agents import RunContext, function_tool

TRIVIA_INSTRUCTIONS = """
MODO JUEGO: TRIVIA
Estas jugando trivia con el usuario. Reglas:
1. Haz una pregunta de conocimiento general apropiada para ninos
2. Espera la respuesta del usuario
3. Di si es correcta o incorrecta, y explica brevemente
4. Lleva la cuenta del puntaje (correctas/total)
5. Despues de cada respuesta, pregunta si quiere otra pregunta o parar
6. Adapta la dificultad segun las respuestas
7. Celebra los aciertos con entusiasmo y anima en los errores
Manten tu personalidad durante todo el juego.
"""

RIDDLE_INSTRUCTIONS = """
MODO JUEGO: ADIVINANZAS
Estas jugando adivinanzas con el usuario. Reglas:
1. Cuenta una adivinanza apropiada para ninos
2. Espera la respuesta del usuario
3. Si no adivina, da una pista
4. Maximo 3 pistas antes de revelar la respuesta
5. Celebra cuando adivine correctamente
6. Pregunta si quiere otra adivinanza o parar
Manten tu personalidad durante todo el juego.
"""

STORY_INSTRUCTIONS = """
MODO JUEGO: CUENTO INTERACTIVO
Estas creando un cuento interactivo con el usuario. Reglas:
1. Comienza una historia corta y emocionante
2. En momentos clave, ofrece 2-3 opciones al usuario para decidir que pasa
3. Continua la historia segun la eleccion del usuario
4. Incluye elementos educativos sutilmente
5. La historia debe tener un inicio, desarrollo y final
6. Manten los segmentos cortos (2-3 oraciones por turno)
7. Pregunta si quiere otra historia al terminar
Manten tu personalidad durante todo el juego.
"""


def _get_base_instructions(context: RunContext) -> str:
    """Obtiene el prompt base original (personalizado o default)."""
    return context.session.userdata.get("base_instructions", "")


def _get_variety(context: RunContext):
    """Obtiene el VarietyEngine de la sesión, o None."""
    return context.session.userdata.get("variety")


@function_tool(
    name="start_trivia",
    description="Start a trivia game. Use when the user wants to play trivia or answer questions.",
)
async def start_trivia(context: RunContext) -> str:
    """Start a trivia game with the user."""
    base = _get_base_instructions(context)

    variety = _get_variety(context)
    personality_block = ""
    category_hint = ""
    if variety:
        variety.reset_combo()
        cat = variety.pick_trivia_category()
        category_hint = f"\nCATEGORIA PARA LA PRIMERA PREGUNTA: {cat}"
        personality_block = (
            f"\n\n{variety.get_mood_instruction()}"
            f"\n{variety.get_rapport_instruction()}"
        )
        variety.tick()

    await context.session.current_agent.update_instructions(
        base + personality_block + "\n\n" + TRIVIA_INSTRUCTIONS + category_hint
    )
    return f"Trivia iniciada. Haz la primera pregunta al usuario.{category_hint}"


@function_tool(
    name="start_riddles",
    description="Start a riddle game. Use when the user wants to play riddles or adivinanzas.",
)
async def start_riddles(context: RunContext) -> str:
    """Start a riddle/adivinanza game with the user."""
    base = _get_base_instructions(context)

    variety = _get_variety(context)
    riddle_context = ""
    personality_block = ""
    if variety:
        variety.reset_combo()
        riddle_prompt = variety.build_riddle_prompt()
        riddle_context = f"\n\n{riddle_prompt}"
        personality_block = (
            f"\n\n{variety.get_mood_instruction()}"
            f"\n{variety.get_rapport_instruction()}"
        )
        variety.tick()

    await context.session.current_agent.update_instructions(
        base + personality_block + "\n\n" + RIDDLE_INSTRUCTIONS + riddle_context
    )
    return "Adivinanzas iniciadas. Cuenta la primera adivinanza al usuario."


@function_tool(
    name="start_story",
    description="Start an interactive story. Use when the user wants a story or cuento.",
)
async def start_story(context: RunContext) -> str:
    """Start an interactive storytelling session."""
    base = _get_base_instructions(context)

    variety = _get_variety(context)
    theme_hint = ""
    personality_block = ""
    if variety:
        variety.reset_combo()
        theme = variety.pick_story_theme()
        theme_hint = f"\nTEMA SUGERIDO: {theme}"
        personality_block = (
            f"\n\n{variety.get_mood_instruction()}"
            f"\n{variety.get_rapport_instruction()}"
            f"\n{variety.get_time_flavor()}"
        )
        variety.tick()

    await context.session.current_agent.update_instructions(
        base + personality_block + "\n\n" + STORY_INSTRUCTIONS + theme_hint
    )
    return f"Cuento interactivo iniciado. Comienza una historia emocionante.{theme_hint}"


@function_tool(
    name="end_game",
    description="End the current game and return to normal conversation. Use when the user wants to stop playing.",
)
async def end_game(context: RunContext) -> str:
    """End the current game mode and return to normal mode."""
    base = _get_base_instructions(context)

    variety = _get_variety(context)
    if variety:
        variety.reset_combo()

    await context.session.current_agent.update_instructions(base)
    return "Juego terminado. Vuelve a tu modo normal y pregunta que quiere hacer ahora."
