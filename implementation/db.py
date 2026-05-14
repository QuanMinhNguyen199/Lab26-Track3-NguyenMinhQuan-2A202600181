import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "lab26.db")

ALLOWED_METRICS   = {"COUNT", "SUM", "AVG", "MIN", "MAX"}
ALLOWED_OPERATORS = {"=", "!=", ">", "<", ">=", "<=", "LIKE"}


class ValidationError(Exception):
    """Raised when a request cannot be safely executed."""


class SQLiteAdapter:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    # ── connection ──────────────────────────────────────────────────────────
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── introspection ───────────────────────────────────────────────────────
    def list_tables(self) -> list[str]:
        conn = self.connect()
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [r["name"] for r in cur.fetchall()]
        conn.close()
        return tables

    def get_table_schema(self, table: str) -> list[dict]:
        self._validate_identifier(table, self.list_tables(), "table")
        conn = self.connect()
        cur = conn.execute(f"PRAGMA table_info({table})")
        schema = [{"column": r["name"], "type": r["type"]} for r in cur.fetchall()]
        conn.close()
        return schema

    # ── validation helpers ──────────────────────────────────────────────────
    def _validate_identifier(self, name: str, allowed: list, kind: str):
        if name not in allowed:
            raise ValidationError(
                f"Unknown {kind} '{name}'. Allowed: {sorted(allowed)}"
            )

    def _validate_columns(self, table: str, columns: list[str]):
        valid = {c["column"] for c in self.get_table_schema(table)}
        for col in columns:
            if col not in valid:
                raise ValidationError(
                    f"Unknown column '{col}' in '{table}'. Valid: {sorted(valid)}"
                )

    # ── search ──────────────────────────────────────────────────────────────
    def search(
        self,
        table: str,
        columns: list[str] = None,
        filters: dict = None,
        limit: int = 20,
        offset: int = 0,
        order_by: str = None,
        descending: bool = False,
    ) -> dict:
        tables = self.list_tables()
        self._validate_identifier(table, tables, "table")

        if columns:
            self._validate_columns(table, columns)
            col_clause = ", ".join(columns)
        else:
            col_clause = "*"

        where_clause, values = self._build_where(table, filters)

        if order_by:
            self._validate_columns(table, [order_by])
            direction = "DESC" if descending else "ASC"
            order_clause = f"ORDER BY {order_by} {direction}"
        else:
            order_clause = ""

        query = f"SELECT {col_clause} FROM {table} {where_clause} {order_clause} LIMIT ? OFFSET ?"
        conn = self.connect()
        cur = conn.execute(query, values + [limit, offset])
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {"table": table, "count": len(rows), "rows": rows}

    def _build_where(self, table: str, filters: dict) -> tuple[str, list]:
        if not filters:
            return "", []
        clauses, values = [], []
        for col, condition in filters.items():
            # condition can be a plain value OR {"op": ">=", "value": 80}
            if isinstance(condition, dict):
                op = condition.get("op", "=").upper()
                val = condition["value"]
            else:
                op, val = "=", condition
            if op not in ALLOWED_OPERATORS:
                raise ValidationError(
                    f"Unsupported operator '{op}'. Allowed: {ALLOWED_OPERATORS}"
                )
            self._validate_columns(table, [col])
            clauses.append(f"{col} {op} ?")
            values.append(val)
        return "WHERE " + " AND ".join(clauses), values

    # ── insert ──────────────────────────────────────────────────────────────
    def insert(self, table: str, values: dict) -> dict:
        tables = self.list_tables()
        self._validate_identifier(table, tables, "table")
        if not values:
            raise ValidationError("'values' must not be empty.")
        self._validate_columns(table, list(values.keys()))

        cols        = ", ".join(values.keys())
        placeholders = ", ".join(["?"] * len(values))
        conn = self.connect()
        cur  = conn.execute(
            f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
            list(values.values()),
        )
        new_id = cur.lastrowid
        conn.commit()
        row = conn.execute(f"SELECT * FROM {table} WHERE rowid = ?", [new_id]).fetchone()
        conn.close()
        return {"inserted": dict(row), "id": new_id}

    # ── aggregate ───────────────────────────────────────────────────────────
    def aggregate(
        self,
        table: str,
        metric: str,
        column: str = None,
        filters: dict = None,
        group_by: str = None,
    ) -> dict:
        tables = self.list_tables()
        self._validate_identifier(table, tables, "table")

        metric = metric.upper()
        if metric not in ALLOWED_METRICS:
            raise ValidationError(
                f"Unsupported metric '{metric}'. Allowed: {ALLOWED_METRICS}"
            )

        # COUNT(*) is valid; everything else needs a column
        if column is None or column == "*":
            agg_target = "*"
        else:
            self._validate_columns(table, [column])
            agg_target = column

        select_clause = f"SELECT {metric}({agg_target}) AS value"

        if group_by:
            self._validate_columns(table, [group_by])
            select_clause = f"SELECT {group_by}, {metric}({agg_target}) AS value"

        where_clause, values = self._build_where(table, filters)
        group_clause = f"GROUP BY {group_by}" if group_by else ""

        query = f"{select_clause} FROM {table} {where_clause} {group_clause}"
        conn = self.connect()
        cur  = conn.execute(query, values)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {"table": table, "metric": metric, "column": agg_target, "rows": rows}