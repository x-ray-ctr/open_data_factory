"""ローカルファイルのマルチフォーマットローダー"""

import json
from pathlib import Path

import polars as pl


class LocalFileLoader:
    """CSV / JSON / JSONL / Parquet を読み込むローダー"""

    SUPPORTED_SUFFIXES = {".csv", ".json", ".jsonl", ".ndjson", ".parquet"}

    def load(self, file_path: str) -> pl.DataFrame:
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".csv":
            return pl.read_csv(file_path)
        elif suffix == ".json":
            with open(file_path) as f:
                data = json.load(f)
            rows = data if isinstance(data, list) else [data]
            return pl.from_dicts(rows)
        elif suffix in {".jsonl", ".ndjson"}:
            return pl.read_ndjson(file_path)
        elif suffix == ".parquet":
            return pl.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix!r}")
