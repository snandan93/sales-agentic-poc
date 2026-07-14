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
def get_team_target(region: str | None = None, product: str | None = None, channel: str | None = None) -> dict:
    """Get team performance, optionally filtered by region, product, and channel."""
    return du.team_target_summary(region, product, channel)


@mcp.tool()
def get_top_performer(n: int = 1, region: str | None = None) -> list:
    """Get up to 100 top performers, optionally for one region."""
    return du.top_performer(n, region)


@mcp.tool()
def get_bottom_performer(n: int = 1, region: str | None = None) -> list:
    """Get the bottom N performing sales reps this month, ranked by % of target achieved. Useful for identifying who needs coaching support."""
    return du.bottom_performer(n, region)


@mcp.tool()
def get_average_performer() -> dict:
    """Get the team's average target/achieved/achievement %, and the rep(s) closest to that average (the 'typical' performer)."""
    return du.average_performer()


@mcp.tool()
def get_who_reached_target(page: int = 1, page_size: int = 25) -> dict:
    """Get a paginated list of reps who met target, sorted best first."""
    return du.who_reached_target(page, page_size)


@mcp.tool()
def get_who_missed_target(page: int = 1, page_size: int = 25) -> dict:
    """Get a paginated list of reps who missed target, sorted worst first."""
    return du.who_missed_target(page, page_size)


@mcp.tool()
def get_individual_performance(query: str, page: int = 1, page_size: int = 25) -> dict:
    """Find reps by partial name or exact employee code, with pagination."""
    return du.individual_performance(query, page, page_size)


@mcp.tool()
def get_region_breakdown() -> dict:
    """Get target vs achieved rolled up by region."""
    return du.region_breakdown()


@mcp.tool()
def get_dimension_breakdown(dimension: str = "region") -> dict:
    """Roll up results by region, product, channel, city, or manager."""
    return du.dimension_breakdown(dimension)


@mcp.tool()
def get_full_leaderboard(page: int = 1, page_size: int = 25) -> dict:
    """Get one leaderboard page; page size is capped at 100."""
    return du.full_leaderboard(page, page_size)


if __name__ == "__main__":
    mcp.run(transport="stdio")
