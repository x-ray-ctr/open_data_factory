"""分析実行の入力DTO"""

from dataclasses import dataclass

from app.domain.value_object.dataset import Dataset
from app.domain.value_object.target_date import TargetDate


@dataclass(frozen=True)
class RunAnalysisInput:
    """分析実行の入力データ"""

    dataset: Dataset
    target_date: TargetDate
