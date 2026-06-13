"""Tests for SAF-002: AI Output Validation"""

import pytest
from ai_governance_controls.controls.saf_002 import _detect_signals, ai_safety_screen


class TestActuatorDetection:
    def test_actuator_terms_detected(self):
        signals = _detect_signals("The agent will execute and deploy changes automatically")
        assert any("ACTUATOR" in s for s in signals)

    def test_financial_terms_detected(self):
        signals = _detect_signals("Handles wire transfers and payment processing")
        assert any("FINANCIAL" in s for s in signals)

    def test_destructive_db_operations_detected(self):
        signals = _detect_signals("Can drop or truncate database tables")
        assert any("ACTUATOR" in s for s in signals)


class TestAuthGap:
    def test_actuator_without_auth_triggers_gap(self):
        signals = _detect_signals("Automatically execute file deletions on user request")
        assert any("AUTH GAP" in s for s in signals)

    def test_actuator_with_auth_no_gap(self):
        signals = _detect_signals("Execute transfers only after MFA verification and user consent")
        assert not any("AUTH GAP" in s for s in signals)

    def test_agentic_without_auth_triggers_gap(self):
        signals = _detect_signals("An autonomous agent that orchestrates multi-step workflows")
        assert any("AUTH GAP" in s for s in signals)

    def test_agentic_with_auth_no_gap(self):
        signals = _detect_signals("An autonomous agent with role-based access control and JWT authentication")
        assert not any("AUTH GAP" in s for s in signals)

    def test_no_actuator_no_auth_gap(self):
        signals = _detect_signals("A read-only search tool that summarizes documents")
        assert not any("AUTH GAP" in s for s in signals)


class TestPiiDetection:
    def test_pii_term_detected(self):
        signals = _detect_signals("Processes PII including names and addresses")
        assert any("PII" in s for s in signals)

    def test_student_data_detected(self):
        signals = _detect_signals("Handles student data and academic records")
        assert any("PII" in s for s in signals)

    def test_patient_data_detected(self):
        signals = _detect_signals("Accesses patient data from the EHR system")
        assert any("PII" in s for s in signals)

    def test_employee_data_detected(self):
        signals = _detect_signals("Contains employee data and HR records")
        assert any("PII" in s for s in signals)

    def test_ssn_detected(self):
        signals = _detect_signals("Requires SSN for identity verification")
        assert any("PII" in s for s in signals)

    def test_national_id_detected(self):
        signals = _detect_signals("Validates national id documents")
        assert any("PII" in s for s in signals)


class TestHealthDetection:
    def test_medical_terms_detected(self):
        signals = _detect_signals("Provides medical diagnosis and treatment recommendations")
        assert any("HEALTH" in s for s in signals)

    def test_genomic_data_detected(self):
        signals = _detect_signals("Analyzes genomic and genetic data for risk scoring")
        assert any("HEALTH" in s for s in signals)

    def test_prescription_detected(self):
        signals = _detect_signals("Suggests prescription dosage adjustments")
        assert any("HEALTH" in s for s in signals)


class TestAgenticDetection:
    def test_agentic_pattern_detected(self):
        signals = _detect_signals("A multi-agent pipeline with computer use capabilities")
        assert any("AGENTIC" in s for s in signals)

    def test_orchestration_detected(self):
        signals = _detect_signals("Orchestrates subagents to complete autonomous workflows")
        assert any("AGENTIC" in s for s in signals)


class TestContentRisk:
    def test_harmful_content_domain_detected(self):
        signals = _detect_signals("Must filter harmful and toxic content before publishing")
        assert any("CONTENT RISK" in s for s in signals)


class TestBaseline:
    def test_no_signals_returns_default(self):
        signals = _detect_signals("A simple chatbot that answers FAQs about office hours")
        assert signals == ["no high-risk signals detected in automated pre-screening"]

    def test_empty_string(self):
        signals = _detect_signals("")
        assert signals == ["no high-risk signals detected in automated pre-screening"]


class TestPublicApi:
    def test_context_used_in_signal_detection(self):
        # System prompt is neutral but context mentions financial domain
        result = ai_safety_screen(
            system_prompt="You are a helpful assistant.",
            context="deployed for wire transfers and payment processing at a bank",
        )
        assert "FINANCIAL" in result

    def test_context_appears_in_output(self):
        result = ai_safety_screen("You are a helpful assistant.", context="customer support bot")
        assert "customer support bot" in result

    def test_no_context_no_context_block(self):
        result = ai_safety_screen("You are a helpful assistant.")
        assert "Deployment context:" not in result

    def test_output_contains_saf_002_header(self):
        result = ai_safety_screen("You are a helpful assistant.")
        assert "SAF-002" in result

    def test_output_contains_evaluation_framework(self):
        result = ai_safety_screen("You are a helpful assistant.")
        assert "CAPABILITY SCOPE" in result
        assert "AUTHORIZATION" in result
