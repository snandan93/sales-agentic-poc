"""
mcp_server.py
--------------
MCP (Model Context Protocol) tool server for the Sales POC.

This is the "tools" layer: it exposes the sales dataset as a small set of
callable tools over the MCP protocol (stdio transport). It knows nothing
about LangGraph or Ollama — any MCP-compatible client can use it.

Run standalone for a quick manual check:
    python mcp_server.py
(it will just sit waiting for an MCP client on stdio — Ctrl+C to quit)

In this POC it's launched automatically as a subprocess by graph.py via
MultiServerMCPClient, so you normally don't run it by hand.
"""

from mcp.server.fastmcp import FastMCP
import data_utils as du

mcp = FastMCP("SalesDataServer")


@mcp.tool()
def get_team_target() -> dict:
    """Get this month's overall team sales target, total achieved, and % completion."""
    return du.team_target_summary()


@mcp.tool()
def get_top_performer(n: int = 1) -> list:
    """Get the top N performing sales reps this month, ranked by % of target achieved."""
    return du.top_performer(n)


@mcp.tool()
def get_bottom_performer(n: int = 1) -> list:
    """Get the bottom N performing sales reps this month, ranked by % of target achieved. Useful for identifying who needs coaching support."""
    return du.bottom_performer(n)


@mcp.tool()
def get_average_performer() -> dict:
    """Get the team's average target/achieved/achievement %, and the rep(s) closest to that average (the 'typical' performer)."""
    return du.average_performer()


@mcp.tool()
def get_who_reached_target() -> list:
    """List every sales rep who met or exceeded their target this month, sorted best first."""
    return du.who_reached_target()


@mcp.tool()
def get_who_missed_target() -> list:
    """List every sales rep who did NOT reach their target this month, sorted worst first."""
    return du.who_missed_target()


@mcp.tool()
def get_individual_performance(name: str) -> list:
    """Look up one sales rep's target, achieved and achievement % by name (partial name match is fine)."""
    return du.individual_performance(name)


@mcp.tool()
def get_region_breakdown() -> dict:
    """Get target vs achieved rolled up by region (North/South/East/West)."""
    return du.region_breakdown()


@mcp.tool()
def get_full_leaderboard() -> list:
    """Get every sales rep ranked from best to worst by achievement %."""
    return du.full_leaderboard()


if __name__ == "__main__":
    mcp.run(transport="stdio")
