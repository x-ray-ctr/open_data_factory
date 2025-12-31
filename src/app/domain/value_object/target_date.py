"""対象日付の値オブジェクト"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class TargetDate:
    """対象日付を表す値オブジェクト"""

    value: date

    def __post_init__(self):
        if not isinstance(self.value, date):
            raise ValueError("TargetDate must be a date object")

    def __str__(self) -> str:
        return self.value.isoformat()
