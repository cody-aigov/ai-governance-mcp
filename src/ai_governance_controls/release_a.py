"""Release A evidence review, search/get, validation and export tools."""
from __future__ import annotations
import csv, hashlib, io, json, re
from typing import Any
from .contracts import *
from .content_pack import content_pack, resolve_control

MAX_INPUT = 100_000
MAX_MANIFEST_TOOLS = 500

def _text(value: Any, name: str) -> str:
    if not isinstance(value, str): raise ValueError(f"INVALID_INPUT: {name} must be text")
    if not value.strip(): raise ValueError(f"INSUFFICIENT_EVIDENCE: {name} is empty")
    if len(value) > MAX_INPUT: raise ValueError(f"LIMIT_EXCEEDED: {name} exceeds {MAX_INPUT} characters")
    return value

def governance_search(query: str, domain: str | None = None, artifact_type: str | None = None, agent_relevance: bool | None = None) -> dict:
    query = _text(query, "query").lower()
    pack = content_pack(); hits = []
    for cid, c in pack["controls"].items():
        hay = " ".join([cid, c["title"], c["objective"], c["slug"]]).lower()
        score = sum(1 for token in query.split() if token in hay)
        if score: hits.append({"id": cid, "type": "control", "title": c["title"], "snippet": c["objective"], "score": score, "content_pack_version": pack["manifest"]["packVersion"]})
    for key in pack["kits"]["mcp-governance"]["artifacts"]:
        if query in key or any(t in key for t in query.split()): hits.append({"id": key, "type": "kit_artifact", "title": key, "snippet": "MCP governance kit artifact", "score": 1, "content_pack_version": pack["manifest"]["packVersion"]})
    return {"schema_version": SCHEMA_VERSION, "results": sorted(hits, key=lambda x: -x["score"])}

def governance_get(canonical_id: str, requested_sections: list[str] | None = None) -> dict:
    item = resolve_control(canonical_id)
    if item is None:
        if canonical_id in content_pack()["kits"]["mcp-governance"]["artifacts"]: return {"schema_version": SCHEMA_VERSION, "id": canonical_id, "type": "kit_artifact", "content_pack_version": CONTENT_PACK_VERSION, "sections": {"acceptanceCriteria": content_pack()["kits"]["mcp-governance"]["acceptanceCriteria"][canonical_id]}}
        raise ValueError("INVALID_INPUT: unknown canonical ID")
    sections = requested_sections or ["title", "objective", "evidence_requirements"]
    return {"schema_version": SCHEMA_VERSION, "id": canonical_id, "type": "control", "content_pack_version": CONTENT_PACK_VERSION, "sections": {s: item[s] for s in sections if s in item}}

def ai_control_review(system_profile: dict, selected_control_ids: list[str], supplied_artifacts: list[dict] | None = None, system_id: str = "system") -> dict:
    if not isinstance(system_profile, dict): raise ValueError("INVALID_INPUT: system_profile must be an object")
    if not selected_control_ids or any(resolve_control(x) is None for x in selected_control_ids): raise ValueError("INVALID_INPUT: selected controls must resolve in content pack")
    run_id = new_run_id(); refs=[]; findings=[]; missing=[]; artifacts=[]
    supplied_artifacts = supplied_artifacts or []
    for raw in supplied_artifacts:
        if not isinstance(raw, dict) or not isinstance(raw.get("id"), str) or not isinstance(raw.get("content"), str): raise ValueError("INVALID_INPUT: artifacts require id and content")
        content = raw["content"]
        if len(content) > MAX_INPUT: raise ValueError("LIMIT_EXCEEDED: artifact content")
        aid=raw["id"]; digest="sha256:"+hashlib.sha256(content.encode()).hexdigest(); artifacts.append(Artifact(id=aid,type=raw.get("type","document"),templateVersion=raw.get("templateVersion","1.0"),content=content,validation="not_validated"))
        ref=EvidenceReference(id=f"ev_{aid}",artifactId=aid,runId=run_id,findingId=f"finding_{aid}",source=raw.get("source","user-supplied artifact"),basis="supplied",contentHash=digest,locator=raw.get("locator"),url=raw.get("url"),capturedAt=raw.get("capturedAt")); refs.append(ref)
    if not supplied_artifacts:
        missing.append("At least one source artifact is required to support control findings.")
    for cid in selected_control_ids:
        ev=[r for r in refs if any(req.lower().split()[0] in (r.locator or r.artifactId).lower() for req in resolve_control(cid)["evidence_requirements"])]
        fid=f"finding_{cid.lower()}"
        if ev:
            findings.append(Finding(id=fid,ruleId=f"EVIDENCE-{cid}",controlIds=[cid],severity="medium",status="supported",observedFact=f"Supplied artifact evidence was provided for {cid}.",interpretation="Evidence is present for reviewer assessment; semantic effectiveness is not certified.",remediation="Reviewer should verify scope, authenticity and completeness.",evidenceReferenceIds=[r.id for r in ev],basis="supplied_document"))
        else:
            missing.extend(resolve_control(cid)["evidence_requirements"]); findings.append(Finding(id=fid,ruleId=f"EVIDENCE-{cid}",controlIds=[cid],severity="medium",status="unknown",observedFact="No matching supplied evidence was identified.",interpretation="The control cannot be marked supported without evidence.",remediation="Collect the listed evidence requirements.",basis="configuration_observation"))
    result=GovernanceResult(run_id=run_id,system_id=_text(system_id,"system_id"),created_at=now_iso(),mode="deterministic_check",completion="complete" if not missing else "partial",inputs=[{"id":a.id,"type":a.type,"hash":"sha256:"+hashlib.sha256(a.content.encode()).hexdigest()} for a in artifacts],evidence_references=refs,scope={"selected_controls":selected_control_ids},findings=findings,missing_evidence=sorted(set(missing)),provenance={"engine":"ai-governance-controls","rules":"pinned content pack"},limitations=["Static evidence presence checks do not prove runtime enforcement, authenticity or semantic effectiveness."])
    return result.model_dump()

def ai_evidence_validate(proposed_report: dict, source_input_ids: list[str] | None = None) -> dict:
    try: result=GovernanceResult.model_validate(proposed_report)
    except Exception as exc: return {"schema_version":SCHEMA_VERSION,"valid":False,"errors":[f"INVALID_INPUT: {exc}"]}
    ids={r.id for r in result.evidence_references}; errors=[]
    for f in result.findings:
        if f.status == "supported" and not f.evidenceReferenceIds: errors.append(f"{f.id}: supported finding lacks evidence reference")
        errors.extend(f"{f.id}: evidence reference {r} is unresolved" for r in f.evidenceReferenceIds if r not in ids)
        errors.extend(f"{f.id}: unknown control {c}" for c in f.controlIds if resolve_control(c) is None)
    return {"schema_version":SCHEMA_VERSION,"valid":not errors,"errors":errors,"run_id":result.run_id}

def ai_report_export(validated_run: dict, requested_format: str = "json") -> dict:
    result=GovernanceResult.model_validate(validated_run); check=ai_evidence_validate(result.model_dump())
    if not check["valid"]: raise ValueError("INVALID_INPUT: report failed validation")
    if requested_format == "json": content=json.dumps(result.model_dump(), indent=2)
    elif requested_format == "markdown": content="# Governance review\n\n"+"\n".join(f"- **{f.id}** ({f.status}): {f.interpretation}" for f in result.findings)
    elif requested_format == "csv":
        out=io.StringIO(); w=csv.writer(out); w.writerow(["finding_id","rule_id","control_ids","status","severity","evidence_reference_ids"])
        for f in result.findings: w.writerow([f.id,f.ruleId,";".join(f.controlIds),f.status,f.severity,";".join(f.evidenceReferenceIds)])
        content=out.getvalue()
    else: raise ValueError("INVALID_INPUT: requested_format must be json, markdown or csv")
    return {"schema_version":SCHEMA_VERSION,"format":requested_format,"run_id":result.run_id,"content":content}

def _parse_json_object(value: Any, name: str) -> dict:
    if isinstance(value, str):
        if len(value) > MAX_INPUT: raise ValueError(f"LIMIT_EXCEEDED: {name} exceeds {MAX_INPUT} characters")
        try: value = json.loads(value)
        except json.JSONDecodeError as exc: raise ValueError(f"INVALID_INPUT: {name} is not valid JSON: {exc.msg}") from exc
    if not isinstance(value, dict): raise ValueError(f"INVALID_INPUT: {name} must be a JSON object")
    return value

def _tools(manifest: Any) -> list[dict]:
    if not isinstance(manifest, dict): raise ValueError("INVALID_INPUT: tool_manifest must be an object")
    if "tools" not in manifest or not isinstance(manifest["tools"], list):
        raise ValueError("UNSUPPORTED_FORMAT: tool_manifest must be a captured tools/list response with a tools array")
    if len(manifest["tools"]) > MAX_MANIFEST_TOOLS: raise ValueError("LIMIT_EXCEEDED: tool_manifest contains too many tools")
    for tool in manifest["tools"]:
        if not isinstance(tool, dict) or not isinstance(tool.get("name"), str): raise ValueError("INVALID_INPUT: every manifest tool needs a name")
    return manifest["tools"]

def _secret_scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if re.search(r"(token|secret|password|api.?key|credential|authorization)", k, re.I) else _secret_scrub(v)) for k, v in value.items()}
    if isinstance(value, list): return [_secret_scrub(v) for v in value]
    return value

def _capabilities(tool: dict) -> dict:
    text = json.dumps(tool, sort_keys=True).lower()
    read_only = bool(tool.get("annotations", {}).get("readOnlyHint"))
    return {"readOnlyHint": read_only, "write": any(x in text for x in ("write", "create", "delete", "update", "send", "execute", "modify", "publish")), "external": any(x in text for x in ("http", "external", "network", "web", "github", "email")), "untrustedContent": any(x in text for x in ("untrusted", "user content", "document", "web page", "issue", "retrieved"))}

def ai_mcp_review(config: dict | str, tool_manifest: dict | str, approved_baseline: dict | str | None = None, system_id: str = "mcp-deployment", environment: str = "unknown", publisher: str | None = None, owner: str | None = None) -> dict:
    """Statically review MCP configuration and a captured tools/list manifest.

    The inputs are parsed as data. No command, endpoint, package, or environment
    variable referenced by the inputs is accessed.
    """
    cfg = _parse_json_object(config, "config")
    manifest = _parse_json_object(tool_manifest, "tool_manifest")
    tools = _tools(manifest)
    baseline = _parse_json_object(approved_baseline, "approved_baseline") if approved_baseline is not None else {"tools": []}
    baseline_tools = {t["name"]: t for t in _tools(baseline)}
    run_id = new_run_id(); refs=[]; findings=[]; missing=[]; proposed=[]
    configured = cfg.get("mcpServers")
    if configured is None:
        raise ValueError("UNSUPPORTED_FORMAT: config must use the mcpServers object format")
    if not isinstance(configured, dict): raise ValueError("INVALID_INPUT: config.mcpServers must be an object")
    for server_name, server_cfg in configured.items():
        if not isinstance(server_cfg, dict): raise ValueError("INVALID_INPUT: each mcpServers entry must be an object")
        # Deliberately inspect fields only; command/args are never launched.
    current = {t["name"]: t for t in tools}
    added = sorted(set(current) - set(baseline_tools)); removed = sorted(set(baseline_tools) - set(current)); changed = sorted(name for name in set(current) & set(baseline_tools) if _capabilities(current[name]) != _capabilities(baseline_tools[name]))
    if added: proposed.append("Review newly exposed tools before allowing them.")
    if changed: proposed.append("Re-review capability changes before deployment.")
    if not publisher: missing.append("Publisher identity and verification evidence")
    if not owner: missing.append("Named accountable owner")
    if not cfg.get("approved") and configured: findings.append({"id":"finding_allowlist","ruleId":"MCP-ALLOWLIST","status":"gap","severity":"high","observedFact":"Configuration does not declare approved status.","interpretation":"Static configuration cannot establish that this server is allowlisted.","remediation":"Record an approved decision and enforce the allowlist at the runtime boundary.","before":None,"after":_secret_scrub(cfg)})
    for name in added:
        findings.append({"id":f"finding_added_{name}","ruleId":"MCP-TOOL-ADDED","status":"gap","severity":"high","observedFact":f"Tool {name} is present in the captured manifest but absent from the approved baseline.","interpretation":"A new capability requires intake review.","remediation":"Deny by default until reviewed and explicitly allowlisted.","before":None,"after":_secret_scrub(current[name])})
    for name in changed:
        findings.append({"id":f"finding_changed_{name}","ruleId":"MCP-CAPABILITY-CHANGE","status":"gap","severity":"high","observedFact":f"Tool {name} capability indicators differ from the baseline.","interpretation":"The before/after capability surface changed.","remediation":"Re-review scopes, effects and untrusted-content handling.","before":_secret_scrub(baseline_tools[name]),"after":_secret_scrub(current[name])})
    for tool in tools:
        caps = _capabilities(tool)
        if caps["write"] and caps["untrustedContent"]: findings.append({"id":f"finding_surface_{tool['name']}","ruleId":"MCP-MIXED-SURFACE","status":"unknown","severity":"high","observedFact":f"Tool {tool['name']} appears to combine write/external effects with untrusted-content inputs.","interpretation":"Descriptions and annotations are claims, not proof of separation or enforcement.","remediation":"Document and test the enforcement boundary and human gate.","before":None,"after":_secret_scrub(tool)})
    if not any(x.get("identity") for x in (cfg.get("metadata", {}), {})): missing.append("Dedicated identity and credential scope evidence")
    findings_json=[Finding(id=f["id"],ruleId=f["ruleId"],controlIds=["AGT-019"],severity=f["severity"],status=f["status"],observedFact=f["observedFact"],interpretation=f["interpretation"],remediation=f["remediation"],basis="configuration_observation").model_dump() for f in findings]
    result=GovernanceResult(run_id=run_id,system_id=_text(system_id,"system_id"),created_at=now_iso(),mode="deterministic_check",completion="complete" if not missing and not findings else "partial",inputs=[{"type":"mcp_config","hash":"sha256:"+hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()},{"type":"tools_list_manifest","count":len(tools)}],scope={"environment":environment,"publisher":publisher,"owner":owner,"baseline_tools":sorted(baseline_tools),"current_tools":sorted(current)},findings=findings_json,missing_evidence=sorted(set(missing)),questions=["Where is the human approval gate enforced?"],provenance={"engine":"ai-governance-controls","mode":"static-only","rules":"pinned content pack"},limitations=["No server startup, package installation, endpoint connection, command launch or credential lookup was performed.","Tool descriptions and annotations are untrusted claims; runtime isolation and enforcement remain unverified."])
    out=result.model_dump(); out["changes"]={"added":added,"removed":removed,"changed":changed}; out["intake_artifacts"]={"server_inventory":{"server":system_id,"publisher":publisher,"owner":owner,"environment":environment,"tools":[{"name":t["name"],"capabilities":_capabilities(t)} for t in tools]},"intake_review":{"decision":"review_required","tool_count":len(tools),"missing_evidence":sorted(set(missing))},"credential_scoping":{"status":"unknown","identity":cfg.get("metadata",{}).get("identity"),"scopes":cfg.get("metadata",{}).get("scopes")},"rereview_trigger_log":{"triggers":["tool additions/removals","schema or capability changes","publisher or maintainer changes","version changes"],"proposed":proposed}}
    out["worked_example"]={"config":{"mcpServers":{"ai-governance-controls":{"command":"ai-governance-controls","args":[]}}},"manifest":{"tools":[{"name":"governance_get","description":"Read-only control lookup","annotations":{"readOnlyHint":True}}]},"result":"A captured manifest is reviewable without launching the server."}
    return out
