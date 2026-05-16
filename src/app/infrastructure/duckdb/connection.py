"""DuckDB接続管理"""

import threading
from pathlib import Path

import duckdb


class DuckDBConnection:
    """スレッドセーフなDuckDB接続ラッパー"""

    def __init__(self, db_path: str):
        path = Path(db_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = duckdb.connect(str(path))
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS ingestion_registry (
                file_id     TEXT PRIMARY KEY,
                dataset_name TEXT NOT NULL,
                file_name   TEXT NOT NULL,
                file_path   TEXT NOT NULL,
                checksum    TEXT NOT NULL UNIQUE,
                detected_at TIMESTAMP NOT NULL,
                processed_at TIMESTAMP,
                status      TEXT NOT NULL,
                schema_json TEXT,
                row_count   BIGINT
            )
        """)

    def execute(self, query: str, params: list | None = None):
        with self._lock:
            if params is not None:
                return self._conn.execute(query, params)
            return self._conn.execute(query)
