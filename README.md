# AI Governance Controls

AI governance checks for MCP-compatible assistants. Use this server to review AI system prompts, classify deployment risk, plan adversarial testing, and inspect an MCP server configuration before connecting it to an agent.

Works in Claude Code, Cursor, Windsurf, Codex, and any other MCP-compatible tool.

Built on the control library from [AI Governance Institute](https://aigovernance.com).

---

## What the tools do

| Tool | Control | What it does |
|---|---|---|
| `ai_safety_screen` | [SAF-002](https://aigovernance.com/controls/ai-output-validation) | Reviews a system prompt and deployment context for actuator, financial, personal-data, health, content, agentic, and authorization signals. Returns a host-readable review framework. |
| `ai_risk_classify` | [HOC-001](https://aigovernance.com/controls/ai-system-risk-classification) | Pre-screens a deployment description for high-impact sectors, automation, oversight, consequential decisions, scale, and relevant governance references. |
| `ai_red_team` | [SEC-005](https://aigovernance.com/controls/adversarial-robustness-testing) | Produces a bounded test plan with stable attack categories and expected safe behavior. It does not run the tests. |
| `governance_search` | [Governance controls and playbooks](https://aigovernance.com/controls) | Finds matching controls and implementation-kit artifacts in the bundled, versioned library. |
| `governance_get` | [Governance controls and playbooks](https://aigovernance.com/controls) | Retrieves the exact objective, evidence requirements, or acceptance criteria for one control or kit artifact. |
| `ai_control_review` | [MCP governance playbook](https://aigovernance.com/playbook/governing-mcp-servers-and-agent-tools) | Compares supplied documents or artifact text with selected control evidence requirements. Missing evidence remains unknown; it is never treated as proof of safety or compliance. |
| `ai_mcp_review` | [MCP governance playbook](https://aigovernance.com/playbook/governing-mcp-servers-and-agent-tools) | Reviews a JSON MCP client configuration and captured `tools/list` manifest against an approved baseline. Reports new tools, removed tools, capability changes, mixed write/untrusted-content surfaces, and missing identity evidence. |
| `ai_evidence_validate` | [Audit-ready AI documentation](https://aigovernance.com/playbook/audit-ready-ai-documentation) | Checks report structure, control IDs, finding statuses, and evidence-reference links. |
| `ai_report_export` | [Audit-ready AI documentation](https://aigovernance.com/playbook/audit-ready-ai-documentation) | Exports a validated review as JSON, Markdown, or CSV while retaining stable finding and evidence-reference IDs. |
| `ai_risk_classify_v2` | [AI system risk classification](https://aigovernance.com/controls/ai-system-risk-classification) | Collects deployment facts, separates internal risk from jurisdiction applicability, and abstains when required facts are missing. |
| `ai_output_validate` | [AI output validation](https://aigovernance.com/controls/ai-output-validation) | Validates actual supplied output samples against required fields, types, and patterns. |
| `ai_red_team_v2` | [Adversarial robustness testing](https://aigovernance.com/controls/adversarial-robustness-testing) | Creates stable, versioned test cases with explicit pass criteria. Plans are marked `not_run` until a runner supplies results. |
| `ai_eval_review` | [Adversarial robustness testing](https://aigovernance.com/controls/adversarial-robustness-testing) | Imports test outcomes, reports coverage and inconclusive cases, and detects regressions against a prior equivalent run. |

The governance library is bundled with the package so the same package version uses the same control wording and evidence requirements on every run. `governance_search` and `governance_get` are the way to inspect that library; you do not need to load the entire catalog into your prompt.

## MCP configuration review

`ai_mcp_review` is a static review. Give it the configuration your MCP client would use, a captured `tools/list` response, and optionally the previously approved manifest. For example:

```json
{
  "config": {
    "mcpServers": {
      "github": {
        "command": "github-mcp-server",
        "args": ["--repository", "acme/project"]
      }
    },
    "metadata": {
      "identity": "svc-agent-github",
      "scopes": ["issues:read"]
    }
  },
  "tool_manifest": {
    "tools": [
      {
        "name": "list_issues",
        "description": "List issues in the approved repository",
        "annotations": {"readOnlyHint": true}
      }
    ]
  },
  "approved_baseline": {
    "tools": [
      {
        "name": "list_issues",
        "description": "List issues in the approved repository",
        "annotations": {"readOnlyHint": true}
      }
    ]
  }
}
```

The review parses those values as data. It does not launch the configured command, install a package, connect to an endpoint, read environment variables, or retrieve credentials. A tool description or `readOnlyHint` is treated as a claim to review, not as proof that the runtime enforces that behavior. The output identifies what still needs an owner, publisher verification, scope evidence, approval, or runtime testing.

---

## Installation

Add this block to your MCP configuration file. No global install required.

```json
{
  "mcpServers": {
    "ai-governance-controls": {
      "command": "uvx",
      "args": ["ai-governance-controls"]
    }
  }
}
```

**Configuration file locations:**
- Claude Code: `.claude/settings.json` (project) or `~/.claude/settings.json` (global)
- Cursor: `.cursor/mcp.json`
- Windsurf: `.windsurf/mcp.json`

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/) to be installed.

---

## Usage

Once installed, call the tools directly in conversation.

**Prompt safety screening (`ai_safety_screen`):**
> Screen this system prompt for safety risks: "You are a customer service assistant with access to customer accounts. You can initiate transfers up to $10,000 on behalf of verified customers."

**Deployment risk intake (`ai_risk_classify` or `ai_risk_classify_v2`):**
> Classify this deployment using structured facts: a clinical decision-support system used by an EU hospital, processing patient health data, with a clinician reviewing every recommendation before treatment.

**Red-team planning (`ai_red_team` or `ai_red_team_v2`):**
> Create 15 adversarial test cases for this healthcare assistant. It can read patient records and call a prescription tool. Include prompt injection, tool abuse, data extraction, and boundary-probing cases, but do not run them.

**MCP deployment review (`ai_mcp_review`):**
> Review this captured MCP configuration and `tools/list` manifest against the approved baseline. Identify added tools, permission changes, missing identity evidence, and any tool that combines write access with untrusted content.

**Find governance material (`governance_search`):**
> Search the governance library for controls and kit artifacts about MCP tool permissions and prompt injection.

**Retrieve one requirement (`governance_get`):**
> Retrieve the evidence requirements and acceptance criteria for AGT-019.

**Review supplied evidence (`ai_control_review`):**
> Review this server inventory and intake document against AGT-019 and identify which evidence requirements are supported, gaps, or still unknown.

**Validate an output sample (`ai_output_validate`):**
> Validate these representative JSON outputs against a rule requiring an object with `decision` and `reason` fields, and report every failing sample.

**Validate a governance bundle (`ai_evidence_validate`):**
> Validate this proposed governance report and flag supported findings that lack evidence references or reference unknown controls.

**Export a review (`ai_report_export`):**
> Export this validated review as JSON for systems integration, Markdown for a reviewer, or CSV for a tracking spreadsheet.

**Review imported evaluation results (`ai_eval_review`):**
> Import these red-team runner results, report pass/fail/inconclusive coverage, and compare them with the prior equivalent run for regressions.

---

## How it works

The prompt, risk, and red-team tools perform lightweight deterministic pre-screening and return a bounded framework for the host assistant to complete. The governance and MCP review tools perform deterministic checks against the bundled offline library and return structured findings. Evidence references record the artifact, hash, source, capture time, locator, and whether the basis was supplied, observed, or inferred.

These tools assist a governance review; they do not certify an organization, determine legal applicability conclusively, prove runtime enforcement, or execute a red-team plan. A generated test plan has status `not_run` until execution results are supplied by a separate runner. Missing facts and missing evidence are returned explicitly so a reviewer can decide what to collect next. No additional API key is required, and the server performs no automatic telemetry or remote inference.

The structured risk tool treats the EU AI Act and NIST AI RMF differently: EU results are potential applicability records that require legal review, while NIST is reported as voluntary framework guidance. The output validator checks the samples you provide; it does not generate samples or decide whether an output is substantively correct. Evaluation review distinguishes `pass`, `fail`, and `inconclusive`, and a model judge alone is not proof that a real-world side effect occurred.

## Documentation rule for future tools

Every new tool must be added to the “What the tools do” table with a direct link to the corresponding control, playbook, kit, or other reviewed content on [aigovernance.com](https://aigovernance.com). Its entry must describe the input, the output, and the boundary of what it does not prove. Every new tool must also have a concrete example in Usage. Keep internal release names out of these user-facing descriptions.

---

## Requirements

- Any MCP-compatible AI tool (Claude Code, Cursor, Windsurf, Codex, etc.)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

---

## License

Apache 2.0. See [LICENSE](LICENSE).

---

## More

Full control library, self-assessment wizard, and real-time regulatory alerts at [aigovernance.com](https://aigovernance.com).
