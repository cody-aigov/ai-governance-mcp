"""Versioned, evidence-first contracts used by Release A tools."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

SCHEMA_VERSION = "1.0"
TOOL_VERSION = "0.2.0"
CONTENT_PACK_VERSION = "2026-09-12"

class EvidenceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=128)
    artifactId: str = Field(min_length=1, max_length=128)
    runId: str = Field(min_length=1, max_length=128)
    findingId: str = Field(min_length=1, max_length=128)
    source: str = Field(min_length=1, max_length=256)
    basis: Literal["supplied", "observed", "inferred"]
    contentHash: str | None = None
    locator: str | None = Field(default=None, max_length=256)
    url: str | None = None
    capturedAt: str | None = None
    importedAt: str | None = None

    @field_validator("url")
    @classmethod
    def safe_url(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith(("https://", "http://")):
            raise ValueError("url must use http or https")
        return value

class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    ruleId: str
    controlIds: list[str] = Field(default_factory=list)
    severity: Literal["low", "medium", "high", "critical"]
    status: Literal["supported", "gap", "unknown", "not_applicable"]
    observedFact: str
    interpretation: str
    remediation: str
    evidenceReferenceIds: list[str] = Field(default_factory=list)
    basis: Literal["configuration_observation", "supplied_document", "imported_execution", "model_inference"]

class Artifact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    type: str
    templateVersion: str
    content: str
    validation: Literal["valid", "invalid", "not_validated"]

class GovernanceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = SCHEMA_VERSION
    tool_version: str = TOOL_VERSION
    content_pack_version: str = CONTENT_PACK_VERSION
    run_id: str
    system_id: str
    created_at: str
    mode: Literal["deterministic_check", "guided_review", "imported_test_results"]
    completion: Literal["complete", "partial", "needs_input", "failed"]
    inputs: list[dict[str, Any]] = Field(default_factory=list)
    evidence_references: list[EvidenceReference] = Field(default_factory=list)
    scope: dict[str, Any] = Field(default_factory=dict)
    findings: list[Finding] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)

def new_run_id() -> str:
    return f"run_{uuid4().hex}"

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
