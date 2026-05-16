"""ファイル取り込みユースケースのポート（入力）"""

from abc import ABC, abstractmethod

from app.usecase.dto.ingest_file_input import IngestFileInput
from app.usecase.dto.ingest_file_output import IngestFileOutput


class IngestFileUseCase(ABC):
    """ファイルを取り込むユースケース"""

    @abstractmethod
    def run(self, input: IngestFileInput) -> IngestFileOutput:
        pass
