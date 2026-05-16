"""アプリケーション設定"""

import os
from dataclasses import dataclass


@dataclass
class Settings:
    """アプリケーション設定"""

    s3_bucket: str
    s3_prefix: str = "analysis-results/daily"
    dataset_url: str = ""
    target_date: str = ""
    # Ingestion platform paths
    dropzone_path: str = "storage/dropzone"
    raw_path: str = "storage/raw"
    archive_path: str = "storage/archive"
    duckdb_path: str = "duckdb/analytics.duckdb"

    @classmethod
    def from_env(cls) -> "Settings":
        """環境変数から設定を読み込む"""
        return cls(
            s3_bucket=os.getenv("S3_BUCKET", "analysis-results"),
            s3_prefix=os.getenv("S3_PREFIX", "analysis-results/daily"),
            dataset_url=os.getenv("DATASET_URL", ""),
            target_date=os.getenv("TARGET_DATE", ""),
            dropzone_path=os.getenv("DROPZONE_PATH", "storage/dropzone"),
            raw_path=os.getenv("RAW_PATH", "storage/raw"),
            archive_path=os.getenv("ARCHIVE_PATH", "storage/archive"),
            duckdb_path=os.getenv("DUCKDB_PATH", "duckdb/analytics.duckdb"),
        )
