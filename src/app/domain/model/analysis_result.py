"""分析結果のドメインモデル"""

from dataclasses import dataclass

import polars as pl


@dataclass(frozen=True)
class AnalysisResult:
    """分析結果を表すドメインモデル"""

    data: pl.DataFrame

    def __post_init__(self):
        if not isinstance(self.data, pl.DataFrame):
            raise ValueError("AnalysisResult.data must be a polars DataFrame")
