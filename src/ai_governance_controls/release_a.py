"""Release A evidence review, search/get, validation and export tools."""
from __future__ import annotations
import csv, hashlib, io, json, re
from typing import Any
from .contracts import *
from .content_pack import content_pack, resolve_control

MAX_INPUT = 100_000

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
