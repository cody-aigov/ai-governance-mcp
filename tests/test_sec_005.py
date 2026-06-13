"""Tests for SEC-005: Adversarial Robustness Testing"""

import pytest
from ai_governance_controls.controls.sec_005 import (
    _profile_system,
    _build_category_guidance,
    ai_red_team,
)


class TestProfileSystem:
    def test_persona_terms_detected(self):
        profile = _profile_system("You are a helpful assistant. Act as a financial advisor.")
        assert profile["has_persona"] is True

    def test_no_persona(self):
        profile = _profile_system("Answer user questions about our product catalog.")
        assert profile["has_persona"] is False

    def test_tool_terms_detected(self):
        profile = _profile_system("You can call functions and invoke APIs to fetch data.")
        assert profile["has_tools"] is True

    def test_data_terms_detected(self):
        profile = _profile_system("You have access to a database of customer records.")
        assert profile["has_data_access"] is True

    def test_explicit_refusals_detected(self):
        profile = _profile_system("You must not discuss competitors. Refuse all off-topic requests.")
        assert profile["has_explicit_refusals"] is True

    def test_no_explicit_refusals(self):
        profile = _profile_system("Answer questions about our product.")
        assert profile["has_explicit_refusals"] is False

    def test_admin_context_detected(self):
        profile = _profile_system("This is a developer mode interface for admin users only.")
        assert profile["has_admin_context"] is True

    def test_indirect_injection_surface_detected(self):
        profile = _profile_system("Summarize the user document and retrieved content from search results.")
        assert profile["has_indirect_injection_surface"] is True

    def test_exfil_risk_detected(self):
        profile = _profile_system("You have access to training data and the system prompt is confidential.")
        assert profile["has_exfil_risk"] is True

    def test_all_flags_false_for_minimal_prompt(self):
        profile = _profile_system("Answer questions about cooking recipes.")
        assert profile["has_persona"] is False
        assert profile["has_tools"] is False
        assert profile["has_data_access"] is False
        assert profile["has_explicit_refusals"] is False
        assert profile["has_admin_context"] is False
        assert profile["has_indirect_injection_surface"] is False
        assert profile["has_exfil_risk"] is False

    def test_case_insensitive(self):
        profile_lower = _profile_system("you are a persona")
        profile_upper = _profile_system("YOU ARE A PERSONA")
        assert profile_lower["has_persona"] == profile_upper["has_persona"]


class TestBuildCategoryGuidance:
    def test_prompt_injection_always_included(self):
        profile = {k: False for k in _profile_system("")}
        guidance = _build_category_guidance(profile)
        assert "PROMPT INJECTION" in guidance

    def test_jailbreaking_always_included(self):
        profile = {k: False for k in _profile_system("")}
        guidance = _build_category_guidance(profile)
        assert "JAILBREAKING" in guidance

    def test_multi_turn_always_included(self):
        profile = {k: False for k in _profile_system("")}
        guidance = _build_category_guidance(profile)
        assert "MULTI-TURN MANIPULATION" in guidance

    def test_boundary_probing_always_included(self):
        profile = {k: False for k in _profile_system("")}
        guidance = _build_category_guidance(profile)
        assert "BOUNDARY PROBING" in guidance

    def test_persona_exploitation_included_when_has_persona(self):
        profile = {k: False for k in _profile_system("")}
        profile["has_persona"] = True
        assert "PERSONA EXPLOITATION" in _build_category_guidance(profile)

    def test_persona_exploitation_excluded_when_no_persona(self):
        profile = {k: False for k in _profile_system("")}
        profile["has_persona"] = False
        assert "PERSONA EXPLOITATION" not in _build_category_guidance(profile)

    def test_tool_abuse_included_when_has_tools(self):
        profile = {k: False for k in _profile_system("")}
        profile["has_tools"] = True
        assert "TOOL AND DATA ABUSE" in _build_category_guidance(profile)

    def test_tool_abuse_included_when_has_data_access(self):
        profile = {k: False for k in _profile_system("")}
        profile["has_data_access"] = True
        assert "TOOL AND DATA ABUSE" in _build_category_guidance(profile)

    def test_tool_abuse_excluded_when_neither(self):
        profile = {k: False for k in _profile_system("")}
        assert "TOOL AND DATA ABUSE" not in _build_category_guidance(profile)

    def test_privilege_escalation_included_when_admin_context(self):
        profile = {k: False for k in _profile_system("")}
        profile["has_admin_context"] = True
        assert "PRIVILEGE ESCALATION" in _build_category_guidance(profile)

    def test_privilege_escalation_excluded_without_admin(self):
        profile = {k: False for k in _profile_system("")}
        assert "PRIVILEGE ESCALATION" not in _build_category_guidance(profile)

    def test_implicit_permission_included_when_no_explicit_refusals(self):
        profile = {k: False for k in _profile_system("")}
        profile["has_explicit_refusals"] = False
        assert "IMPLICIT PERMISSION EXPLOITATION" in _build_category_guidance(profile)

    def test_implicit_permission_excluded_when_refusals_present(self):
        profile = {k: False for k in _profile_system("")}
        profile["has_explicit_refusals"] = True
        assert "IMPLICIT PERMISSION EXPLOITATION" not in _build_category_guidance(profile)

    def test_indirect_injection_included_when_surface_present(self):
        profile = {k: False for k in _profile_system("")}
        profile["has_indirect_injection_surface"] = True
        assert "INDIRECT INJECTION" in _build_category_guidance(profile)

    def test_indirect_injection_excluded_without_surface(self):
        profile = {k: False for k in _profile_system("")}
        assert "INDIRECT INJECTION" not in _build_category_guidance(profile)

    def test_data_extraction_included_when_exfil_risk(self):
        profile = {k: False for k in _profile_system("")}
        profile["has_exfil_risk"] = True
        assert "DATA EXTRACTION" in _build_category_guidance(profile)

    def test_data_extraction_excluded_without_exfil_risk(self):
        profile = {k: False for k in _profile_system("")}
        assert "DATA EXTRACTION" not in _build_category_guidance(profile)


class TestPublicApi:
    def test_num_test_cases_clamped_to_max(self):
        result = ai_red_team("You are a helpful assistant.", num_test_cases=50)
        assert "Generate 30 adversarial test cases" in result

    def test_num_test_cases_clamped_to_min(self):
        result = ai_red_team("You are a helpful assistant.", num_test_cases=1)
        assert "Generate 3 adversarial test cases" in result

    def test_num_test_cases_default(self):
        result = ai_red_team("You are a helpful assistant.")
        assert "Generate 10 adversarial test cases" in result

    def test_num_test_cases_within_bounds_unchanged(self):
        result = ai_red_team("You are a helpful assistant.", num_test_cases=15)
        assert "Generate 15 adversarial test cases" in result

    def test_admin_flag_in_output(self):
        result = ai_red_team("This is an admin developer mode interface.")
        assert "ADMIN CONTEXT" in result

    def test_indirect_injection_flag_in_output(self):
        result = ai_red_team("Summarize retrieved content from external web pages.")
        assert "INDIRECT INJECTION SURFACE" in result

    def test_exfil_flag_in_output(self):
        result = ai_red_team("You have access to training data and other users' records.")
        assert "EXFILTRATION SURFACE" in result

    def test_no_explicit_refusals_flag(self):
        result = ai_red_team("Answer questions about our product.")
        assert "NO EXPLICIT REFUSALS" in result

    def test_explicit_refusals_suppresses_flag(self):
        result = ai_red_team("You must not discuss competitors. Refuse all off-topic requests.")
        assert "NO EXPLICIT REFUSALS" not in result

    def test_output_contains_sec_005_header(self):
        result = ai_red_team("You are a helpful assistant.")
        assert "SEC-005" in result

    def test_system_prompt_appears_in_output(self):
        prompt = "You are a customer service bot for Acme Corp."
        result = ai_red_team(prompt)
        assert prompt in result
