"""
Example usage and tests for the tool dispatcher.

Run with:
    python -m pytest tests/test_tool_dispatcher.py -v
"""

import pytest

from src.config import Settings
from src.tools.dispatcher import IntentClassifier, ToolIntent, ToolRegistry, get_dispatcher
from src.tools.setup import setup_tool_registry


@pytest.fixture
def registry():
    """Create a fresh registry for testing."""
    return ToolRegistry()


@pytest.fixture
def settings():
    """Create test settings with clinical tools enabled."""
    settings = Settings()
    settings.enable_openmrs_tools = True
    settings.web_search_provider = None  # Disable web search
    return settings


class TestIntentClassifier:
    """Test intent classification logic."""

    @pytest.mark.asyncio
    async def test_clinical_intent_detection(self, settings):
        """Test that clinical queries route to clinical tools."""
        setup_tool_registry(settings)
        classifier = IntentClassifier(get_dispatcher().registry)

        intent = await classifier.classify("The patient has a headache and fever")

        assert intent.category == "clinical"
        assert intent.primary_tool in ["record_clinical_fact", "search_patient"]
        assert intent.confidence > 0.5

    @pytest.mark.asyncio
    async def test_patient_search_intent(self, settings):
        """Test that patient searches are routed correctly."""
        setup_tool_registry(settings)
        classifier = IntentClassifier(get_dispatcher().registry)

        intent = await classifier.classify("Find patient named Juan")

        assert intent.primary_tool == "search_patient"
        assert intent.confidence > 0.6

    @pytest.mark.asyncio
    async def test_symptom_recording_intent(self, settings):
        """Test that symptom recording is recognized."""
        setup_tool_registry(settings)
        classifier = IntentClassifier(get_dispatcher().registry)

        intent = await classifier.classify("Record that patient has cough")

        assert intent.primary_tool == "record_clinical_fact"
        assert intent.category == "clinical"

    @pytest.mark.asyncio
    async def test_weather_intent(self, settings):
        """Test that weather queries are classified correctly."""
        setup_tool_registry(settings)
        classifier = IntentClassifier(get_dispatcher().registry)

        intent = await classifier.classify("What's the weather today?")

        assert intent.primary_tool == "get_weather"
        assert intent.category == "informational"

    @pytest.mark.asyncio
    async def test_time_intent(self, settings):
        """Test that time/date queries are recognized."""
        setup_tool_registry(settings)
        classifier = IntentClassifier(get_dispatcher().registry)

        intent = await classifier.classify("What time is it?")

        assert intent.primary_tool == "get_current_datetime"

    @pytest.mark.asyncio
    async def test_fallback_chain(self, settings):
        """Test that fallback tools are configured."""
        setup_tool_registry(settings)
        classifier = IntentClassifier(get_dispatcher().registry)

        intent = await classifier.classify("Search for information")

        # Should have fallback options configured
        assert isinstance(intent.fallback_tools, list)


class TestToolRegistry:
    """Test tool registry operations."""

    def test_register_and_retrieve(self, registry):
        """Test basic registration."""
        from src.tools.dispatcher import ToolMetadata

        async def dummy_tool(query):
            return "result"

        metadata = ToolMetadata(
            name="test_tool",
            categories=["test"],
            keywords=["test", "example"],
        )
        registry.register(metadata, dummy_tool)

        assert registry.get_metadata("test_tool") is not None
        assert registry.get_callable("test_tool") is not None

    def test_list_by_category(self, registry):
        """Test filtering tools by category."""
        from src.tools.dispatcher import ToolMetadata

        async def tool1(q):
            return "1"

        async def tool2(q):
            return "2"

        registry.register(
            ToolMetadata(
                name="tool1",
                categories=["clinical", "search"],
                keywords=["patient"],
                priority=2,
            ),
            tool1,
        )
        registry.register(
            ToolMetadata(
                name="tool2",
                categories=["clinical"],
                keywords=["vital"],
                priority=3,
            ),
            tool2,
        )

        clinical_tools = registry.list_by_category("clinical")
        assert len(clinical_tools) == 2
        # Should be sorted by priority (descending)
        assert clinical_tools[0].priority >= clinical_tools[1].priority


class TestDispatcherIntegration:
    """Integration tests for the full dispatcher."""

    @pytest.mark.asyncio
    async def test_dispatcher_initialization(self, settings):
        """Test that dispatcher initializes correctly."""
        dispatcher = get_dispatcher()
        setup_tool_registry(settings)

        summary = dispatcher.get_registry_summary()
        assert "clinical" in summary
        assert "informational" in summary or "utility" in summary


# ─────────────────────────────────────────────────────────────────────────────
# Example usage (can be run interactively)
# ─────────────────────────────────────────────────────────────────────────────


async def example_intent_classification():
    """Example: classify user queries and see routing."""
    from src.tools.setup import setup_tool_registry

    settings = Settings()
    settings.enable_openmrs_tools = True
    settings.web_search_provider = None

    setup_tool_registry(settings)
    classifier = IntentClassifier(get_dispatcher().registry)

    # Clinical queries
    queries = [
        "The patient has a fever and cough",
        "Find patient named Carlos",
        "What's the weather?",
        "Tell me a fun fact",
        "What time is it?",
    ]

    print("\n📊 Intent Classification Examples:")
    print("─" * 70)

    for query in queries:
        intent = await classifier.classify(query)
        print(f"\nQuery: {query!r}")
        print(f"  → Tool: {intent.primary_tool}")
        print(f"  → Category: {intent.category}")
        print(f"  → Confidence: {intent.confidence:.0%}")
        print(f"  → Reasoning: {intent.reasoning}")
        if intent.fallback_tools:
            print(f"  → Fallbacks: {', '.join(intent.fallback_tools)}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_intent_classification())
