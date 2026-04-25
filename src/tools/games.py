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

from src.prompt_budget import BudgetSection, compose_budgeted_text

TRIVIA_INSTRUCTIONS = (
    "\n\nMODO JUEGO: TRIVIA\n"
    "Haz 1 pregunta para ninos, espera respuesta, corrige breve, lleva puntaje, "
    "ajusta dificultad y pregunta si quiere seguir."
)

RIDDLE_INSTRUCTIONS = (
    "\n\nMODO JUEGO: ADIVINANZAS\n"
    "Cuenta 1 adivinanza, espera respuesta, da hasta 3 pistas, revela si hace falta "
    "y pregunta si quiere otra."
)

STORY_INSTRUCTIONS = (
    "\n\nMODO JUEGO: CUENTO INTERACTIVO\n"
    "Crea una historia corta por turnos, ofrece 2-3 opciones, sigue la eleccion "
    "del nino y cierra con mensaje positivo."
)


def _get_base_instructions(context: RunContext) -> str:
    """Obtiene el prompt base original (personalizado o default)."""
    return context.session.userdata.get("base_instructions", "")


def _get_variety(context: RunContext):
    """Obtiene el VarietyEngine de la sesión, o None."""
    return context.session.userdata.get("variety")


def _budget_update(
    context: RunContext,
    *,
    personality_block: str = "",
    mode_block: str = "",
    hint_block: str = "",
) -> str:
    settings = context.session.userdata.get("settings")
    total_tokens = getattr(settings, "llm_max_input_tokens", 76)
    base = _get_base_instructions(context)
    updated, _meta = compose_budgeted_text(
        [
            BudgetSection(
                name="base_instructions",
                text=base,
                required=True,
                max_tokens=max(24, total_tokens - 22),
                min_tokens=max(18, total_tokens // 2),
                trim_priority=20,
            ),
            BudgetSection(
                name="personality_block",
                text=personality_block,
                max_tokens=6,
                trim_priority=80,
            ),
            BudgetSection(
                name="mode_block",
                text=mode_block,
                required=True,
                max_tokens=18,
                min_tokens=10,
                trim_priority=30,
            ),
            BudgetSection(
                name="hint_block",
                text=hint_block,
                max_tokens=4,
                trim_priority=100,
            ),
        ],
        total_tokens=total_tokens,
    )
    return updated


@function_tool(
    name="start_trivia",
    description="Start a trivia game. Use when the user wants to play trivia or answer questions.",
)
async def start_trivia(context: RunContext) -> str:
    """Start a trivia game with the user."""
    variety = _get_variety(context)
    personality_block = ""
    category_hint = ""
    if variety:
        variety.reset_combo()
        cat = variety.pick_trivia_category()
        category_hint = f"\nCATEGORIA PARA LA PRIMERA PREGUNTA: {cat}"
        personality_block = (
            f"\n\n{variety.get_mood_instruction()}\n{variety.get_rapport_instruction()}"
        )
        variety.tick()

    await context.session.current_agent.update_instructions(
        _budget_update(
            context,
            personality_block=personality_block,
            mode_block=TRIVIA_INSTRUCTIONS,
            hint_block=category_hint,
        )
    )
    return f"Trivia iniciada. Haz la primera pregunta al usuario.{category_hint}"


@function_tool(
    name="start_riddles",
    description="Start a riddle game. Use when the user wants to play riddles or adivinanzas.",
)
async def start_riddles(context: RunContext) -> str:
    """Start a riddle/adivinanza game with the user."""
    variety = _get_variety(context)
    riddle_context = ""
    personality_block = ""
    if variety:
        variety.reset_combo()
        riddle_prompt = variety.build_riddle_prompt()
        riddle_context = f"\n\n{riddle_prompt}"
        personality_block = (
            f"\n\n{variety.get_mood_instruction()}\n{variety.get_rapport_instruction()}"
        )
        variety.tick()

    await context.session.current_agent.update_instructions(
        _budget_update(
            context,
            personality_block=personality_block,
            mode_block=RIDDLE_INSTRUCTIONS,
            hint_block=riddle_context,
        )
    )
    return "Adivinanzas iniciadas. Cuenta la primera adivinanza al usuario."


@function_tool(
    name="start_story",
    description="Start an interactive story. Use when the user wants a story or cuento.",
)
async def start_story(context: RunContext) -> str:
    """Start an interactive storytelling session."""
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
        _budget_update(
            context,
            personality_block=personality_block,
            mode_block=STORY_INSTRUCTIONS,
            hint_block=theme_hint,
        )
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
