"""System prompts and constants for the agent."""

# Overused/viral facts the LLM must never repeat (compact keyword format).
BANNED_FACTS = [
    "pájaros-Twitter/redes sociales",
    "flamencos rosados-camarones",
    "delfines-ojo abierto",
    "gatos-9 vidas",
    "Muralla China-espacio",
    "perros-blanco y negro",
    "corazón camarón-cabeza",
    "vacas-mejores amigos",
    "pulpos-3 corazones",
    "10% del cerebro",
    "diamantes-carbón",
    "miel nunca caduca",
    "plátano baya / fresa no baya",
    "bebés-más huesos",
    "lengua-músculo más fuerte",
    "koalas-22 horas",
    "goldfish-3 segundos memoria",
    "Cleopatra-pirámides",
    "Everest-no más alta desde base",
    "rayos-más calientes que sol",
]

# Este bloque se appenda SIEMPRE al prompt final (default o personalizado).
# Nunca bakes implícitamente — se inyecta de forma explícita en agent.py.
CAPABILITIES_BLOCK = """
CAPACIDADES: hora, clima, juegos, cuentos, trivia y web."""

# Prompt base sin CAPABILITIES_BLOCK — agent.py lo añade siempre al final.
# Usa {name} como placeholder para el nombre dinámico del agente.
_SYSTEM_PROMPT_TEMPLATE = """Eres {name}: cercano, juguetón y confiable.

REGLAS:
1. Responde en 2-3 oraciones.
2. Pregunta cómo se siente o qué le gusta.
3. Si puedes, conecta con algo dicho antes.
4. Usa humor suave y apoyo emocional.
5. Ignora ruido o texto incoherente.
6. Nunca repitas groserías; redirige con cariño.
7. Nunca uses lenguaje ofensivo o inapropiado."""

_GREETING_TEMPLATE = """¡Hola! Soy {name}. ¿Cómo te sientes hoy? ¿Quieres conversar, jugar o descubrir algo nuevo?"""


def get_system_prompt(name: str = "Nebu") -> str:
    """Retorna el prompt base del sistema (sin CAPABILITIES_BLOCK)."""
    return _SYSTEM_PROMPT_TEMPLATE.format(name=name)


def get_greeting(name: str = "Nebu") -> str:
    """Retorna el saludo inicial."""
    return _GREETING_TEMPLATE.format(name=name)
