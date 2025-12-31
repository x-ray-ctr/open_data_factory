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
    
    @classmethod
    def from_env(cls) -> "Settings":
        """環境変数から設定を読み込む"""
        return cls(
            s3_bucket=os.getenv("S3_BUCKET", "analysis-results"),
            s3_prefix=os.getenv("S3_PREFIX", "analysis-results/daily"),
            dataset_url=os.getenv("DATASET_URL", ""),
            target_date=os.getenv("TARGET_DATE", ""),
        )

