"""ファイル取り込みユースケースの出力DTO"""

from dataclasses import dataclass


@dataclass(frozen=True)
class IngestFileOutput:
    """ファイル取り込みの結果"""

    file_id: str
    success: bool
    message: str
    raw_path: str = ""
    skipped: bool = False
