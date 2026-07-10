import os
import sqlite3
import json
from datetime import datetime, timezone


def _connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path, inputs_dir, outputs_dir):
    os.makedirs(inputs_dir, exist_ok=True)
    os.makedirs(outputs_dir, exist_ok=True)
    conn = _connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS calculation_history (
            calculation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            execution_time REAL,
            objective_function_cost REAL,
            status TEXT NOT NULL,
            input_json_path TEXT NOT NULL,
            output_json_path TEXT
        )
    """)
    conn.commit()
    conn.close()


def start_calculation(db_path, inputs_dir, input_data: dict) -> int:
    """Inserts a placeholder record to obtain calculation_id, writes the input
    file to inputs_dir/<calculation_id>.json, then fills in input_json_path."""
    conn = _connect(db_path)
    cur = conn.execute(
        "INSERT INTO calculation_history (timestamp, status, input_json_path) "
        "VALUES (?, ?, ?)",
        (datetime.now(timezone.utc).isoformat(), "processing", ""),
    )
    calculation_id = cur.lastrowid

    input_path = os.path.join(inputs_dir, f"{calculation_id}.json")
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(input_data, f, indent=2, ensure_ascii=False)

    conn.execute(
        "UPDATE calculation_history SET input_json_path = ? WHERE calculation_id = ?",
        (input_path, calculation_id),
    )
    conn.commit()
    conn.close()
    return calculation_id


def finish_success(db_path, outputs_dir, calculation_id: int, output_data: dict,
                    execution_time: float, objective_function_cost):
    output_path = os.path.join(outputs_dir, f"{calculation_id}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    conn = _connect(db_path)
    conn.execute(
        "UPDATE calculation_history SET output_json_path = ?, execution_time = ?, "
        "objective_function_cost = ?, status = ? WHERE calculation_id = ?",
        (output_path, execution_time, objective_function_cost, "success", calculation_id),
    )
    conn.commit()
    conn.close()


def finish_error(db_path, outputs_dir, calculation_id: int, error_message: str,
                  execution_time: float = None):
    output_path = os.path.join(outputs_dir, f"{calculation_id}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"error": error_message}, f, indent=2, ensure_ascii=False)

    conn = _connect(db_path)
    conn.execute(
        "UPDATE calculation_history SET output_json_path = ?, execution_time = ?, "
        "status = ? WHERE calculation_id = ?",
        (output_path, execution_time, "error", calculation_id),
    )
    conn.commit()
    conn.close()


def get_all_metadata(db_path) -> list:
    """Returns every calculation_history row as a dict with exactly the
    columns calculation_id, timestamp, execution_time, objective_function_cost,
    status, input_json_path, output_json_path. Does not read the input/output
    files themselves."""
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT calculation_id, timestamp, execution_time, objective_function_cost, "
        "status, input_json_path, output_json_path "
        "FROM calculation_history ORDER BY calculation_id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_metadata_by_id(db_path, calculation_id: int):
    """Returns the raw calculation_history row as a dict with exactly the
    columns calculation_id, timestamp, execution_time, objective_function_cost,
    status, input_json_path, output_json_path. Does not read the input/output
    files themselves."""
    conn = _connect(db_path)
    row = conn.execute(
        "SELECT calculation_id, timestamp, execution_time, objective_function_cost, "
        "status, input_json_path, output_json_path "
        "FROM calculation_history WHERE calculation_id = ?",
        (calculation_id,),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return dict(row)


def get_all(db_path) -> list:
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT calculation_id, timestamp, execution_time, objective_function_cost, status "
        "FROM calculation_history ORDER BY calculation_id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_by_id(db_path, calculation_id: int):
    conn = _connect(db_path)
    row = conn.execute(
        "SELECT calculation_id, timestamp, execution_time, objective_function_cost, "
        "status, input_json_path, output_json_path "
        "FROM calculation_history WHERE calculation_id = ?",
        (calculation_id,),
    ).fetchone()
    conn.close()
    if row is None:
        return None

    result = dict(row)

    input_data = None
    if result["input_json_path"] and os.path.exists(result["input_json_path"]):
        with open(result["input_json_path"], encoding="utf-8") as f:
            input_data = json.load(f)
    result["input"] = input_data

    output_data = None
    if result["output_json_path"] and os.path.exists(result["output_json_path"]):
        with open(result["output_json_path"], encoding="utf-8") as f:
            output_data = json.load(f)
    result["output"] = output_data

    return result