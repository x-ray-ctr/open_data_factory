"""取り込みレジストリのポート（出力）"""

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.model.ingestion_record import IngestionRecord


class IngestionRegistry(ABC):
    """ファイル取り込み履歴を管理するポート"""

    @abstractmethod
    def find_by_checksum(self, checksum: str) -> IngestionRecord | None:
        pass

    @abstractmethod
    def save(self, record: IngestionRecord) -> None:
        pass

    @abstractmethod
    def update_status(
        self,
        file_id: str,
        status: str,
        processed_at: datetime | None = None,
        schema_json: str | None = None,
        row_count: int | None = None,
    ) -> None:
        pass

    @abstractmethod
    def list_records(self) -> list[IngestionRecord]:
        pass
