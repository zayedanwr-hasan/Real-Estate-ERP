import json
import os
from datetime import datetime
from typing import Any, Dict, List

from psycopg2 import sql
from psycopg2.extras import execute_values

from db_connection import get_connection

BACKUP_TABLES = ["accounts", "properties", "vendors", "vouchers", "ledger", "users"]


def _table_columns(cur, table_name: str) -> List[str]:
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'finance' AND table_name = %s
        ORDER BY ordinal_position
        """,
        (table_name,),
    )
    return [r[0] for r in cur.fetchall()]


def create_json_backup(backup_root: str, created_by: str = "system") -> str:
    os.makedirs(backup_root, exist_ok=True)
    file_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    file_path = os.path.join(backup_root, file_name)

    conn = get_connection()
    if not conn:
        raise RuntimeError("تعذر الاتصال بقاعدة البيانات")

    snapshot: Dict[str, Any] = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "created_by": created_by,
        "tables": {},
    }

    try:
        with conn:
            with conn.cursor() as cur:
                for table_name in BACKUP_TABLES:
                    cur.execute(sql.SQL("SELECT * FROM finance.{}").format(sql.Identifier(table_name)))
                    columns = [d[0] for d in cur.description] if cur.description else []
                    rows = cur.fetchall() or []
                    snapshot["tables"][table_name] = [
                        {columns[i]: row[i] for i in range(len(columns))}
                        for row in rows
                    ]
    finally:
        conn.close()

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2, default=str)

    return file_path


def restore_json_backup(file_path: str) -> Dict[str, int]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tables_data = data.get("tables") or {}
    if not isinstance(tables_data, dict):
        raise ValueError("ملف النسخة الاحتياطية غير صالح")

    conn = get_connection()
    if not conn:
        raise RuntimeError("تعذر الاتصال بقاعدة البيانات")

    restore_counts: Dict[str, int] = {}

    try:
        with conn:
            with conn.cursor() as cur:
                existing_tables = [t for t in BACKUP_TABLES if t in tables_data]
                if not existing_tables:
                    raise ValueError("الملف لا يحتوي على جداول قابلة للاستعادة")

                truncate_sql = sql.SQL(", ").join([
                    sql.SQL("finance.{}").format(sql.Identifier(t)) for t in reversed(existing_tables)
                ])
                cur.execute(sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(truncate_sql))

                for table_name in existing_tables:
                    rows = tables_data.get(table_name) or []
                    if not rows:
                        restore_counts[table_name] = 0
                        continue

                    table_cols = _table_columns(cur, table_name)
                    valid_cols = [c for c in table_cols if c in rows[0]]
                    if not valid_cols:
                        restore_counts[table_name] = 0
                        continue

                    values = [tuple(row.get(col) for col in valid_cols) for row in rows]
                    query = sql.SQL("INSERT INTO finance.{} ({}) VALUES %s").format(
                        sql.Identifier(table_name),
                        sql.SQL(", ").join(sql.Identifier(c) for c in valid_cols),
                    )
                    execute_values(cur, query, values)
                    restore_counts[table_name] = len(values)
    finally:
        conn.close()

    return restore_counts

