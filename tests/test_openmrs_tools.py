"""Tests for OpenMRS FHIR tools and client."""

from src.clinical_facts import ClinicalEvidence, ClinicalFact, EncounterDraft
from src.config import Settings


class TestOpenMRSConfig:
    def test_openmrs_settings_defaults(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        s = Settings(
            livekit_url="ws://localhost:7880",
            livekit_api_key="k",
            livekit_api_secret="s",
            llm_provider="ollama",
            stt_provider="whisper",
            tts_provider="piper",
            enable_openmrs_tools=True,
        )
        assert s.enable_openmrs_tools is True
        assert s.openmrs_base_url == "http://localhost/openmrs"
        assert s.openmrs_username == "admin"
        assert s.openmrs_password == "Admin123"

    def test_openmrs_custom_url(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        s = Settings(
            livekit_url="ws://localhost:7880",
            livekit_api_key="k",
            livekit_api_secret="s",
            llm_provider="ollama",
            stt_provider="whisper",
            tts_provider="piper",
            openmrs_base_url="http://192.168.1.100:8080/openmrs",
        )
        assert s.openmrs_base_url == "http://192.168.1.100:8080/openmrs"

    def test_openmrs_disabled_by_default(self):
        s = Settings(
            livekit_url="ws://localhost:7880",
            livekit_api_key="k",
            livekit_api_secret="s",
            openai_api_key="sk-test",
        )
        assert s.enable_openmrs_tools is False


class TestToolRegistration:
    def test_tools_include_openmrs_when_enabled(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from src.tools import get_tools

        s = Settings(
            livekit_url="ws://localhost:7880",
            livekit_api_key="k",
            livekit_api_secret="s",
            llm_provider="ollama",
            stt_provider="whisper",
            tts_provider="piper",
            enable_openmrs_tools=True,
        )
        tools = get_tools(s)
        tool_names = [getattr(t, "name", getattr(t, "__name__", "")) for t in tools]
        assert "search_patient" in tool_names
        assert "record_clinical_fact" in tool_names
        assert "show_encounter_draft" in tool_names
        assert "submit_encounter" in tool_names

    def test_tools_exclude_openmrs_when_disabled(self):
        from src.tools import get_tools

        s = Settings(
            livekit_url="ws://localhost:7880",
            livekit_api_key="k",
            livekit_api_secret="s",
            openai_api_key="sk-test",
            enable_openmrs_tools=False,
        )
        tools = get_tools(s)
        tool_names = [getattr(t, "name", getattr(t, "__name__", "")) for t in tools]
        assert "search_patient" not in tool_names


class TestClinicalPrompts:
    def test_clinical_prompt_loaded(self):
        from src.prompts import get_system_prompt

        prompt = get_system_prompt()
        assert "asistente clínico" in prompt
        assert "record_clinical_fact" in prompt
        assert "search_patient" in prompt

    def test_clinical_greeting(self):
        from src.prompts import get_greeting

        greeting = get_greeting()
        assert "documentación clínica" in greeting

    def test_clinical_capabilities(self):
        from src.prompts import get_capabilities_block

        block = get_capabilities_block()
        assert "buscar pacientes" in block


class TestEncounterDraftWorkflow:
    def test_add_facts_and_review(self):
        draft = EncounterDraft(patient_uuid="test-uuid")
        fact1 = ClinicalFact(
            kind="symptom",
            value="dolor abdominal",
            confidence=0.95,
            evidence=ClinicalEvidence(transcript="me duele el estómago"),
        )
        fact2 = ClinicalFact(
            kind="vital_sign",
            value="presión 140/90",
            confidence=0.7,
            evidence=ClinicalEvidence(transcript="la presión está alta"),
        )
        draft.add_fact(fact1)
        draft.add_fact(fact2)

        assert len(draft.facts) == 2
        assert not fact1.needs_review()
        assert fact2.needs_review()
        # Both facts have status="detected", so both are in review_queue
        assert len(draft.review_queue()) == 2

    def test_approved_facts(self):
        draft = EncounterDraft()
        fact = ClinicalFact(
            kind="diagnosis",
            value="gastritis",
            confidence=0.9,
            evidence=ClinicalEvidence(transcript="diagnóstico gastritis"),
            status="approved",
        )
        draft.add_fact(fact)
        assert len(draft.approved_facts()) == 1


class TestFHIRClientParsing:
    def test_auth_header(self):
        from src.openmrs_client import _auth_header

        s = Settings(
            livekit_url="ws://localhost:7880",
            livekit_api_key="k",
            livekit_api_secret="s",
            openai_api_key="sk-test",
            openmrs_username="admin",
            openmrs_password="Admin123",
        )
        header = _auth_header(s)
        assert header.startswith("Basic ")
        import base64

        decoded = base64.b64decode(header.split(" ")[1]).decode()
        assert decoded == "admin:Admin123"
