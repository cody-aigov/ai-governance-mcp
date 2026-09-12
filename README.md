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
| `governance_search` | Governance library search | Finds matching governance controls and MCP implementation-kit artifacts in the bundled, versioned library. |
| `governance_get` | Governance library lookup | Retrieves the exact objective, evidence requirements, or acceptance criteria for one control or kit artifact. |
| `ai_control_review` | Evidence review | Compares supplied documents or artifact text with selected control evidence requirements. Missing evidence remains unknown; it is never treated as proof of safety or compliance. |
| `ai_mcp_review` | MCP deployment review | Reviews a JSON MCP client configuration and a previously captured `tools/list` manifest against an approved baseline. Reports new tools, removed tools, capability changes, mixed write/untrusted-content surfaces, and missing identity evidence. |
| `ai_evidence_validate` | Evidence bundle validation | Checks report structure, control IDs, finding statuses, and evidence-reference links. |
| `ai_report_export` | Evidence bundle export | Exports a validated review as JSON, Markdown, or CSV while retaining stable finding and evidence-reference IDs. |

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

**Safety screening:**
> Screen this system prompt for safety risks: "You are a customer service assistant with access to customer accounts. You can initiate transfers up to $10,000 on behalf of verified customers."

**Risk classification:**
> Classify the risk tier for this deployment: "An automated resume screening system used by a Fortune 500 company to shortlist job applicants. No human reviews the shortlist before candidates are rejected."

**Red teaming:**
> Red team this system prompt with 15 test cases: "You are a helpful assistant for a healthcare provider. You have access to patient records and can answer questions about their medical history."

**MCP review:**
> Review this captured MCP configuration and tools/list manifest against the approved baseline. Identify added tools, permission changes, missing identity evidence, and any tool that combines write access with untrusted content.

---

## How it works

The prompt, risk, and red-team tools perform lightweight deterministic pre-screening and return a bounded framework for the host assistant to complete. The governance and MCP review tools perform deterministic checks against the bundled offline library and return structured findings. Evidence references record the artifact, hash, source, capture time, locator, and whether the basis was supplied, observed, or inferred.

These tools assist a governance review; they do not certify an organization, determine legal applicability conclusively, prove runtime enforcement, or execute a red-team plan. A generated test plan has status `not_run` until execution results are supplied by a separate runner. Missing facts and missing evidence are returned explicitly so a reviewer can decide what to collect next. No additional API key is required, and the server performs no automatic telemetry or remote inference.

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
