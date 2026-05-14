"""Smoke test — chạy trực tiếp để verify không cần server."""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from init_db import create_database
from db import SQLiteAdapter, ValidationError

create_database()
a = SQLiteAdapter()

def ok(label, result):
    print(f"✅ {label}")
    print("  ", result, "\n")

def expect_error(label, fn):
    try:
        fn()
        print(f"❌ {label} — should have raised!")
    except ValidationError as e:
        print(f"✅ {label} → error caught: {e}\n")

# 1. tool discovery
ok("list tables", a.list_tables())

# 2. search
ok("search all students",   a.search("students"))
ok("search cohort A1",      a.search("students", filters={"cohort": "A1"}))
ok("search score >= 80",    a.search("students", filters={"score": {"op": ">=", "value": 80}}))
ok("search ordered by score desc", a.search("students", order_by="score", descending=True))

# 3. insert
ok("insert student", a.insert("students", {"name": "Frank", "cohort": "C3", "score": 77.5}))

# 4. aggregate
ok("COUNT students",     a.aggregate("students", "COUNT", "*"))
ok("AVG score",          a.aggregate("students", "AVG", "score"))
ok("AVG score by cohort",a.aggregate("students", "AVG", "score", group_by="cohort"))

# 5. resources
ok("full schema",    a.list_tables())
ok("students schema",a.get_table_schema("students"))

# 6. error handling
expect_error("unknown table",    lambda: a.search("hackers"))
expect_error("unknown column",   lambda: a.search("students", columns=["password"]))
expect_error("bad operator",     lambda: a.search("students", filters={"score": {"op": "DROP", "value": 1}}))
expect_error("empty insert",     lambda: a.insert("students", {}))
expect_error("bad metric",       lambda: a.aggregate("students", "DROP"))

print("🎉 All verification checks passed!")