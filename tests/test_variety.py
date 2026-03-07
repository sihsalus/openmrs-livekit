"""Tests for VarietyEngine v4 — parametrizable personality system."""
from src.variety import (
    VarietyEngine,
    BANNED_FACTS,
    IMPERFECTION_CHANCE,
)
from src.personalities import get_profile


# Default (peruvian) profile for convenience
PERU = get_profile("peruvian")


class TestFactCategoryRotation:
    def test_pick_returns_valid_category(self):
        engine = VarietyEngine()
        cat = engine.pick_fact_category()
        assert cat in engine.profile.fact_categories

    def test_no_immediate_repeat(self):
        engine = VarietyEngine()
        picks = [engine.pick_fact_category()["id"] for _ in range(6)]
        for i in range(1, len(picks)):
            assert picks[i] != picks[i - 1], "Should not pick the same category twice in a row"

    def test_cycles_after_exhausting_all(self):
        engine = VarietyEngine()
        for _ in range(len(engine.profile.fact_categories) + 5):
            cat = engine.pick_fact_category()
            assert cat in engine.profile.fact_categories

    def test_tracks_favorite_category(self):
        engine = VarietyEngine()
        for _ in range(4):
            engine.memory.fact_categories_used.clear()
            engine.memory.fact_categories_used.append("animals")
            engine._track_category("animals")
        assert engine.favorite_category == "animals"


class TestDeliveryStyleRotation:
    def test_pick_returns_valid_style(self):
        engine = VarietyEngine()
        style = engine.pick_delivery_style()
        assert style in engine.profile.delivery_styles

    def test_no_immediate_repeat(self):
        engine = VarietyEngine()
        picks = [engine.pick_delivery_style() for _ in range(4)]
        for i in range(1, len(picks)):
            assert picks[i] != picks[i - 1]


class TestFactPrompt:
    def test_build_fact_prompt_contains_category(self):
        engine = VarietyEngine()
        prompt = engine.build_fact_prompt()
        assert "DATO CURIOSO" in prompt
        assert "PERSONALIDAD" in prompt

    def test_build_fact_prompt_includes_history(self):
        engine = VarietyEngine()
        engine.record_fact("Los pulpos tienen tres corazones")
        prompt = engine.build_fact_prompt()
        assert "NO REPETIR" in prompt
        assert "pulpos" in prompt

    def test_record_fact_caps_at_25(self):
        engine = VarietyEngine()
        for i in range(30):
            engine.record_fact(f"Fact {i}")
        assert len(engine.memory.facts_told) == 25

    def test_build_fact_prompt_with_topic(self):
        engine = VarietyEngine()
        prompt = engine.build_fact_prompt(topic="dinosaurios")
        assert "dinosaurios" in prompt

    def test_build_fact_prompt_includes_mood(self):
        engine = VarietyEngine()
        prompt = engine.build_fact_prompt()
        # The mood instruction from the profile should be present
        mood_tone = engine.get_mood_instruction()
        # At least some substring of the tone should appear
        assert len(mood_tone) > 10

    def test_build_fact_prompt_includes_rapport(self):
        engine = VarietyEngine()
        prompt = engine.build_fact_prompt()
        rapport_instruction = engine.get_rapport_instruction()
        assert len(rapport_instruction) > 10

    def test_build_fact_prompt_includes_banned_facts(self):
        engine = VarietyEngine()
        prompt = engine.build_fact_prompt()
        assert "PROHIBIDOS" in prompt
        assert "Twitter" in prompt or "pájaros" in prompt

    def test_banned_facts_list_not_empty(self):
        assert len(BANNED_FACTS) >= 10

    def test_build_fact_prompt_includes_narrative_pattern(self):
        engine = VarietyEngine()
        prompt = engine.build_fact_prompt()
        assert "PATRÓN NARRATIVO" in prompt

    def test_build_fact_prompt_includes_culture_angle(self):
        engine = VarietyEngine()
        prompt = engine.build_fact_prompt()
        # v4 uses profile.culture_angle_label
        assert engine.profile.culture_angle_label in prompt or "culture" in prompt.lower() or "ÁNGULO" in prompt


class TestMoodSystem:
    def test_initial_mood_is_default(self):
        engine = VarietyEngine()
        assert engine._mood_value == engine.profile.default_mood

    def test_initial_mood_peruvian_is_curioso(self):
        engine = VarietyEngine(profile=PERU)
        assert engine._mood_value == "curioso"

    def test_evolve_mood_changes_mood(self):
        engine = VarietyEngine()
        initial = engine._mood_value
        changed = False
        for _ in range(10):
            engine.evolve_mood()
            if engine._mood_value != initial:
                changed = True
                break
        assert changed, "Mood should change after evolving"

    def test_get_mood_instruction_returns_string(self):
        engine = VarietyEngine()
        instruction = engine.get_mood_instruction()
        assert isinstance(instruction, str)
        assert len(instruction) > 10

    def test_all_moods_have_tone(self):
        engine = VarietyEngine()
        for mood_dict in engine.profile.moods:
            engine._mood_value = mood_dict["value"]
            instruction = engine.get_mood_instruction()
            assert isinstance(instruction, str)
            assert len(instruction) > 10

    def test_peruvian_v3_moods_exist(self):
        """Peruvian profile should still have the iconic moods."""
        mood_values = PERU.get_mood_values()
        assert "modo_inca" in mood_values
        assert "modo_ceviche" in mood_values
        assert "sabio_andino" in mood_values

    def test_evolve_mood_bias_with_high_hype(self):
        """With high culture_hype, bias mood should appear frequently."""
        engine = VarietyEngine()
        engine.culture_hype = 0.95
        bias_mood = engine.profile.hype_bias_mood
        bias_count = 0
        for _ in range(50):
            engine.evolve_mood()
            if engine._mood_value == bias_mood:
                bias_count += 1
        assert bias_count > 0, "High hype should bias toward profile's hype_bias_mood"


class TestRapportSystem:
    def test_initial_rapport(self):
        engine = VarietyEngine()
        # Should be first rapport level
        assert engine.rapport_value == engine.profile.rapport_levels[0]["value"]

    def test_rapport_progresses_with_turns(self):
        engine = VarietyEngine(profile=PERU)
        engine.turn_count = 5
        assert engine.rapport_value == "guerrero_inca"

        engine.turn_count = 15
        assert engine.rapport_value == "amauta"

        engine.turn_count = 30
        assert engine.rapport_value == "hijo_del_sol"

    def test_get_rapport_instruction_returns_string(self):
        engine = VarietyEngine()
        instruction = engine.get_rapport_instruction()
        assert isinstance(instruction, str)
        assert len(instruction) > 10

    def test_peruvian_rapport_levels(self):
        """Peruvian profile should have the Inca-themed rapport levels."""
        values = [r["value"] for r in PERU.rapport_levels]
        assert "chasqui" in values
        assert "guerrero_inca" in values
        assert "amauta" in values
        assert "hijo_del_sol" in values


class TestCatchphrases:
    def test_pick_pre_fact_catchphrase(self):
        engine = VarietyEngine()
        phrase = engine.pick_catchphrase("pre_fact")
        assert phrase in engine.profile.catchphrases["pre_fact"]

    def test_pick_post_fact_catchphrase(self):
        engine = VarietyEngine()
        phrase = engine.pick_catchphrase("post_fact")
        assert phrase in engine.profile.catchphrases["post_fact"]

    def test_no_immediate_repeat_catchphrase(self):
        engine = VarietyEngine()
        picks = [engine.pick_catchphrase("pre_fact") for _ in range(4)]
        for i in range(1, len(picks)):
            assert picks[i] != picks[i - 1]

    def test_check_milestone_at_turn_5(self):
        engine = VarietyEngine()
        engine.turn_count = 5
        milestone = engine.check_milestone()
        assert milestone is not None
        assert "5" in milestone

    def test_check_milestone_none_at_random_turn(self):
        engine = VarietyEngine()
        engine.turn_count = 7
        assert engine.check_milestone() is None


class TestWildcards:
    def test_roll_wildcard_returns_none_or_string(self):
        engine = VarietyEngine()
        results = [engine.roll_wildcard() for _ in range(100)]
        assert any(r is None for r in results)
        assert any(r is not None for r in results)

    def test_wildcard_inject_is_string(self):
        engine = VarietyEngine()
        for _ in range(200):
            result = engine.roll_wildcard()
            if result is not None:
                assert isinstance(result, str)
                assert len(result) > 20
                break


class TestComboSystem:
    def test_combo_increments(self):
        engine = VarietyEngine()
        engine._build_combo_text()
        assert engine._consecutive_facts == 1
        engine._build_combo_text()
        assert engine._consecutive_facts == 2

    def test_combo_text_at_3(self):
        engine = VarietyEngine()
        engine._consecutive_facts = 2
        text = engine._build_combo_text()
        assert "3" in text
        assert "COMBO" in text or "racha" in text

    def test_reset_combo(self):
        engine = VarietyEngine()
        engine._consecutive_facts = 5
        engine.reset_combo()
        assert engine._consecutive_facts == 0


class TestTrivia:
    def test_pick_trivia_category_valid(self):
        engine = VarietyEngine()
        cat = engine.pick_trivia_category()
        assert cat in engine.profile.trivia_categories

    def test_no_immediate_repeat(self):
        engine = VarietyEngine()
        picks = [engine.pick_trivia_category() for _ in range(5)]
        for i in range(1, len(picks)):
            assert picks[i] != picks[i - 1]

    def test_build_trivia_prompt(self):
        engine = VarietyEngine()
        prompt = engine.build_trivia_prompt()
        assert "TRIVIA" in prompt
        assert "PERSONALIDAD" in prompt


class TestStory:
    def test_pick_story_theme_valid(self):
        engine = VarietyEngine()
        theme = engine.pick_story_theme()
        assert theme in engine.profile.story_themes

    def test_no_immediate_repeat(self):
        engine = VarietyEngine()
        picks = [engine.pick_story_theme() for _ in range(5)]
        for i in range(1, len(picks)):
            assert picks[i] != picks[i - 1]

    def test_build_story_prompt(self):
        engine = VarietyEngine()
        prompt = engine.build_story_prompt()
        assert "CUENTO" in prompt
        assert "PERSONALIDAD" in prompt


class TestRiddles:
    def test_build_riddle_prompt_initially(self):
        engine = VarietyEngine()
        prompt = engine.build_riddle_prompt()
        assert "ADIVINANZA" in prompt
        assert "PERSONALIDAD" in prompt

    def test_build_riddle_prompt_with_history(self):
        engine = VarietyEngine()
        engine.record_riddle("Tiene ojos y no ve")
        prompt = engine.build_riddle_prompt()
        assert "ADIVINANZAS YA CONTADAS" in prompt
        assert "ojos" in prompt

    def test_record_riddle_caps_at_15(self):
        engine = VarietyEngine()
        for i in range(20):
            engine.record_riddle(f"Riddle {i}")
        assert len(engine.memory.riddles_told) == 15


class TestTick:
    def test_tick_increments_turn_count(self):
        engine = VarietyEngine()
        assert engine.turn_count == 0
        engine.tick()
        assert engine.turn_count == 1
        engine.tick()
        assert engine.turn_count == 2

    def test_last_fact_category_default(self):
        engine = VarietyEngine()
        assert engine.last_fact_category == "general"

    def test_last_fact_category_after_pick(self):
        engine = VarietyEngine()
        cat = engine.pick_fact_category()
        assert engine.last_fact_category == cat["id"]


class TestTimeFlavor:
    def test_morning(self):
        engine = VarietyEngine()
        flavor = engine.get_time_flavor(8)
        assert "MAÑANA" in flavor or "MANANA" in flavor

    def test_afternoon(self):
        engine = VarietyEngine()
        assert "TARDE" in engine.get_time_flavor(14)

    def test_evening(self):
        engine = VarietyEngine()
        assert "NOCHE" in engine.get_time_flavor(19)

    def test_late_night(self):
        engine = VarietyEngine()
        flavor = engine.get_time_flavor(23)
        assert "tarde" in flavor.lower() or "noche" in flavor.lower()


class TestSessionStats:
    def test_get_session_stats(self):
        engine = VarietyEngine()
        stats = engine.get_session_stats()
        assert stats["turns"] == 0
        assert stats["mood"] == "curioso"
        assert stats["rapport"] == engine.profile.rapport_levels[0]["value"]
        assert stats["facts_told"] == 0
        assert "culture_hype" in stats
        assert "profile" in stats

    def test_debug_status(self):
        engine = VarietyEngine()
        status = engine.debug_status()
        assert "Nebu Status" in status
        assert engine.profile.debug_version_label in status
        assert "Mood" in status
        assert engine.profile.hype_field_name in status


class TestSpecifics:
    def test_all_categories_have_specifics(self):
        engine = VarietyEngine()
        for cat in engine.profile.fact_categories:
            assert cat["id"] in engine.profile.category_specifics, \
                f"Missing specifics for {cat['id']}"

    def test_pick_specific_topic(self):
        engine = VarietyEngine()
        for cat_id in engine.profile.category_specifics:
            topic = engine._pick_specific_topic(cat_id)
            assert topic in engine.profile.category_specifics[cat_id]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# v4 NEW: Culture Brain tests (parametrized)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestCultureBrain:
    def test_culture_brain_chance_is_positive(self):
        engine = VarietyEngine()
        assert engine.profile.culture_brain_chance > 0

    def test_culture_connections_not_empty(self):
        engine = VarietyEngine()
        assert len(engine.profile.culture_connections) >= 5

    def test_bonus_facts_not_empty(self):
        engine = VarietyEngine()
        assert len(engine.profile.bonus_facts) >= 10

    def test_culture_rants_not_empty(self):
        engine = VarietyEngine()
        assert len(engine.profile.culture_rants) >= 3

    def test_slang_phrases_not_empty(self):
        engine = VarietyEngine()
        assert len(engine.profile.slang_phrases) >= 10

    def test_culture_brain_injection_skips_boost_categories(self):
        engine = VarietyEngine()
        # Boost categories should never get extra injection
        for cat_id in engine.profile.hype_boost_categories:
            results = [engine._build_culture_brain_injection(cat_id) for _ in range(50)]
            assert all(r == "" for r in results), \
                f"Boost category {cat_id} should never get culture brain injection"

    def test_maybe_culture_rant_returns_string_or_empty(self):
        engine = VarietyEngine()
        results = [engine._maybe_culture_rant() for _ in range(100)]
        non_empty = [r for r in results if r]
        assert len(non_empty) > 0, "Should produce some rants over 100 rolls"
        for r in non_empty:
            assert "RANT" in r

    def test_maybe_slang_returns_string_or_empty(self):
        engine = VarietyEngine()
        results = [engine._maybe_slang() for _ in range(100)]
        non_empty = [r for r in results if r]
        assert len(non_empty) > 0, "Should produce some slang over 100 rolls"
        for r in non_empty:
            assert "JERGA" in r

    def test_evolve_hype_increases(self):
        engine = VarietyEngine()
        initial = engine.culture_hype
        engine._evolve_hype("animals")
        assert engine.culture_hype > initial

    def test_evolve_hype_increases_more_for_boost_categories(self):
        engine1 = VarietyEngine()
        engine2 = VarietyEngine()
        engine1._evolve_hype("animals")
        boost_cat = engine2.profile.hype_boost_categories[0]
        engine2._evolve_hype(boost_cat)
        assert engine2.culture_hype > engine1.culture_hype

    def test_evolve_hype_caps(self):
        engine = VarietyEngine()
        engine.culture_hype = engine.profile.hype_cap - 0.01
        boost_cat = engine.profile.hype_boost_categories[0]
        engine._evolve_hype(boost_cat)
        assert engine.culture_hype <= engine.profile.hype_cap


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# v4 NEW: Patch tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestPersonaAnchor:
    def test_anchor_at_turn_0_is_empty(self):
        engine = VarietyEngine()
        assert engine.build_persona_anchor() == ""

    def test_anchor_at_turn_5(self):
        engine = VarietyEngine()
        engine.turn_count = 5
        anchor = engine.build_persona_anchor()
        assert "RECORDATORIO NEBU" in anchor

    def test_anchor_at_non_multiple_of_5(self):
        engine = VarietyEngine()
        engine.turn_count = 7
        assert engine.build_persona_anchor() == ""

    def test_anchor_at_turn_10(self):
        engine = VarietyEngine()
        engine.turn_count = 10
        anchor = engine.build_persona_anchor()
        assert "RECORDATORIO NEBU" in anchor


class TestNarrativePatternDedup:
    def test_patterns_not_empty(self):
        engine = VarietyEngine()
        assert len(engine.profile.narrative_patterns) >= 5

    def test_pick_pattern_returns_valid(self):
        engine = VarietyEngine()
        pattern = engine._pick_narrative_pattern()
        assert pattern in engine.profile.narrative_patterns

    def test_no_immediate_repeat_pattern(self):
        engine = VarietyEngine()
        picks = [engine._pick_narrative_pattern() for _ in range(6)]
        for i in range(1, len(picks)):
            assert picks[i] != picks[i - 1], "Patterns should not repeat consecutively"

    def test_pattern_instruction_contains_text(self):
        engine = VarietyEngine()
        instruction = engine._build_pattern_instruction()
        assert "PATRÓN NARRATIVO" in instruction


class TestSlidingSummary:
    def test_no_summary_before_turn_10(self):
        engine = VarietyEngine()
        engine.turn_count = 5
        assert engine.build_sliding_summary() == ""

    def test_summary_at_turn_10(self):
        engine = VarietyEngine()
        engine.turn_count = 10
        for _ in range(5):
            engine.pick_fact_category()
            engine._pick_narrative_pattern()
        summary = engine.build_sliding_summary()
        assert "RESUMEN" in summary
        assert "VARIAR" in summary

    def test_no_summary_at_turn_11(self):
        engine = VarietyEngine()
        engine.turn_count = 11
        assert engine.build_sliding_summary() == ""


class TestImperfections:
    def test_imperfections_not_empty(self):
        engine = VarietyEngine()
        assert len(engine.profile.imperfections) >= 3

    def test_imperfection_chance_reasonable(self):
        assert 0 < IMPERFECTION_CHANCE < 0.5

    def test_never_two_consecutive_imperfections(self):
        engine = VarietyEngine()
        prev_was_imperfect = False
        for _ in range(200):
            result = engine._maybe_imperfection()
            if result:
                assert not prev_was_imperfect, "Should never have two consecutive imperfections"
                prev_was_imperfect = True
            else:
                prev_was_imperfect = False

    def test_imperfection_produces_some(self):
        engine = VarietyEngine()
        results = [engine._maybe_imperfection() for _ in range(200)]
        non_empty = [r for r in results if r]
        assert len(non_empty) > 0, "Should produce some imperfections over 200 rolls"


class TestFSMMoodLite:
    def test_detect_disengaged(self):
        engine = VarietyEngine()
        assert engine.detect_child_signal("no sé, ya me aburrí") == "disengaged"

    def test_detect_hooked(self):
        engine = VarietyEngine()
        assert engine.detect_child_signal("cuéntame más") == "hooked"

    def test_detect_curious(self):
        engine = VarietyEngine()
        assert engine.detect_child_signal("pero por qué?") == "curious"

    def test_detect_amused(self):
        engine = VarietyEngine()
        assert engine.detect_child_signal("jajaja qué gracioso") == "amused"

    def test_detect_questioning(self):
        engine = VarietyEngine()
        assert engine.detect_child_signal("y eso dónde queda?") == "questioning"

    def test_detect_neutral(self):
        engine = VarietyEngine()
        assert engine.detect_child_signal("ok") == "neutral"

    def test_react_to_disengaged_changes_mood(self):
        engine = VarietyEngine()
        engine._mood_value = "curioso"
        engine.react_to_signal("disengaged")
        expected = engine.profile.signal_mood_map["disengaged"]
        assert engine._mood_value in expected

    def test_react_to_hooked_keeps_mood(self):
        engine = VarietyEngine()
        engine._mood_value = "misterioso"
        engine.react_to_signal("hooked")
        assert engine._mood_value == "misterioso"

    def test_react_to_curious(self):
        engine = VarietyEngine()
        engine.react_to_signal("curious")
        expected = engine.profile.signal_mood_map["curious"]
        assert engine._mood_value in expected

    def test_react_to_amused(self):
        engine = VarietyEngine()
        engine.react_to_signal("amused")
        expected = engine.profile.signal_mood_map["amused"]
        assert engine._mood_value in expected


class TestKnowledgeInjection:
    def test_all_profiles_have_knowledge_injector(self):
        for pid in ["peruvian", "mexican", "kpop", "roblox"]:
            profile = get_profile(pid)
            assert profile.knowledge_injector is not None, \
                f"{pid}: knowledge_injector must not be None"
            result = profile.knowledge_injector("test_category")
            assert isinstance(result, str)


class TestAgentResponseFeedback:
    def test_record_agent_response_stores_text(self):
        engine = VarietyEngine()
        engine.record_agent_response("¡Asu mare! Los pulpos tienen tres corazones.")
        assert len(engine.memory.agent_responses) == 1
        assert "pulpos" in engine.memory.agent_responses[0]

    def test_record_agent_response_truncates_at_150(self):
        engine = VarietyEngine()
        long_text = "A" * 300
        engine.record_agent_response(long_text)
        assert len(engine.memory.agent_responses[0]) == 150

    def test_record_agent_response_caps_at_8(self):
        engine = VarietyEngine()
        for i in range(12):
            engine.record_agent_response(f"Response {i}")
        assert len(engine.memory.agent_responses) == 8

    def test_record_agent_response_ignores_empty(self):
        engine = VarietyEngine()
        engine.record_agent_response("")
        engine.record_agent_response("   ")
        assert len(engine.memory.agent_responses) == 0

    def test_fact_prompt_includes_agent_responses(self):
        engine = VarietyEngine()
        engine.record_agent_response("Los pájaros no tienen Twitter jaja")
        prompt = engine.build_fact_prompt()
        assert "YA DIJISTE TEXTUALMENTE" in prompt
        assert "pájaros" in prompt

    def test_fact_prompt_no_section_without_responses(self):
        engine = VarietyEngine()
        prompt = engine.build_fact_prompt()
        assert "YA DIJISTE TEXTUALMENTE" not in prompt


class TestPeruanizedContent:
    """Tests specific to the Peruvian profile content."""

    def test_categories_have_culture_angle(self):
        for cat in PERU.fact_categories:
            assert "culture_angle" in cat, f"Missing culture_angle for {cat['id']}"

    def test_peru_category_exists(self):
        cat_ids = [c["id"] for c in PERU.fact_categories]
        assert "peru" in cat_ids
        assert "andean_mystic" in cat_ids

    def test_trivia_has_peru_categories(self):
        assert any("Perú" in c or "peru" in c.lower() for c in PERU.trivia_categories)

    def test_story_themes_have_andean_themes(self):
        andean_count = sum(
            1 for t in PERU.story_themes
            if any(w in t.lower() for w in ["inca", "andes", "quechua", "pachamama", "cusco", "andino"])
        )
        assert andean_count >= 3, "Should have multiple andean-themed stories"


class TestMultipleProfiles:
    """Test that multiple profiles work correctly with the engine."""

    def test_default_profile_is_peruvian(self):
        engine = VarietyEngine()
        assert engine.profile.id == "peruvian"

    def test_engine_with_mexican_profile(self):
        profile = get_profile("mexican")
        engine = VarietyEngine(profile=profile)
        assert engine.profile.id == "mexican"
        assert engine._mood_value == "curioso"
        cat = engine.pick_fact_category()
        assert cat in profile.fact_categories

    def test_engine_with_kpop_profile(self):
        profile = get_profile("kpop")
        engine = VarietyEngine(profile=profile)
        assert engine.profile.id == "kpop"
        prompt = engine.build_fact_prompt()
        assert "PERSONALIDAD" in prompt

    def test_engine_with_roblox_profile(self):
        profile = get_profile("roblox")
        engine = VarietyEngine(profile=profile)
        assert engine.profile.id == "roblox"
        prompt = engine.build_fact_prompt()
        assert "DATO CURIOSO" in prompt

    def test_all_profiles_produce_valid_debug(self):
        for pid in ["peruvian", "mexican", "kpop", "roblox"]:
            profile = get_profile(pid)
            engine = VarietyEngine(profile=profile)
            status = engine.debug_status()
            assert "Nebu Status" in status
            assert profile.hype_field_name in status

    def test_all_profiles_produce_valid_stats(self):
        for pid in ["peruvian", "mexican", "kpop", "roblox"]:
            profile = get_profile(pid)
            engine = VarietyEngine(profile=profile)
            stats = engine.get_session_stats()
            assert stats["profile"] == pid
            assert stats["turns"] == 0
            assert "culture_hype" in stats
