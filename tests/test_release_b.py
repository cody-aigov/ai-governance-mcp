import json
import pytest
from ai_governance_controls.release_a import ai_mcp_review

def test_mcp_review_detects_added_and_mixed_surface_without_execution():
    config={"mcpServers":{"demo":{"command":"this-must-never-run","args":["--token","SECRET"]}},"metadata":{"identity":"svc-demo","scopes":["issues:read"]}}
    baseline={"tools":[{"name":"list_issues","description":"read issues","annotations":{"readOnlyHint":True}}]}
    manifest={"tools":[{"name":"list_issues","description":"read issues","annotations":{"readOnlyHint":True}},{"name":"create_issue","description":"write issue from untrusted user document"}]}
    result=ai_mcp_review(config,manifest,baseline,publisher="Acme",owner="Owner",system_id="demo")
    assert "create_issue" in result["changes"]["added"]
    assert any(f["ruleId"] == "MCP-MIXED-SURFACE" for f in result["findings"])
    assert "SECRET" not in json.dumps(result)
    assert result["limitations"][0].startswith("No server startup")

def test_mcp_review_rejects_bad_and_oversized_formats():
    with pytest.raises(ValueError, match="UNSUPPORTED_FORMAT"):
        ai_mcp_review({"servers": {}}, {"tools": []})
    with pytest.raises(ValueError, match="UNSUPPORTED_FORMAT"):
        ai_mcp_review({"mcpServers": {}}, {"result": {"tools": []}})
    with pytest.raises(ValueError, match="LIMIT_EXCEEDED"):
        ai_mcp_review({"mcpServers": {}}, "x" * 100001)

def test_mcp_review_reports_missing_identity_evidence():
    result=ai_mcp_review({"mcpServers":{"demo":{"command":"ignored"}}},{"tools":[]})
    assert "Publisher identity and verification evidence" in result["missing_evidence"]
    assert "Dedicated identity and credential scope evidence" in result["missing_evidence"]
    assert result["intake_artifacts"]["rereview_trigger_log"]["triggers"]
