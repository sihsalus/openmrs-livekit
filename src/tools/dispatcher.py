"""
Tool Dispatcher/Router for intelligent tool selection and invocation.

Provides:
- ToolMetadata: intent categories, keywords, priority for each tool
- IntentClassifier: analyzes queries to rank applicable tools
- ToolDispatcher: routes calls to appropriate tools with fallback
- Registry: central mapping of tool names to metadata and handlers
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from src.logger import get_logger

logger = get_logger("nebu.tools.dispatcher")


@dataclass
class ToolMetadata:
    """Metadata for a tool to enable intelligent routing."""

    name: str
    categories: list[str]  # e.g., ["clinical", "search", "openmrs"]
    keywords: list[str]  # e.g., ["patient", "vital", "symptom"]
    priority: int = 1  # Higher = tried first (0-10)
    requires_context: list[str] = field(default_factory=list)  # e.g., ["patient_uuid"]
    description: str = ""
    fallback_tools: list[str] = field(default_factory=list)  # Tools to try if this fails


@dataclass
class ToolIntent:
    """Result of intent classification."""

    primary_tool: str
    confidence: float  # 0.0-1.0
    category: str
    fallback_tools: list[str]
    reasoning: str


class ToolRegistry:
    """Central registry mapping tool names to metadata and callables."""

    def __init__(self):
        self._metadata: dict[str, ToolMetadata] = {}
        self._callables: dict[str, Callable] = {}

    def register(self, metadata: ToolMetadata, callable_fn: Callable) -> None:
        """Register a tool with its metadata."""
        if metadata.name in self._metadata:
            logger.warning(f"Overriding tool {metadata.name}")
        self._metadata[metadata.name] = metadata
        self._callables[metadata.name] = callable_fn
        logger.debug(
            f"Registered tool {metadata.name}",
            extra={"categories": metadata.categories, "keywords": metadata.keywords},
        )

    def get_metadata(self, tool_name: str) -> ToolMetadata | None:
        """Get metadata for a tool."""
        return self._metadata.get(tool_name)

    def get_callable(self, tool_name: str) -> Callable | None:
        """Get callable for a tool."""
        return self._callables.get(tool_name)

    def list_by_category(self, category: str) -> list[ToolMetadata]:
        """Get all tools in a category, sorted by priority."""
        tools = [m for m in self._metadata.values() if category in m.categories]
        return sorted(tools, key=lambda m: -m.priority)

    def list_all(self) -> list[ToolMetadata]:
        """Get all registered tool metadata."""
        return list(self._metadata.values())


class IntentClassifier:
    """Analyzes user queries to classify intent and suggest tools."""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    async def classify(self, query: str, available_categories: list[str] | None = None) -> ToolIntent:
        """
        Classify user intent from query and suggest best tool.

        Args:
            query: User utterance
            available_categories: If provided, only consider tools in these categories

        Returns:
            ToolIntent with primary tool, confidence, and fallbacks
        """
        query_lower = query.lower()

        # Score each tool based on keyword matching
        scores: dict[str, tuple[float, str, list[str]]] = {}
        for tool_name, metadata in self.registry._metadata.items():
            # Skip if category filter provided
            if available_categories:
                if not any(c in available_categories for c in metadata.categories):
                    continue

            confidence = 0.0
            matched_keywords = []
            reasoning_parts = []

            # Keyword matching
            for keyword in metadata.keywords:
                # Whole-word match using word boundaries
                if re.search(rf"\b{re.escape(keyword)}\b", query_lower):
                    confidence += 0.3
                    matched_keywords.append(keyword)
                    reasoning_parts.append(f"keyword '{keyword}'")
                # Partial match (lower score)
                elif keyword in query_lower:
                    confidence += 0.15
                    reasoning_parts.append(f"partial '{keyword}'")

            # Category boost if multiple keywords or high confidence
            if matched_keywords:
                confidence = min(1.0, confidence + (0.1 * len(matched_keywords)))

            if confidence > 0.0:
                reasoning = "; ".join(reasoning_parts) if reasoning_parts else "keyword match"
                scores[tool_name] = (confidence, reasoning, metadata.fallback_tools)

        # Find best match
        if not scores:
            # Fallback to first available tool
            all_tools = self.registry.list_all()
            if all_tools:
                best_tool = all_tools[0]
                return ToolIntent(
                    primary_tool=best_tool.name,
                    confidence=0.0,
                    category="unknown",
                    fallback_tools=[],
                    reasoning="no keywords matched, using default",
                )
            raise ValueError("No tools available")

        best_name = max(scores, key=lambda k: scores[k][0])
        confidence, reasoning, fallbacks = scores[best_name]
        metadata = self.registry.get_metadata(best_name)

        intent = ToolIntent(
            primary_tool=best_name,
            confidence=min(confidence, 1.0),
            category=metadata.categories[0] if metadata.categories else "unknown",
            fallback_tools=fallbacks,
            reasoning=reasoning,
        )

        logger.debug(
            f"Intent classified",
            extra={
                "query": query[:50],
                "primary": intent.primary_tool,
                "confidence": f"{intent.confidence:.2f}",
                "category": intent.category,
                "reasoning": reasoning,
            },
        )

        return intent


class ToolDispatcher:
    """
    Dispatches tool calls to the appropriate handler based on intent.

    Provides:
    - Intelligent routing (primary + fallback)
    - Error handling with fallback chain
    - Call logging and metrics
    """

    def __init__(self, registry: ToolRegistry, classifier: IntentClassifier):
        self.registry = registry
        self.classifier = classifier

    async def dispatch(
        self, query: str, *args, available_categories: list[str] | None = None, **kwargs
    ) -> Any:
        """
        Dispatch a query to the best available tool.

        Tries primary tool first, then fallbacks if it fails.

        Args:
            query: User utterance
            *args, **kwargs: Arguments to pass to tool callable
            available_categories: Filter which tool categories to consider

        Returns:
            Result from tool callable
        """
        intent = await self.classifier.classify(query, available_categories=available_categories)

        # Try primary tool
        logger.info(
            f"Dispatching to {intent.primary_tool}",
            extra={"confidence": f"{intent.confidence:.2f}", "reasoning": intent.reasoning},
        )
        try:
            callable_fn = self.registry.get_callable(intent.primary_tool)
            if callable_fn is None:
                raise RuntimeError(f"No callable registered for {intent.primary_tool}")
            return await callable_fn(query, *args, **kwargs)
        except Exception as e:
            logger.warning(
                f"Primary tool {intent.primary_tool} failed: {str(e)}",
                extra={"error": str(e)},
            )

            # Try fallback tools
            for fallback_name in intent.fallback_tools:
                logger.info(f"Trying fallback: {fallback_name}")
                try:
                    callable_fn = self.registry.get_callable(fallback_name)
                    if callable_fn is None:
                        continue
                    return await callable_fn(query, *args, **kwargs)
                except Exception as e2:
                    logger.debug(f"Fallback {fallback_name} also failed: {str(e2)}")
                    continue

            # All tools failed
            logger.error(
                f"All tools failed (primary + {len(intent.fallback_tools)} fallbacks)",
                extra={"primary": intent.primary_tool, "error": str(e)},
            )
            raise

    def register_tool(self, metadata: ToolMetadata, callable_fn: Callable) -> None:
        """Register a tool with the dispatcher."""
        self.registry.register(metadata, callable_fn)

    def get_registry_summary(self) -> dict[str, list[str]]:
        """Get summary of registered tools by category."""
        summary: dict[str, list[str]] = {}
        for metadata in self.registry.list_all():
            for category in metadata.categories:
                if category not in summary:
                    summary[category] = []
                summary[category].append(metadata.name)
        return summary


# Global dispatcher instance (initialized on first use)
_dispatcher: ToolDispatcher | None = None
_registry: ToolRegistry | None = None
_classifier: IntentClassifier | None = None


def get_dispatcher() -> ToolDispatcher:
    """Get or create the global tool dispatcher."""
    global _dispatcher, _registry, _classifier
    if _dispatcher is None:
        _registry = ToolRegistry()
        _classifier = IntentClassifier(_registry)
        _dispatcher = ToolDispatcher(_registry, _classifier)
    return _dispatcher


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    global _registry
    if _registry is None:
        get_dispatcher()  # Initializes registry
    return _registry
