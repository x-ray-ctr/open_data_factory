"""Rawストレージのポート（出力）"""

from abc import ABC, abstractmethod
from datetime import date

import polars as pl


class RawStorage(ABC):
    """Rawレイヤーへ Parquet を保存するポート"""

    @abstractmethod
    def save(self, df: pl.DataFrame, dataset_name: str, target_date: date) -> str:
        """DataFrameをParquetとして保存し、保存先パスを返す"""
        pass
