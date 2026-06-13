"""HOC-001: AI Risk Classification"""


_HIGH_RISK_SECTORS = {
    "biometric": "biometric identification",
    "education": "education and vocational training",
    "employment": "employment and worker management",
    "hiring": "employment and hiring decisions",
    "recruiting": "employment and recruiting",
    "essential services": "access to essential services",
    "benefits": "access to essential services / benefits",
    "housing": "access to housing",
    "welfare": "social welfare decisions",
    "law enforcement": "law enforcement",
    "criminal": "criminal justice",
    "migration": "migration and border control",
    "justice": "administration of justice",
    "judicial": "administration of justice",
    "parole": "administration of justice",
    "critical infrastructure": "critical infrastructure management",
    "healthcare": "healthcare and medical",
    "clinical": "healthcare and medical",
    "diagnostic": "healthcare and medical diagnostics",
    "financial": "financial services and credit",
    "credit": "financial services and credit",
    "lending": "financial services and credit",
    "underwriting": "financial services and underwriting",
    "insurance": "insurance underwriting",
    "claims": "insurance claims adjudication",
    "scoring": "consequential scoring system",
}

_AUTOMATION_TERMS = [
    "fully automated", "autonomous", "no human review", "without human",
    "automatically", "auto-approve", "auto-deny", "auto-generate",
    # from HOC controls
    "automated decision", "automated decisioning", "automated scoring",
    "without oversight", "no oversight", "unsupervised",
    "auto-accept", "auto-reject", "auto-triage",
]

_OVERSIGHT_TERMS = [
    "human review", "human oversight", "human in the loop", "approval required",
    "reviewed by", "supervised", "audited", "monitored",
    # HOC-002: approval gates
    "human approval", "approval gate", "approval workflow", "review sla",
    # HOC-003: review workflow vocabulary
    "review workflow", "acceptance criteria", "escalation",
    # HOC-004: automation bias detection
    "override rate", "calibration",
    # HOC-005: reviewer competency
    "qualified reviewer", "competency", "certified",
    # HOC-006: override logging
    "override procedure", "reason code",
    # general
    "hitl", "human-in-the-loop",
]

_GDPR_TERMS = [
    "eu", "european", "gdpr", "data subject", "right to erasure",
    "right to access", "controller", "processor",
    # regulatory references cited across HOC controls
    "eu ai act", "article 26", "nist ai rmf", "right to explanation",
    "right to human review", "conformity assessment",
]

_SCALE_TERMS = [
    "millions", "large-scale", "mass", "widespread", "population",
    "national", "global", "enterprise-wide",
    # from HOC controls
    "high-volume", "bulk", "batch", "at scale", "organization-wide",
]

# HOC-002: irreversible or high-stakes decisions that require an approval gate
_CONSEQUENTIAL_TERMS = [
    "irreversible", "consequential", "high-stakes", "high stakes",
    "credit decision", "hiring decision", "termination", "denial",
    "rejection", "foreclosure", "eviction", "suspension", "ban",
    "eligibility", "disqualify", "blacklist",
]


def _classify_signals(text: str) -> tuple[list[str], list[str]]:
    t = text.lower()
    risk_signals = []
    reg_signals = []

    matched_sectors = [label for term, label in _HIGH_RISK_SECTORS.items() if term in t]
    if matched_sectors:
        risk_signals.append(f"HIGH-RISK SECTOR: {', '.join(matched_sectors)}")
        reg_signals.append("EU AI Act (Annex III high-risk classification likely)")

    automation = [w for w in _AUTOMATION_TERMS if w in t]
    if automation:
        risk_signals.append(f"AUTOMATION: high automation level detected ({', '.join(automation[:2])})")

    oversight = [w for w in _OVERSIGHT_TERMS if w in t]
    if not oversight and automation:
        risk_signals.append("OVERSIGHT GAP: automated decision-making without explicit human oversight")
    elif oversight:
        risk_signals.append(f"OVERSIGHT: human oversight mechanisms mentioned ({', '.join(oversight[:2])})")

    consequential = [w for w in _CONSEQUENTIAL_TERMS if w in t]
    if consequential:
        risk_signals.append(f"CONSEQUENTIAL: irreversible or high-stakes decisions detected ({', '.join(consequential[:3])})")
        reg_signals.append("EU AI Act Art. 26 (human oversight for high-risk systems)")
        if not oversight:
            risk_signals.append("APPROVAL GATE GAP: consequential decisions without documented human approval gate (HOC-002)")

    gdpr = [w for w in _GDPR_TERMS if w in t]
    if gdpr:
        reg_signals.append("EU AI Act, GDPR")

    scale = [w for w in _SCALE_TERMS if w in t]
    if scale:
        risk_signals.append(f"SCALE: large-scale deployment indicated ({', '.join(scale[:2])})")
        reg_signals.append("NIST AI RMF (Govern 1.1: organizational risk tolerance)")

    if not reg_signals:
        reg_signals.append("NIST AI RMF (baseline)")

    return (
        risk_signals or ["no high-risk signals detected in automated pre-screening"],
        list(dict.fromkeys(reg_signals)),
    )


def ai_risk_classify(deployment_description: str) -> str:
    """
    Classify an AI deployment's risk tier and applicable regulations (HOC-001).

    Evaluates a deployment description against the HOC-001 risk classification
    control, referencing EU AI Act risk tiers and NIST AI RMF. Returns a
    structured analysis framework for the host to complete.

    Args:
        deployment_description: Description of the AI system and how it is deployed.
            Include: what the system does, who uses it, what decisions it influences,
            what data it processes, and any human oversight in place.
    """
    risk_signals, reg_signals = _classify_signals(deployment_description)
    risk_block = "\n".join(f"  - {s}" for s in risk_signals)
    reg_block = ", ".join(reg_signals)

    return f"""RISK CLASSIFICATION ANALYSIS (HOC-001)
{"=" * 60}
Deployment description:
{deployment_description}

Automated pre-screening signals:
{risk_block}

Potentially applicable frameworks: {reg_block}

Classification framework -- assess the deployment against each dimension:

1. RISK TIER (EU AI Act)
   - Unacceptable risk: prohibited (social scoring, real-time biometric surveillance)
   - High risk: Annex III sectors (biometric, employment, education, law enforcement,
     essential services, critical infrastructure, migration, justice)
   - Limited risk: transparency obligations (chatbots must disclose AI nature)
   - Minimal risk: no mandatory requirements

2. AUTOMATION AND HUMAN OVERSIGHT
   Is this fully automated, human-assisted, or human-in-the-loop? For consequential
   decisions, is there a meaningful override mechanism? Who is accountable?

3. AFFECTED POPULATIONS
   Who is subject to decisions made by this system? Are they vulnerable groups
   (minors, job applicants, loan seekers, patients)? What is the scale?

4. DATA SENSITIVITY
   What data does the system process? Does it involve special category data under
   GDPR (health, biometric, racial/ethnic origin, political opinions)?

5. APPLICABLE OBLIGATIONS
   Based on the above, list the specific compliance obligations: conformity
   assessment, technical documentation, logging, human oversight requirements,
   transparency notices, registration in the EU AI Act database.

Required output format (follow exactly):

Risk tier: [unacceptable / high / limited / minimal]
NIST AI RMF profile: [govern / map / measure / manage -- which functions apply most]

Applicable regulations:
- [regulation + specific obligation]
- [...]

Key risk factors:
- [specific factor from the deployment description]
- [...]

Recommended next steps:
- [specific action for this deployment]
- [...]

Produce the risk classification report for the deployment described above.
"""
