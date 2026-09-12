import json
import pytest
from ai_governance_controls.content_pack import content_pack, export_pack
from ai_governance_controls.release_a import (
    ai_control_review, ai_evidence_validate, ai_report_export,
    governance_get, governance_search,
)

def test_pack_is_pinned_and_resolves_mcp_controls():
    pack = content_pack()
    assert pack["manifest"]["contentHash"].startswith("sha256:")
    assert "AGT-019" in pack["controls"]
    assert "mcp-intake" in pack["kits"]["mcp-governance"]["artifacts"]

def test_search_and_get_are_bounded():
    assert governance_search("MCP tool supply chain")["results"]
    assert governance_get("AGT-019")["id"] == "AGT-019"
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        governance_search("")

def test_review_unknown_has_no_fake_evidence_and_export_preserves_refs():
    run = ai_control_review({"purpose": "agent"}, ["AGT-019"], system_id="demo")
    finding = run["findings"][0]
    assert finding["status"] == "unknown"
    assert not finding["evidenceReferenceIds"]
    assert ai_evidence_validate(run)["valid"]
    for fmt in ("json", "markdown", "csv"):
        exported = ai_report_export(run, fmt)
        assert exported["run_id"] == run["run_id"]
        assert exported["content"]

def test_supplied_evidence_reference_is_stable_and_provenanced():
    run = ai_control_review({}, ["AGT-019"], [{"id":"inventory", "type":"table", "content":"authorized inventory", "source":"operator", "capturedAt":"2026-09-12T00:00:00Z"}])
    assert run["evidence_references"][0]["basis"] == "supplied"
    assert run["evidence_references"][0]["contentHash"].startswith("sha256:")
    assert ai_evidence_validate(run)["valid"]

def test_invalid_supported_finding_is_rejected():
    run = ai_control_review({}, ["AGT-019"])
    run["findings"][0]["status"] = "supported"
    assert not ai_evidence_validate(run)["valid"]
