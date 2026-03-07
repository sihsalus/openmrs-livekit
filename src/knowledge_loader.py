"""
knowledge_loader — Load knowledge modules from YAML.

Each YAML defines cultural knowledge data (sections of dicts) plus
metadata for the builder function (format strings, vocabulary config).

Usage:
    from src.knowledge_loader import build_knowledge_injection

    text = build_knowledge_injection("andean")  # returns formatted str
"""

import random
from pathlib import Path
from typing import Any

import yaml

_KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
_cache: dict[str, dict] = {}


def _load_knowledge(module_name: str) -> dict:
    """Load and cache a knowledge YAML file."""
    if module_name not in _cache:
        yaml_path = _KNOWLEDGE_DIR / f"{module_name}.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError(f"No knowledge YAML found: {yaml_path}")
        with open(yaml_path) as f:
            _cache[module_name] = yaml.safe_load(f)
    return _cache[module_name]


def build_knowledge_injection(module_name: str) -> str:
    """
    Build a knowledge injection string from YAML data.

    Picks a random section, formats one random item, optionally
    appends a vocabulary word. Mirrors the old per-module
    build_*_knowledge_injection() functions exactly.
    """
    data = _load_knowledge(module_name)
    meta = data["meta"]
    sections = meta["sections"]
    blocks: list[str] = []

    # 1. Pick random section
    section_id = random.choice(list(sections.keys()))
    section_meta = sections[section_id]
    # data_key allows a section to read from a different data list (e.g. vocabulario_concepto → vocabulario)
    data_key = section_meta.get("data_key", section_id)
    items = data[data_key]

    # 2. Format random item from that section
    item = random.choice(items)
    template = section_meta["format"]
    blocks.append(template.format(**item))

    # 3. Vocabulary bonus
    vocab_key = meta.get("vocab_key")
    if vocab_key and vocab_key in data:
        chance = meta.get("vocab_chance", 0.4)
        if random.random() < chance:
            word = random.choice(data[vocab_key])
            vocab_format = meta["vocab_format"]
            blocks.append(vocab_format.format(**word))

    return "\n".join(blocks)
