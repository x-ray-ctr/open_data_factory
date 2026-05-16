"""取り込みレコードのドメインモデル"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class IngestionRecord:
    """ファイル取り込みの記録"""

    file_id: str
    dataset_name: str
    file_name: str
    file_path: str
    checksum: str
    detected_at: datetime
    status: str  # pending | processing | completed | failed
    processed_at: datetime | None = None
    schema_json: str | None = None
    row_count: int | None = None
