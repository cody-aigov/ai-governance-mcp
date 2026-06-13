from mcp.server.fastmcp import FastMCP
from .controls.saf_001 import ai_safety_screen
from .controls.hoc_001 import ai_risk_classify
from .controls.saf_005 import ai_red_team

mcp = FastMCP("AI Governance Controls")

mcp.tool()(ai_safety_screen)
mcp.tool()(ai_risk_classify)
mcp.tool()(ai_red_team)


def main():
    mcp.run()
