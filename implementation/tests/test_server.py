"""
Automated tests for Lab 26 MCP server.
Run with: python -m pytest tests/test_server.py -v
"""
import json
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from init_db import create_database
from db import SQLiteAdapter, ValidationError

# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def db():
    """Initialize fresh DB once for the whole test session."""
    create_database()
    return SQLiteAdapter()

# ── Part 1: server foundation ─────────────────────────────────────────────────

def test_list_tables(db):
    tables = db.list_tables()
    assert "students"    in tables
    assert "courses"     in tables
    assert "enrollments" in tables

def test_get_table_schema(db):
    schema = db.get_table_schema("students")
    cols = [c["column"] for c in schema]
    assert "id"     in cols
    assert "name"   in cols
    assert "cohort" in cols
    assert "score"  in cols

# ── Part 2: search tool ───────────────────────────────────────────────────────

def test_search_all(db):
    result = db.search("students")
    assert result["count"] > 0
    assert isinstance(result["rows"], list)

def test_search_filter_exact(db):
    result = db.search("students", filters={"cohort": "A1"})
    for row in result["rows"]:
        assert row["cohort"] == "A1"

def test_search_filter_operator(db):
    result = db.search("students", filters={"score": {"op": ">=", "value": 80}})
    for row in result["rows"]:
        assert row["score"] >= 80

def test_search_order_by(db):
    result = db.search("students", order_by="score", descending=True)
    scores = [r["score"] for r in result["rows"]]
    assert scores == sorted(scores, reverse=True)

def test_search_pagination(db):
    all_rows  = db.search("students", limit=100)["rows"]
    page1     = db.search("students", limit=2, offset=0)["rows"]
    page2     = db.search("students", limit=2, offset=2)["rows"]
    assert len(page1) == 2
    assert page1[0]["id"] != page2[0]["id"]

def test_search_select_columns(db):
    result = db.search("students", columns=["name", "cohort"])
    for row in result["rows"]:
        assert "name"   in row
        assert "cohort" in row
        assert "score"  not in row

# ── Part 3: insert tool ───────────────────────────────────────────────────────

def test_insert_valid(db):
    result = db.insert("students", {"name": "TestUser", "cohort": "Z9", "score": 55.0})
    assert "inserted" in result
    assert result["inserted"]["name"] == "TestUser"

def test_insert_returns_id(db):
    result = db.insert("courses", {"title": "Test Course", "credits": 1})
    assert "id" in result
    assert result["id"] > 0

# ── Part 4: aggregate tool ────────────────────────────────────────────────────

def test_aggregate_count(db):
    result = db.aggregate("students", "COUNT", "*")
    assert result["rows"][0]["value"] > 0

def test_aggregate_avg(db):
    result = db.aggregate("students", "AVG", "score")
    avg = result["rows"][0]["value"]
    assert isinstance(avg, float)
    assert 0 < avg <= 100

def test_aggregate_group_by(db):
    result = db.aggregate("students", "AVG", "score", group_by="cohort")
    assert len(result["rows"]) > 1
    for row in result["rows"]:
        assert "cohort" in row
        assert "value"  in row

def test_aggregate_with_filter(db):
    result = db.aggregate(
        "students", "COUNT", "*",
        filters={"cohort": "A1"}
    )
    assert result["rows"][0]["value"] > 0

# ── Part 5: resources ─────────────────────────────────────────────────────────

def test_full_schema(db):
    schema = {t: db.get_table_schema(t) for t in db.list_tables()}
    assert "students"    in schema
    assert "courses"     in schema
    assert "enrollments" in schema

def test_table_schema_template(db):
    schema = db.get_table_schema("students")
    assert any(c["column"] == "score" for c in schema)

# ── Part 6: validation & error handling ───────────────────────────────────────

def test_error_unknown_table(db):
    with pytest.raises(ValidationError, match="Unknown table"):
        db.search("hackers")

def test_error_unknown_column(db):
    with pytest.raises(ValidationError, match="Unknown column"):
        db.search("students", columns=["password"])

def test_error_bad_operator(db):
    with pytest.raises(ValidationError, match="Unsupported operator"):
        db.search("students", filters={"score": {"op": "DROP", "value": 1}})

def test_error_empty_insert(db):
    with pytest.raises(ValidationError, match="must not be empty"):
        db.insert("students", {})

def test_error_bad_metric(db):
    with pytest.raises(ValidationError, match="Unsupported metric"):
        db.aggregate("students", "DROP_TABLE")

def test_error_unknown_table_insert(db):
    with pytest.raises(ValidationError, match="Unknown table"):
        db.insert("admin", {"username": "root"})