"""DuckDBベースの取り込みレジストリ"""

from datetime import datetime

from app.domain.model.ingestion_record import IngestionRecord
from app.infrastructure.duckdb.connection import DuckDBConnection
from app.usecase.ports.output.ingestion_registry import IngestionRegistry


class DuckDBIngestionRegistry(IngestionRegistry):
    def __init__(self, connection: DuckDBConnection):
        self._db = connection

    def find_by_checksum(self, checksum: str) -> IngestionRecord | None:
        row = self._db.execute(
            "SELECT * FROM ingestion_registry WHERE checksum = ?", [checksum]
        ).fetchone()
        return _row_to_record(row) if row else None

    def save(self, record: IngestionRecord) -> None:
        self._db.execute(
            """INSERT INTO ingestion_registry
               (file_id, dataset_name, file_name, file_path, checksum,
                detected_at, processed_at, status, schema_json, row_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                record.file_id,
                record.dataset_name,
                record.file_name,
                record.file_path,
                record.checksum,
                record.detected_at,
                record.processed_at,
                record.status,
                record.schema_json,
                record.row_count,
            ],
        )

    def update_status(
        self,
        file_id: str,
        status: str,
        processed_at: datetime | None = None,
        schema_json: str | None = None,
        row_count: int | None = None,
    ) -> None:
        self._db.execute(
            """UPDATE ingestion_registry
               SET status = ?, processed_at = ?, schema_json = ?, row_count = ?
               WHERE file_id = ?""",
            [status, processed_at, schema_json, row_count, file_id],
        )

    def list_records(self) -> list[IngestionRecord]:
        rows = self._db.execute(
            "SELECT * FROM ingestion_registry ORDER BY detected_at DESC"
        ).fetchall()
        return [_row_to_record(row) for row in rows]


def _row_to_record(row: tuple) -> IngestionRecord:
    return IngestionRecord(
        file_id=row[0],
        dataset_name=row[1],
        file_name=row[2],
        file_path=row[3],
        checksum=row[4],
        detected_at=row[5],
        processed_at=row[6],
        status=row[7],
        schema_json=row[8],
        row_count=row[9],
    )
