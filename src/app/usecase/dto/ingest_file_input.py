"""ファイル取り込みユースケースの入力DTO"""

from dataclasses import dataclass


@dataclass(frozen=True)
class IngestFileInput:
    """ファイル取り込みの入力"""

    file_path: str
    dataset_name: str
