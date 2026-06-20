"""Helpers para presupuestar texto que termina dentro del contexto del LLM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CHARS_PER_TOKEN = 4
TRUNCATION_MARKER = "\n[truncado]"


@dataclass(slots=True)
class BudgetSection:
    """Sección de texto con prioridad y límites para componer un prompt acotado."""

    name: str
    text: str
    required: bool = False
    max_tokens: int | None = None
    min_tokens: int = 0
    trim_priority: int = 100


def tokens_to_chars(tokens: int) -> int:
    return max(0, tokens) * CHARS_PER_TOKEN


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN


def truncate_text(text: str, max_chars: int) -> str:
    """Recorta preservando el inicio, donde suelen vivir reglas críticas."""
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    if max_chars <= len(TRUNCATION_MARKER):
        return text[:max_chars]
    return text[: max_chars - len(TRUNCATION_MARKER)].rstrip() + TRUNCATION_MARKER


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    return truncate_text(text, tokens_to_chars(max_tokens))


def compose_budgeted_text(
    sections: list[BudgetSection],
    total_tokens: int,
) -> tuple[str, dict[str, Any]]:
    """Compone secciones dentro de un presupuesto global con degradación por prioridad."""
    budget_chars = tokens_to_chars(total_tokens)
    prepared: list[dict[str, Any]] = []
    meta: dict[str, Any] = {
        "budget_tokens": total_tokens,
        "truncated_sections": [],
        "dropped_sections": [],
        "hard_truncated": False,
    }

    for section in sections:
        if not section.text:
            continue
        piece = section.text
        if section.max_tokens is not None:
            limited = truncate_to_tokens(piece, section.max_tokens)
            if limited != piece:
                meta["truncated_sections"].append(section.name)
            piece = limited
        prepared.append(
            {
                "name": section.name,
                "piece": piece,
                "required": section.required,
                "min_chars": tokens_to_chars(section.min_tokens),
                "trim_priority": section.trim_priority,
            }
        )

    def render() -> str:
        return "".join(item["piece"] for item in prepared)

    current = render()
    if len(current) <= budget_chars:
        return current, meta

    for item in sorted(prepared, key=lambda value: value["trim_priority"], reverse=True):
        if len(current) <= budget_chars:
            break
        min_chars = min(item["min_chars"], len(item["piece"])) if item["required"] else 0
        reducible = len(item["piece"]) - min_chars
        if reducible <= 0:
            continue
        shrink_by = min(reducible, len(current) - budget_chars)
        new_len = len(item["piece"]) - shrink_by
        before = item["piece"]
        item["piece"] = truncate_text(item["piece"], new_len)
        if item["piece"] != before and item["name"] not in meta["truncated_sections"]:
            meta["truncated_sections"].append(item["name"])
        if not item["piece"]:
            meta["dropped_sections"].append(item["name"])
        current = render()

    if len(current) > budget_chars:
        current = truncate_text(current, budget_chars)
        meta["hard_truncated"] = True

    return current, meta
