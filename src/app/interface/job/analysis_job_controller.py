"""分析Jobのコントローラー"""

from datetime import date
from app.usecase.ports.input.run_analysis_usecase import RunAnalysisUseCase
from app.usecase.dto.run_analysis_input import RunAnalysisInput
from app.domain.value_object.dataset import Dataset
from app.domain.value_object.target_date import TargetDate
from app.infrastructure.config.settings import Settings


def run_from_env(usecase: RunAnalysisUseCase) -> None:
    """
    環境変数から入力を受け取り分析を実行する

    Args:
        usecase: 分析実行ユースケース
    """
    settings = Settings.from_env()

    if not settings.dataset_url:
        raise ValueError("DATASET_URL environment variable is required")
    if not settings.target_date:
        raise ValueError("TARGET_DATE environment variable is required")

    # 入力データを構築
    input_data = RunAnalysisInput(
        dataset=Dataset(url=settings.dataset_url),
        target_date=TargetDate(value=date.fromisoformat(settings.target_date)),
    )

    # 分析を実行
    output = usecase.run(input_data)

    if not output.success:
        raise RuntimeError(f"Analysis failed: {output.message}")

    print(f"Analysis completed successfully. Result saved to: {output.result_path}")
