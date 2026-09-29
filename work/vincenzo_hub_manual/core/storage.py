import json
import sqlite3
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_FILE = DATA_DIR / "workspace.json"
DATABASE_FILE = DATA_DIR / "va_hub.sqlite3"
UPLOADS_DIR = DATA_DIR / "uploads"

EMPTY_DATA = {
    "clients": [],
    "projects": [],
    "tasks": [],
    "payments": [],
    "expenses": [],
    "appointments": [],
    "documents": [],
    "gis_resources": [],
    "it_assets": [],
    "software_assets": [],
    "licenses": [],
    "social_snapshots": [],
    "quick_links": [
        {
            "id": "va-digital-site",
            "name": "Sito VA Digital",
            "url": "https://va-digital.it/",
            "category": "VA Digital",
        }
    ],
    "notes": [],
    "support_tickets": [],
    "leads": [],
    "quotes": [],
    "followups": [],
}


def _connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            collection TEXT NOT NULL,
            id TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            PRIMARY KEY (collection, id)
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_records_collection ON records(collection)"
    )
    return connection


def _normalise(data: dict) -> dict:
    clean = deepcopy(EMPTY_DATA)
    if isinstance(data, dict):
        for key in clean:
            if isinstance(data.get(key), list):
                clean[key] = data[key]
    return clean


def _database_is_empty(connection) -> bool:
    return connection.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 0


def _legacy_data() -> dict:
    if not DATA_FILE.exists():
        return deepcopy(EMPTY_DATA)
    try:
        return _normalise(json.loads(DATA_FILE.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        backup = DATA_FILE.with_name(
            f"workspace_corrotto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        DATA_FILE.replace(backup)
        return deepcopy(EMPTY_DATA)


def _insert_record(connection, collection: str, record: dict) -> None:
    record = dict(record)
    record_id = str(record.get("id") or uuid4().hex[:12])
    created_at = str(record.get("created_at") or datetime.now().isoformat(timespec="seconds"))
    record["id"] = record_id
    record["created_at"] = created_at
    connection.execute(
        """
        INSERT OR REPLACE INTO records(collection, id, payload, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            collection,
            record_id,
            json.dumps(record, ensure_ascii=False),
            created_at,
            record.get("updated_at"),
        ),
    )


def _ensure_database() -> None:
    with _connect() as connection:
        if not _database_is_empty(connection):
            return
        for collection, records in _legacy_data().items():
            for record in records:
                _insert_record(connection, collection, record)


def load_data() -> dict:
    _ensure_database()
    data = deepcopy(EMPTY_DATA)
    with _connect() as connection:
        rows = connection.execute(
            "SELECT collection, payload FROM records ORDER BY created_at, id"
        ).fetchall()
    for row in rows:
        if row["collection"] not in data:
            continue
        try:
            data[row["collection"]].append(json.loads(row["payload"]))
        except json.JSONDecodeError:
            continue
    return data


def save_data(data: dict) -> None:
    clean = _normalise(data)
    with _connect() as connection:
        connection.execute("DELETE FROM records")
        for collection, records in clean.items():
            for record in records:
                _insert_record(connection, collection, record)


def add_record(collection: str, values: dict) -> dict:
    if collection not in EMPTY_DATA:
        raise KeyError(f"Raccolta sconosciuta: {collection}")
    _ensure_database()
    record = {
        "id": uuid4().hex[:12],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        **values,
    }
    with _connect() as connection:
        _insert_record(connection, collection, record)
    return record


def update_record(collection: str, record_id: str, values: dict) -> bool:
    _ensure_database()
    with _connect() as connection:
        row = connection.execute(
            "SELECT payload FROM records WHERE collection = ? AND id = ?",
            (collection, record_id),
        ).fetchone()
        if row is None:
            return False
        record = json.loads(row["payload"])
        record.update(values)
        record["updated_at"] = datetime.now().isoformat(timespec="seconds")
        _insert_record(connection, collection, record)
    return True


def delete_record(collection: str, record_id: str) -> bool:
    _ensure_database()
    with _connect() as connection:
        cursor = connection.execute(
            "DELETE FROM records WHERE collection = ? AND id = ?",
            (collection, record_id),
        )
    return cursor.rowcount > 0


def backup_database() -> Path:
    _ensure_database()
    backup = DATA_DIR / f"backup_va_hub_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite3"
    with _connect() as source, sqlite3.connect(backup) as destination:
        source.backup(destination)
    return backup


def safe_filename(filename: str) -> str:
    name = Path(filename).name
    cleaned = "".join(char for char in name if char.isalnum() or char in "._- ").strip()
    return cleaned or f"file_{uuid4().hex[:8]}"


def save_upload(filename: str, content: bytes) -> Path:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    path = UPLOADS_DIR / safe_filename(filename)
    if path.exists():
        path = path.with_stem(f"{path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    path.write_bytes(content)
    return path
