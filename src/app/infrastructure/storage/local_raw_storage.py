"""ローカルRawレイヤーのParquetストレージ"""

from datetime import date
from pathlib import Path
from uuid import uuid4

import polars as pl

from app.usecase.ports.output.raw_storage import RawStorage


class LocalRawStorage(RawStorage):
    """raw/{dataset}/{year}/{month}/{day}/{uuid}.parquet に保存する"""

    def __init__(self, base_path: str):
        self._base = Path(base_path).resolve()

    def save(self, df: pl.DataFrame, dataset_name: str, target_date: date) -> str:
        partition = (
            self._base
            / dataset_name
            / str(target_date.year)
            / f"{target_date.month:02d}"
            / f"{target_date.day:02d}"
        )
        partition.mkdir(parents=True, exist_ok=True)
        file_path = partition / f"{uuid4().hex}.parquet"
        df.write_parquet(file_path)
        return str(file_path)
