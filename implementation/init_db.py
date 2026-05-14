import sqlite3
import os
import sys
from db import DB_PATH

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS students (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT    NOT NULL,
    cohort  TEXT    NOT NULL,
    score   REAL    DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS courses (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    title   TEXT    NOT NULL,
    credits INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS enrollments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id),
    course_id  INTEGER NOT NULL REFERENCES courses(id),
    grade      TEXT
);
"""

SEED_SQL = """
INSERT INTO students (name, cohort, score) VALUES
    ('Alice',   'A1', 88.5),
    ('Bob',     'A1', 72.0),
    ('Charlie', 'B2', 91.0),
    ('Diana',   'B2', 65.5),
    ('Eve',     'A1', 79.0);

INSERT INTO courses (title, credits) VALUES
    ('Intro to AI',      3),
    ('Data Structures',  3),
    ('MCP Engineering',  2);

INSERT INTO enrollments (student_id, course_id, grade) VALUES
    (1, 1, 'A'), (1, 3, 'B'),
    (2, 1, 'B'), (2, 2, 'C'),
    (3, 2, 'A'), (3, 3, 'A'),
    (4, 1, 'C'),
    (5, 3, 'B');
"""

def create_database() -> str:
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_SQL)
    cur = conn.execute("SELECT COUNT(*) FROM students")
    if cur.fetchone()[0] == 0:
        conn.executescript(SEED_SQL)
    conn.commit()
    conn.close()
    print(f"✅ Database ready at: {DB_PATH}", file=sys.stderr)  # ← stderr
    return DB_PATH


if __name__ == "__main__":
    create_database()