"""
Tool Dispatcher Architecture — Documentation

OpenMRS LiveKit now includes an intelligent tool routing system that dispatches
user queries to the most appropriate tool based on intent classification.
"""

# Tool Dispatcher Guide

## Overview

The tool dispatcher provides intelligent routing of user queries to the best available tool.
Instead of relying solely on the LLM to choose which tools to call, the dispatcher:

1. **Classifies intent** — analyzes the user query for keywords and intent patterns
2. **Ranks applicable tools** — matches query keywords to tool categories and metadata
3. **Routes intelligently** — calls the highest-confidence tool first
4. **Handles fallbacks** — automatically tries alternative tools if the primary fails
5. **Logs decisions** — provides visibility into routing choices for debugging

## Architecture

```
User Query
    |
    v
IntentClassifier (analyzes keywords + categories)
    |
    v
ToolIntent (primary_tool, confidence, fallback_tools)
    |
    v
ToolDispatcher (routes → primary | fallback chain)
    |
    v
Tool Callable (execution)
```

## Components

### 1. ToolMetadata (src/tools/dispatcher.py)

Each tool declares its capabilities:

```python
ToolMetadata(
    name="search_patient",                          # Tool identifier
    categories=["clinical", "openmrs", "search"],  # What it's for
    keywords=["patient", "find", "name"],          # What activates it
    priority=8,                                     # 0-10, higher = preferred
    requires_context=["patient_uuid"],             # Required to work
    description="Search for a patient in OpenMRS",
    fallback_tools=[],                             # If this fails, try...
)
```

### 2. ToolRegistry (src/tools/dispatcher.py)

Central mapping of tools to metadata and callables:

```python
registry = ToolRegistry()

# Register a tool
registry.register(metadata, callable_fn)

# Query registry
registry.get_metadata("search_patient")
registry.list_by_category("clinical")
```

### 3. IntentClassifier (src/tools/dispatcher.py)

Analyzes queries and classifies intent:

```python
classifier = IntentClassifier(registry)

intent = await classifier.classify("Find patient named Juan")
# Returns:
# ToolIntent(
#     primary_tool="search_patient",
#     confidence=0.85,
#     category="clinical",
#     fallback_tools=[],
#     reasoning="keyword 'patient'; keyword 'find'"
# )
```

**Scoring Algorithm:**
- Whole-word keyword match: +0.30 confidence
- Partial keyword match: +0.15 confidence
- Multiple keywords: +0.10 per additional keyword
- Result clamped to [0.0, 1.0]

### 4. ToolDispatcher (src/tools/dispatcher.py)

Routes queries to tools with fallback:

```python
dispatcher = ToolDispatcher(registry, classifier)

result = await dispatcher.dispatch(
    query="Patient has fever",
    available_categories=["clinical"]  # Optional filter
)
```

**Execution Flow:**
1. Classify intent from query
2. Call primary tool
3. If fails → try each fallback tool in order
4. If all fail → raise error with full context

## Usage

### Initialization (Early in Agent Lifecycle)

```python
# In agent.py or your entrypoint
from src.tools import init_dispatcher
from src.config import Settings

settings = Settings()
init_dispatcher(settings)  # Sets up registry
```

### Getting Tools for Agent

```python
from src.tools import get_tools

tools = get_tools(settings)  # Returns registered tools
# Agent now uses dispatcher automatically
```

### Accessing the Dispatcher

```python
from src.tools import get_dispatcher, get_registry

dispatcher = get_dispatcher()
registry = get_registry()

# Check what tools are available
summary = dispatcher.get_registry_summary()
# {'clinical': ['search_patient', 'record_clinical_fact'],
#  'informational': ['get_weather', 'get_current_datetime']}
```

## Current Tool Registry

### Clinical Tools (Priority 7-9)

| Tool | Keywords | Priority | Fallbacks |
|------|----------|----------|-----------|
| `record_clinical_fact` | symptom, vital, diagnosis, medication, allergy | 9 | — |
| `search_patient` | patient, find, name | 8 | — |
| `show_encounter_draft` | encounter, draft, review, summary | 7 | — |

### Informational Tools (Priority 1-2)

| Tool | Keywords | Priority | Fallbacks |
|------|----------|----------|-----------|
| `web_search` | search, find, look, how, what, where | 2 | — |
| `get_weather` | weather, rain, sunny, temperature | 1 | web_search |
| `get_current_datetime` | time, date, hour, today | 1 | — |
| `get_fun_fact` | fact, trivia, interesting | 1 | — |

## Testing

Run the dispatcher tests:

```bash
pytest tests/test_tool_dispatcher.py -v
```

Example classification:

```bash
python -c "from tests.test_tool_dispatcher import example_intent_classification; import asyncio; asyncio.run(example_intent_classification())"
```

## Adding a New Tool

1. **Create the tool function** (e.g., `src/tools/my_tool.py`)

2. **Register it** in `src/tools/setup.py`:

```python
def setup_tool_registry(settings: Settings) -> None:
    from src.tools.my_tool import my_tool
    
    registry.register(
        ToolMetadata(
            name="my_tool",
            categories=["category"],
            keywords=["keyword1", "keyword2"],
            priority=3,
            description="What this tool does",
            fallback_tools=["other_tool"],  # Optional
        ),
        my_tool,
    )
```

3. **Add tests** in `tests/test_tool_dispatcher.py`

## Logging & Debugging

The dispatcher logs routing decisions with context:

```python
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
```

Check logs during development:
```bash
export LIVEKIT_AGENT_LOG_LEVEL=debug
python -m src.agent  # See routing decisions
```

## Future Enhancements

1. **ML-based classification** — Replace keyword matching with learned intent classifier
2. **Context-aware routing** — Consider session history, patient context, conversation flow
3. **Tool performance metrics** — Track success rates, latency, and adjust priority dynamically
4. **A/B testing** — Route subsets of queries to different tools and measure outcomes
5. **Cost-aware routing** — Prefer cheaper tools (local) over expensive ones (cloud APIs)
6. **Skill-based dispatch** — Route based on required skills (clinical vs. entertainment)

## Example Query Flows

### Clinical Flow
```
User: "El paciente tiene fiebre"
    ↓ classify
Intent: clinical, record_clinical_fact (0.85 confidence)
    ↓ dispatch
Tool: record_clinical_fact("symptom", "fever", ...)
    ↓ result
"Hecho clínico registrado: symptom = fever"
```

### Search Flow
```
User: "¿Dónde puedo encontrar información sobre malaria?"
    ↓ classify  
Intent: informational, web_search (0.70 confidence)
    ↓ dispatch
Tool: web_search("información sobre malaria")
    ↓ result
"Resultados de búsqueda: [...]"
```

### Fallback Flow
```
User: "Busca más información"
    ↓ classify
Intent: search, primary=web_search (0.50 conf) → fallback=get_weather
    ↓ dispatch (web_search fails)
Tool: web_search() → ERROR
    ↓ fallback
Tool: get_weather()
    ↓ result
"Información del clima..."
```
