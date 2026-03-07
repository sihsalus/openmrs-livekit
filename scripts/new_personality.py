#!/usr/bin/env python3
"""
Scaffold a new Nebu personality from templates.

Usage:
    python scripts/new_personality.py

Creates:
    src/personalities/<id>.yaml — Personality profile (from TEMPLATE.yaml)
    src/knowledge/<id>.yaml     — Knowledge module (from TEMPLATE.yaml)
    (No __init__.py update needed — auto-discovery via YAML glob)
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PERSONALITIES_DIR = ROOT / "src" / "personalities"
KNOWLEDGE_DIR = ROOT / "src" / "knowledge"
PERSONALITY_TEMPLATE = PERSONALITIES_DIR / "TEMPLATE.yaml"
KNOWLEDGE_TEMPLATE = KNOWLEDGE_DIR / "TEMPLATE.yaml"


def ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    answer = input(f"  {prompt}{hint}: ").strip()
    return answer or default


def validate_id(personality_id: str) -> str | None:
    if not re.match(r"^[a-z][a-z0-9_]*$", personality_id):
        return "Debe ser snake_case (ej: 'japanese', 'space_explorer')"
    if (PERSONALITIES_DIR / f"{personality_id}.yaml").exists():
        return f"Ya existe src/personalities/{personality_id}.yaml"
    return None


def scaffold_knowledge(personality_id: str, culture_name: str) -> str:
    """Read knowledge TEMPLATE.yaml and apply replacements."""
    content = KNOWLEDGE_TEMPLATE.read_text()
    content = content.replace("[TU_MODULO]", personality_id)
    content = content.replace("[TU CULTURA]", culture_name)
    return content


def scaffold_personality(personality_id: str, replacements: dict[str, str]) -> str:
    """Read personality TEMPLATE.yaml and apply replacements."""
    content = PERSONALITY_TEMPLATE.read_text()

    culture = replacements["culture_name"]
    special_category = replacements.get("special_category", personality_id)

    content = content.replace("tu_personalidad", personality_id)
    content = content.replace("TU_MODULO", personality_id)
    content = content.replace("TU_CATEGORIA_ESPECIAL", special_category)
    content = content.replace("[TU CULTURA]", culture)
    content = content.replace("[TU_CULTURA]", culture)
    content = content.replace("[Tu Cultura]", culture)
    content = content.replace("[Nombre]", culture)
    content = content.replace("[Tu Personalidad]", culture)
    content = content.replace(
        '"Una línea que describe esta personalidad"',
        f'"{replacements["description"]}"',
    )
    content = content.replace(
        f'"Nebu {culture}"',
        f'"{replacements["display_name"]}"',
    )

    return content


def main():
    print("\n🧸 Nuevo perfil de personalidad para Nebu\n")

    while True:
        personality_id = ask("ID (snake_case)", "")
        if not personality_id:
            print("  ✗ El ID es obligatorio")
            continue
        error = validate_id(personality_id)
        if error:
            print(f"  ✗ {error}")
            continue
        break

    culture_name = ask("Nombre de la cultura/tema", personality_id.replace("_", " ").title())
    display_name = ask("Display name", f"Nebu {culture_name}")
    description = ask("Descripción (1 línea)", f"Nebu con personalidad {culture_name.lower()}")
    special_category = ask("ID de categoría especial", personality_id)

    replacements = {
        "culture_name": culture_name,
        "display_name": display_name,
        "description": description,
        "special_category": special_category,
    }

    personality_path = PERSONALITIES_DIR / f"{personality_id}.yaml"
    knowledge_path = KNOWLEDGE_DIR / f"{personality_id}.yaml"

    print(f"\n📁 Se van a crear:")
    print(f"   {personality_path.relative_to(ROOT)}")
    print(f"   {knowledge_path.relative_to(ROOT)}")
    print(f"   (auto-discovery, no se necesita editar __init__.py)\n")

    confirm = ask("¿Continuar? (y/n)", "y")
    if confirm.lower() not in ("y", "yes", "sí", "si", "s"):
        print("  Cancelado.")
        sys.exit(0)

    personality_content = scaffold_personality(personality_id, replacements)
    personality_path.write_text(personality_content)
    print(f"  ✓ {personality_path.relative_to(ROOT)}")

    knowledge_content = scaffold_knowledge(personality_id, culture_name)
    knowledge_path.write_text(knowledge_content)
    print(f"  ✓ {knowledge_path.relative_to(ROOT)}")

    print(f"\n🎉 ¡Listo! Ahora rellena el contenido cultural:")
    print(f"   1. {personality_path.relative_to(ROOT)} — moods, catchphrases, categorías, etc.")
    print(f"   2. {knowledge_path.relative_to(ROOT)} — datos reales con fuentes académicas\n")


if __name__ == "__main__":
    main()
