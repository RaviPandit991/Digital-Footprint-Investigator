"""SQLite database layer for cases, results, and entities."""
import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "dfi.db"
DB_PATH.parent.mkdir(exist_ok=True)

_lock = threading.Lock()
_conn = None


def _get_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, isolation_level=None)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA foreign_keys=ON")
    return _conn


def _now():
    return datetime.utcnow().isoformat(timespec="seconds")


def init_db():
    """Create schema if not exists."""
    conn = _get_conn()
    with _lock:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                primary_target TEXT,
                description TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                tool_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                tool_type TEXT NOT NULL,
                target TEXT NOT NULL,
                options_json TEXT DEFAULT '{}',
                status TEXT NOT NULL,
                result_json TEXT,
                error TEXT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                entity_type TEXT NOT NULL,
                value TEXT NOT NULL,
                source_tool_id TEXT,
                source_result_id INTEGER,
                first_seen TEXT NOT NULL,
                UNIQUE(case_id, entity_type, value),
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
                FOREIGN KEY (source_result_id) REFERENCES results(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_results_case ON results(case_id);
            CREATE INDEX IF NOT EXISTS idx_entities_case ON entities(case_id);
            CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(case_id, entity_type);
        """)


# ============ CASES ============

def create_case(name: str, primary_target: str = "", description: str = "") -> dict:
    conn = _get_conn()
    now = _now()
    with _lock:
        cur = conn.execute(
            "INSERT INTO cases (name, primary_target, description, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (name.strip() or f"Case {now}", primary_target.strip(), description.strip(), now, now)
        )
        case_id = cur.lastrowid
    return get_case(case_id)


def list_cases() -> list:
    conn = _get_conn()
    rows = conn.execute("""
        SELECT c.*,
            (SELECT COUNT(*) FROM results WHERE case_id = c.id) AS result_count,
            (SELECT COUNT(*) FROM entities WHERE case_id = c.id) AS entity_count
        FROM cases c
        ORDER BY c.updated_at DESC
    """).fetchall()
    return [dict(r) for r in rows]


def get_case(case_id: int) -> dict:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    if not row:
        return None
    case = dict(row)
    results = conn.execute(
        "SELECT * FROM results WHERE case_id = ? ORDER BY started_at DESC",
        (case_id,)
    ).fetchall()
    case["results"] = [_hydrate_result(dict(r)) for r in results]
    entities = conn.execute(
        "SELECT * FROM entities WHERE case_id = ? ORDER BY entity_type, value",
        (case_id,)
    ).fetchall()
    case["entities"] = [dict(e) for e in entities]
    return case


def _hydrate_result(r: dict) -> dict:
    try:
        r["result"] = json.loads(r.pop("result_json") or "null")
    except (json.JSONDecodeError, TypeError):
        r["result"] = None
    try:
        r["options"] = json.loads(r.pop("options_json") or "{}")
    except (json.JSONDecodeError, TypeError):
        r["options"] = {}
    return r


def rename_case(case_id: int, name: str = None, description: str = None) -> dict:
    conn = _get_conn()
    now = _now()
    with _lock:
        if name is not None:
            conn.execute("UPDATE cases SET name = ?, updated_at = ? WHERE id = ?",
                         (name.strip(), now, case_id))
        if description is not None:
            conn.execute("UPDATE cases SET description = ?, updated_at = ? WHERE id = ?",
                         (description.strip(), now, case_id))
    return get_case(case_id)


def delete_case(case_id: int) -> bool:
    conn = _get_conn()
    with _lock:
        cur = conn.execute("DELETE FROM cases WHERE id = ?", (case_id,))
    return cur.rowcount > 0


def _touch_case(case_id: int):
    conn = _get_conn()
    with _lock:
        conn.execute("UPDATE cases SET updated_at = ? WHERE id = ?", (_now(), case_id))


# ============ RESULTS ============

def save_result(case_id: int, tool_id: str, tool_name: str, tool_type: str,
                target: str, options: dict, status: str, result: dict = None,
                error: str = None) -> int:
    conn = _get_conn()
    now = _now()
    with _lock:
        cur = conn.execute("""
            INSERT INTO results (case_id, tool_id, tool_name, tool_type, target,
                                 options_json, status, result_json, error,
                                 started_at, finished_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (case_id, tool_id, tool_name, tool_type, target,
              json.dumps(options or {}), status,
              json.dumps(result) if result else None,
              error, now, now))
        result_id = cur.lastrowid
    _touch_case(case_id)
    return result_id


def delete_result(result_id: int) -> bool:
    conn = _get_conn()
    with _lock:
        cur = conn.execute("DELETE FROM results WHERE id = ?", (result_id,))
    return cur.rowcount > 0


# ============ ENTITIES ============

def add_entities(case_id: int, entities: list, source_tool_id: str,
                 source_result_id: int):
    """Bulk-insert entities. Ignores duplicates (via UNIQUE constraint)."""
    if not entities:
        return 0
    conn = _get_conn()
    now = _now()
    inserted = 0
    with _lock:
        for entity_type, value in entities:
            value = str(value).strip()
            if not value:
                continue
            try:
                conn.execute("""
                    INSERT INTO entities (case_id, entity_type, value,
                                          source_tool_id, source_result_id, first_seen)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (case_id, entity_type, value, source_tool_id,
                      source_result_id, now))
                inserted += 1
            except sqlite3.IntegrityError:
                pass  # duplicate
    return inserted


def get_entities(case_id: int, entity_type: str = None) -> list:
    conn = _get_conn()
    if entity_type:
        rows = conn.execute("""
            SELECT * FROM entities WHERE case_id = ? AND entity_type = ?
            ORDER BY value
        """, (case_id, entity_type)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM entities WHERE case_id = ?
            ORDER BY entity_type, value
        """, (case_id,)).fetchall()
    return [dict(r) for r in rows]


def search_entities(query: str, limit: int = 30) -> list:
    """Global search across all cases."""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT e.*, c.name AS case_name FROM entities e
        JOIN cases c ON e.case_id = c.id
        WHERE e.value LIKE ?
        ORDER BY e.first_seen DESC LIMIT ?
    """, (f"%{query}%", limit)).fetchall()
    return [dict(r) for r in rows]
