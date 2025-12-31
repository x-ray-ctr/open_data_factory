"""依存注入（Composition Root）"""

from app.infrastructure.config.settings import Settings
from app.infrastructure.k8s.job_launcher import JobLauncher
from app.infrastructure.loader.http_dataset_loader import HttpDatasetLoader
from app.infrastructure.repository.s3_result_repository import S3ResultRepository
from app.usecase.interactor.run_analysis_interactor import RunAnalysisInteractor
from app.usecase.ports.output.dataset_loader import DatasetLoader
from app.usecase.ports.output.result_repository import ResultRepository


def build_usecase(settings: Settings | None = None) -> RunAnalysisInteractor:
    """
    ユースケースを構築する

    Args:
        settings: アプリケーション設定（Noneの場合は環境変数から読み込む）

    Returns:
        分析実行ユースケース
    """
    if settings is None:
        settings = Settings.from_env()

    loader: DatasetLoader = HttpDatasetLoader()
    repository: ResultRepository = S3ResultRepository(settings)

    return RunAnalysisInteractor(
        loader=loader,
        repository=repository,
    )


def build_job_launcher(settings: Settings | None = None) -> JobLauncher:
    """
    Job起動器を構築する

    Args:
        settings: アプリケーション設定（Noneの場合は環境変数から読み込む）

    Returns:
        Job起動器
    """
    if settings is None:
        settings = Settings.from_env()

    return JobLauncher(settings)
