from mcp.server.fastmcp import FastMCP
from .controls.saf_002 import ai_safety_screen
from .controls.hoc_001 import ai_risk_classify
from .controls.sec_005 import ai_red_team
from .release_a import governance_search, governance_get, ai_control_review, ai_evidence_validate, ai_report_export, ai_mcp_review

mcp = FastMCP("AI Governance Controls")

mcp.tool()(ai_safety_screen)
mcp.tool()(ai_risk_classify)
mcp.tool()(ai_red_team)
mcp.tool()(governance_search)
mcp.tool()(governance_get)
mcp.tool()(ai_control_review)
mcp.tool()(ai_evidence_validate)
mcp.tool()(ai_report_export)
mcp.tool()(ai_mcp_review)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
