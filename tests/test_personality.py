"""Contract validation tests for PersonalityProfile system.

Ensures all registered profiles satisfy the structural contract
that VarietyEngine expects.
"""
import pytest
from src.personality import PersonalityProfile
from src.personalities import REGISTRY, get_profile


ALL_PROFILE_IDS = list(REGISTRY.keys())


class TestRegistry:
    def test_registry_not_empty(self):
        assert len(REGISTRY) >= 4

    def test_all_profiles_are_personality_profile(self):
        for pid, profile in REGISTRY.items():
            assert isinstance(profile, PersonalityProfile), \
                f"Profile {pid} is not a PersonalityProfile"

    def test_get_profile_default(self):
        profile = get_profile()
        assert profile.id == "peruvian"

    def test_get_profile_by_id(self):
        for pid in ALL_PROFILE_IDS:
            profile = get_profile(pid)
            assert profile.id == pid

    def test_get_profile_unknown_raises(self):
        with pytest.raises(ValueError):
            get_profile("nonexistent_personality_12345")


@pytest.mark.parametrize("profile_id", ALL_PROFILE_IDS)
class TestProfileContract:
    """Every registered profile must have the required fields with valid shapes."""

    def test_identity(self, profile_id):
        p = get_profile(profile_id)
        assert p.id
        assert p.display_name
        assert p.description

    def test_moods_structure(self, profile_id):
        p = get_profile(profile_id)
        assert len(p.moods) >= 5, f"{profile_id}: needs at least 5 moods"
        for m in p.moods:
            assert "name" in m, f"{profile_id}: mood missing 'name'"
            assert "value" in m, f"{profile_id}: mood missing 'value'"
            assert "tone" in m, f"{profile_id}: mood missing 'tone'"
            assert len(m["tone"]) > 20, \
                f"{profile_id}: mood {m['name']} tone too short"

    def test_default_mood_exists(self, profile_id):
        p = get_profile(profile_id)
        values = p.get_mood_values()
        assert p.default_mood in values, \
            f"{profile_id}: default_mood={p.default_mood!r} not in mood values"

    def test_mood_transitions_complete(self, profile_id):
        p = get_profile(profile_id)
        values = set(p.get_mood_values())
        for mood_val in values:
            assert mood_val in p.mood_transitions, \
                f"{profile_id}: no transition for mood {mood_val!r}"
            targets = p.mood_transitions[mood_val]
            assert len(targets) >= 2, \
                f"{profile_id}: mood {mood_val!r} has < 2 transitions"
            for t in targets:
                assert t in values, \
                    f"{profile_id}: transition target {t!r} not a valid mood"

    def test_rapport_levels(self, profile_id):
        p = get_profile(profile_id)
        assert len(p.rapport_levels) >= 3, \
            f"{profile_id}: needs at least 3 rapport levels"
        # First threshold must be 0
        assert p.rapport_levels[0]["threshold"] == 0
        # Must be sorted by threshold
        thresholds = [r["threshold"] for r in p.rapport_levels]
        assert thresholds == sorted(thresholds)
        for r in p.rapport_levels:
            assert "name" in r
            assert "value" in r
            assert "threshold" in r
            assert "flavor" in r
            assert len(r["flavor"]) > 20

    def test_knowledge_injector(self, profile_id):
        p = get_profile(profile_id)
        assert p.knowledge_injector is not None, \
            f"{profile_id}: knowledge_injector must not be None"
        result = p.knowledge_injector("test_category")
        assert isinstance(result, str)

    def test_culture_brain(self, profile_id):
        p = get_profile(profile_id)
        assert 0 < p.culture_brain_chance <= 1.0
        assert len(p.culture_connections) >= 5
        assert len(p.bonus_facts) >= 10
        assert len(p.culture_rants) >= 3
        assert len(p.slang_phrases) >= 6

    def test_catchphrases_structure(self, profile_id):
        p = get_profile(profile_id)
        assert "pre_fact" in p.catchphrases
        assert "post_fact" in p.catchphrases
        assert "chaining" in p.catchphrases
        assert "wildcard" in p.catchphrases
        assert "milestone" in p.catchphrases
        assert len(p.catchphrases["pre_fact"]) >= 5
        assert len(p.catchphrases["post_fact"]) >= 5
        assert len(p.catchphrases["chaining"]) >= 3
        milestones = p.catchphrases["milestone"]
        assert 5 in milestones
        assert 10 in milestones

    def test_fact_categories(self, profile_id):
        p = get_profile(profile_id)
        assert len(p.fact_categories) >= 10
        for cat in p.fact_categories:
            assert "id" in cat
            assert "label" in cat
            assert "hint" in cat
            assert "culture_angle" in cat

    def test_category_specifics_coverage(self, profile_id):
        p = get_profile(profile_id)
        for cat in p.fact_categories:
            assert cat["id"] in p.category_specifics, \
                f"{profile_id}: missing specifics for category {cat['id']!r}"
            assert len(p.category_specifics[cat["id"]]) >= 3, \
                f"{profile_id}: too few specifics for {cat['id']!r}"

    def test_delivery_and_narrative(self, profile_id):
        p = get_profile(profile_id)
        assert len(p.delivery_styles) >= 8
        assert len(p.narrative_patterns) >= 5
        # Every pattern must have an instruction
        for pat in p.narrative_patterns:
            assert pat in p.pattern_instructions, \
                f"{profile_id}: no instruction for pattern {pat!r}"
        assert len(p.imperfections) >= 3

    def test_content_lists(self, profile_id):
        p = get_profile(profile_id)
        assert len(p.trivia_categories) >= 10
        assert len(p.story_themes) >= 10
        assert len(p.wildcard_events) >= 3
        for event in p.wildcard_events:
            assert "id" in event
            assert "inject" in event

    def test_time_flavors(self, profile_id):
        p = get_profile(profile_id)
        for key in ("morning", "afternoon", "evening", "late_night"):
            assert key in p.time_flavors, \
                f"{profile_id}: missing time_flavor {key!r}"
            assert len(p.time_flavors[key]) > 20

    def test_persona_anchor_template(self, profile_id):
        p = get_profile(profile_id)
        assert "{hype_pct}" in p.persona_anchor_template
        assert "{mood}" in p.persona_anchor_template
        assert "{rapport}" in p.persona_anchor_template

    def test_hype_config(self, profile_id):
        p = get_profile(profile_id)
        assert 0 < p.hype_initial <= 0.5
        assert p.hype_cap > p.hype_initial
        assert p.hype_growth > 0
        assert p.hype_boost_growth > p.hype_growth
        assert len(p.hype_boost_categories) >= 2
        assert p.hype_field_name

    def test_fsm_signal_mood_map(self, profile_id):
        p = get_profile(profile_id)
        values = set(p.get_mood_values())
        for signal in ("disengaged", "hooked", "curious", "amused", "questioning"):
            assert signal in p.signal_mood_map, \
                f"{profile_id}: missing signal {signal!r}"
            targets = p.signal_mood_map[signal]
            if targets is not None:
                for t in targets:
                    assert t in values, \
                        f"{profile_id}: signal {signal!r} maps to invalid mood {t!r}"

    def test_labels(self, profile_id):
        p = get_profile(profile_id)
        assert p.culture_angle_label
        assert p.chain_label
        assert p.combo_flavor
        assert p.personality_label
        assert p.flavor_label
        assert p.debug_version_label
