import os
import uvicorn
import pandas as pd
from sqlalchemy import create_engine, text
from mcp.server.fastmcp import FastMCP

HOST   = os.environ.get("DB_HOST", "ep-patient-field-aqean10y.c-8.us-east-1.pg.koyeb.app")
PORT   = int(os.environ.get("DB_PORT", 5432))
DBNAME = os.environ.get("DB_NAME", "koyebdb")
USER   = os.environ.get("DB_USER", "northwind_reader")
PASS   = os.environ.get("DB_PASS", "northwind_read_only")

engine = create_engine(f"postgresql+pg8000://{USER}:{PASS}@{HOST}:{PORT}/{DBNAME}")

mcp = FastMCP("Northwind", host="0.0.0.0")


@mcp.tool()
def list_tables() -> list[str]:
    """List all tables in the Northwind database."""
    sql = """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()
    return [r[0] for r in rows]


@mcp.tool()
def describe_table(table_name: str) -> list[dict]:
    """Return column names and data types for a table."""
    sql = """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = :t
        ORDER BY ordinal_position
    """
    with engine.connect() as conn:
        rows = conn.execute(text(sql), {"t": table_name}).fetchall()
    return [{"column": r[0], "type": r[1]} for r in rows]


@mcp.tool()
def run_sql(query: str) -> str:
    """Run a read-only SQL SELECT query and return results as CSV."""
    if not query.strip().upper().startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed.")
    df = pd.read_sql(query, engine)
    return df.to_csv(index=False)


if __name__ == "__main__":
    app = mcp.streamable_http_app()
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
