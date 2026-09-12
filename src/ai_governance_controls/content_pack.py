"""Pinned offline governance content pack for Release A."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

PACK = {
    "manifest": {"packVersion": "2026-09-12", "schemaVersion": "1.0", "source": "aigovernance-reviewed-publication", "generatedAt": "2026-09-12T00:00:00Z", "editorialApproval": "reviewed-source-export"},
    "controls": {
        "AGT-019": {"slug": "ai-tool-plugin-supply-chain-risk-assessment", "title": "AI Tool and Plugin Supply Chain Risk Assessment", "objective": "Prevent compromised third-party tools and plugins from becoming a vector for agent manipulation or exfiltration.", "evidence_requirements": ["Authorized AI tool and plugin inventory with assessment records for each approved tool.", "Tool assessment template and completed assessments for production agents."]},
        "AGT-011": {"slug": "agent-oauth-scope-drift-detection", "title": "Agent OAuth Scope Drift Detection", "objective": "Detect token scopes exceeding their authorized baseline.", "evidence_requirements": ["Agent OAuth token inventory with authorized scope baselines.", "Scope drift detection configuration and alert history."]},
        "AGT-002": {"slug": "agent-prompt-injection-defense", "title": "Agent Prompt Injection Defense", "objective": "Separate untrusted content from tool authority.", "evidence_requirements": ["Architecture and controls separating untrusted content from tool execution authority."]},
        "AGT-006": {"slug": "agent-action-audit-trail", "title": "Agent Action Audit Trail", "objective": "Record agent tool actions with actor and outcome context.", "evidence_requirements": ["Tool-call logs containing tool, actor, target, correlation and outcome fields."]},
        "AGT-008": {"slug": "agent-environment-isolation", "title": "Agent Environment Isolation", "objective": "Restrict agents to approved tools and environments.", "evidence_requirements": ["Allowlist and network enforcement evidence for approved servers."]},
    },
    "kits": {"mcp-governance": {"artifacts": ["mcp-inventory", "mcp-intake", "mcp-credential-standard", "mcp-rereview-log"], "acceptanceCriteria": {"mcp-inventory": ["Every reachable MCP server is listed.", "Untrusted external content is identified.", "Only allowlisted servers are reachable."], "mcp-intake": ["Every exposed tool is listed.", "Untrusted-content separation is architectural.", "A signed-off decision exists before connection."], "mcp-credential-standard": ["No shared or standing personal credential.", "Credentials are scoped to tools, data and targets.", "Revocation has been tested."], "mcp-rereview-log": ["Capability, maintainer, publisher and version changes trigger review.", "New tools are denied by default until reviewed.", "Outcome and effective date are recorded."]}}},
    "references": [{"id": "mcp-kit", "source": "aigovernance.com", "url": "https://aigovernance.com/playbook/governing-mcp-servers-and-agent-tools", "status": "reviewed"}],
}

def content_pack() -> dict:
    payload = json.loads(json.dumps(PACK))
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["manifest"]["contentHash"] = "sha256:" + hashlib.sha256(canonical).hexdigest()
    return payload

def export_pack(path: str | Path | None = None) -> dict:
    pack = content_pack()
    if path:
        Path(path).write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")
    return pack

export_content_pack = export_pack

def resolve_control(control_id: str) -> dict | None:
    return content_pack()["controls"].get(control_id)
