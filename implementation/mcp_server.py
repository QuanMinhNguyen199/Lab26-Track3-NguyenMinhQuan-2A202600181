import json
import sys
from typing import Optional
from fastmcp import FastMCP
from db import SQLiteAdapter, ValidationError
from init_db import create_database

mcp     = FastMCP("SQLite Lab MCP Server")
adapter = SQLiteAdapter()


def _err(e: Exception) -> str:
    return json.dumps({"error": str(e)})


# ── Tool: search ────────────────────────────────────────────────────────────
@mcp.tool(name="search")
def search(
    table: str,
    filters: Optional[dict] = None,
    columns: Optional[list] = None,
    limit: int = 20,
    offset: int = 0,
    order_by: Optional[str] = None,
    descending: bool = False,
) -> str:
    """Search rows in a table with optional filters, ordering, and pagination."""
    try:
        result = adapter.search(
            table, columns=columns, filters=filters,
            limit=limit, offset=offset,
            order_by=order_by, descending=descending,
        )
        return json.dumps(result)
    except ValidationError as e:
        return _err(e)


# ── Tool: insert ────────────────────────────────────────────────────────────
@mcp.tool(name="insert")
def insert(table: str, values: dict) -> str:
    """Insert a row into a table and return the inserted payload."""
    try:
        result = adapter.insert(table, values)
        return json.dumps(result)
    except ValidationError as e:
        return _err(e)


# ── Tool: aggregate ─────────────────────────────────────────────────────────
@mcp.tool(name="aggregate")
def aggregate(
    table: str,
    metric: str,
    column: Optional[str] = None,
    filters: Optional[dict] = None,
    group_by: Optional[str] = None,
) -> str:
    """Run COUNT / AVG / SUM / MIN / MAX with optional filters and GROUP BY."""
    try:
        result = adapter.aggregate(
            table, metric, column=column,
            filters=filters, group_by=group_by,
        )
        return json.dumps(result)
    except ValidationError as e:
        return _err(e)


# ── Resource: full schema ───────────────────────────────────────────────────
@mcp.resource("schema://database")
def database_schema() -> str:
    """Full schema snapshot for all tables."""
    schema = {}
    for table in adapter.list_tables():
        schema[table] = adapter.get_table_schema(table)
    return json.dumps(schema, indent=2)


# ── Resource: per-table schema ──────────────────────────────────────────────
@mcp.resource("schema://table/{table_name}")
def table_schema(table_name: str) -> str:
    """Schema for a single table."""
    try:
        return json.dumps(adapter.get_table_schema(table_name), indent=2)
    except ValidationError as e:
        return _err(e)


if __name__ == "__main__":
    create_database()
    # default: stdio (works with Claude Desktop & Inspector)
    # pass --http for HTTP transport demo / bonus
    transport = "http" if "--http" in sys.argv else "stdio"
    mcp.run(transport=transport)