# AI Governance Controls

Automatable AI governance controls as MCP tools. Paste a system prompt, describe a deployment, or submit content for review and get a structured governance report back.

Works in Claude Code, Cursor, Windsurf, Codex, and any other MCP-compatible tool.

Built on the control library from [AI Governance Institute](https://aigovernance.com).

---

## Available controls

| Tool | Control | What it does |
|---|---|---|
| `ai_safety_screen` | [SAF-002](https://aigovernance.com/controls/ai-output-validation) | Screen a system prompt for safety risks: capability scope, authorization gaps, data exposure |
| `ai_risk_classify` | [HOC-001](https://aigovernance.com/controls/ai-system-risk-classification) | Classify an AI deployment's risk tier against EU AI Act and NIST AI RMF |
| `ai_red_team` | [SEC-005](https://aigovernance.com/controls/adversarial-robustness-testing) | Generate a red team runbook of adversarial test cases for a system prompt |
| `governance_search` / `governance_get` | Release A content pack | Search or retrieve versioned controls and kit criteria |
| `ai_control_review` | Release A evidence review | Check supplied artifacts against a selected control pack |
| `ai_evidence_validate` / `ai_report_export` | Release A evidence contract | Validate and export review bundles as JSON, Markdown, or CSV |

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

---

## How it works

The legacy tools run lightweight heuristic pre-screening and return a bounded evaluation framework to the host LLM. Release A tools perform deterministic checks against a pinned offline content pack and preserve evidence references through validation and export. Supplied commands are never executed, and no tool certifies compliance or claims test execution without imported execution evidence. No additional API keys required.

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
