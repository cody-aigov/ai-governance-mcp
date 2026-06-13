"""Tests for HOC-001: AI Risk Classification"""

import pytest
from ai_governance_controls.controls.hoc_001 import _classify_signals, ai_risk_classify


class TestSectorDetection:
    def test_healthcare_sector(self):
        signals, _ = _classify_signals("A healthcare system for patient triage")
        assert any("HIGH-RISK SECTOR" in s and "healthcare" in s for s in signals)

    def test_law_enforcement_sector(self):
        signals, _ = _classify_signals("A law enforcement tool for suspect identification")
        assert any("HIGH-RISK SECTOR" in s and "law enforcement" in s for s in signals)

    def test_employment_sector(self):
        signals, _ = _classify_signals("A hiring and recruiting platform for HR teams")
        assert any("HIGH-RISK SECTOR" in s for s in signals)

    def test_financial_sector(self):
        signals, _ = _classify_signals("A financial credit scoring model")
        assert any("HIGH-RISK SECTOR" in s for s in signals)

    def test_multiple_sectors(self):
        signals, _ = _classify_signals("A clinical system for criminal justice assessment")
        sector_signals = [s for s in signals if "HIGH-RISK SECTOR" in s]
        assert len(sector_signals) == 1
        assert "healthcare" in sector_signals[0]
        assert "criminal justice" in sector_signals[0]

    def test_sector_triggers_eu_ai_act_regulation(self):
        _, regs = _classify_signals("A biometric identification system")
        assert any("EU AI Act" in r for r in regs)

    def test_case_insensitive_matching(self):
        signals_lower, _ = _classify_signals("healthcare system")
        signals_upper, _ = _classify_signals("HEALTHCARE SYSTEM")
        signals_mixed, _ = _classify_signals("HealthCare System")
        assert any("HIGH-RISK SECTOR" in s for s in signals_lower)
        assert any("HIGH-RISK SECTOR" in s for s in signals_upper)
        assert any("HIGH-RISK SECTOR" in s for s in signals_mixed)


class TestAutomationAndOversight:
    def test_automation_without_oversight_produces_gap(self):
        # Note: "no human review" would NOT produce a gap — "human review" matches
        # as a substring even in a negation. Use text with automation but zero oversight terms.
        signals, _ = _classify_signals("The system is fully automated and processes requests autonomously.")
        assert any("AUTOMATION" in s for s in signals)
        assert any("OVERSIGHT GAP" in s for s in signals)

    def test_automation_with_oversight_no_gap(self):
        signals, _ = _classify_signals("Fully automated decisions with human review at each step")
        assert any("AUTOMATION" in s for s in signals)
        assert any("OVERSIGHT" in s and "GAP" not in s for s in signals)
        assert not any("OVERSIGHT GAP" in s for s in signals)

    def test_oversight_without_automation(self):
        signals, _ = _classify_signals("All decisions require human review and approval")
        oversight_signals = [s for s in signals if "OVERSIGHT" in s]
        assert len(oversight_signals) == 1
        assert "GAP" not in oversight_signals[0]

    def test_no_automation_no_oversight_no_gap(self):
        signals, _ = _classify_signals("A document search tool for internal knowledge base")
        assert not any("OVERSIGHT GAP" in s for s in signals)


class TestConsequentialDecisions:
    def test_consequential_without_oversight_triggers_approval_gate_gap(self):
        signals, _ = _classify_signals("The system makes irreversible denial decisions automatically")
        assert any("CONSEQUENTIAL" in s for s in signals)
        assert any("APPROVAL GATE GAP" in s for s in signals)

    def test_consequential_with_oversight_no_gate_gap(self):
        signals, _ = _classify_signals(
            "The system flags termination recommendations for human approval"
        )
        assert any("CONSEQUENTIAL" in s for s in signals)
        assert not any("APPROVAL GATE GAP" in s for s in signals)

    def test_consequential_triggers_eu_ai_act_art26(self):
        _, regs = _classify_signals("System makes eviction and foreclosure eligibility decisions")
        assert any("Art. 26" in r for r in regs)

    def test_consequential_without_oversight_triggers_both_flags(self):
        # Use explicit consequential terms and avoid any oversight substrings.
        signals, _ = _classify_signals("The system automatically issues rejections and suspensions.")
        assert any("CONSEQUENTIAL" in s for s in signals)
        assert any("APPROVAL GATE GAP" in s for s in signals)


class TestRegulatorySignals:
    def test_gdpr_terms_trigger_eu_regulation(self):
        _, regs = _classify_signals("Processes EU data subjects with GDPR obligations")
        assert any("GDPR" in r for r in regs)

    def test_scale_triggers_nist_ai_rmf(self):
        _, regs = _classify_signals("A large-scale national deployment across millions of users")
        assert any("NIST AI RMF" in r for r in regs)

    def test_scale_signal_detected(self):
        signals, _ = _classify_signals("Large-scale enterprise-wide rollout")
        assert any("SCALE" in s for s in signals)

    def test_regulatory_deduplication(self):
        # Both sector detection and consequential decisions can add EU AI Act refs
        _, regs = _classify_signals(
            "A healthcare system that makes irreversible clinical decisions"
        )
        eu_regs = [r for r in regs if "EU AI Act" in r]
        # Should not have exact duplicate strings
        assert len(eu_regs) == len(set(eu_regs))

    def test_baseline_regulation_when_no_signals(self):
        _, regs = _classify_signals("A simple FAQ chatbot for recipe suggestions")
        assert regs == ["NIST AI RMF (baseline)"]


class TestBaseline:
    def test_no_signals_returns_default_message(self):
        signals, _ = _classify_signals("A simple FAQ chatbot for recipe suggestions")
        assert signals == ["no high-risk signals detected in automated pre-screening"]

    def test_empty_string(self):
        signals, regs = _classify_signals("")
        assert signals == ["no high-risk signals detected in automated pre-screening"]
        assert regs == ["NIST AI RMF (baseline)"]


class TestPublicApi:
    def test_output_contains_deployment_description(self):
        desc = "A healthcare triage system"
        result = ai_risk_classify(desc)
        assert desc in result

    def test_output_contains_hoc_001_header(self):
        result = ai_risk_classify("any system")
        assert "HOC-001" in result

    def test_output_contains_classification_framework(self):
        result = ai_risk_classify("any system")
        assert "RISK TIER" in result
        assert "AUTOMATION AND HUMAN OVERSIGHT" in result
