"""依存注入（Composition Root）"""

from app.infrastructure.config.settings import Settings
from app.infrastructure.duckdb.connection import DuckDBConnection
from app.infrastructure.k8s.job_launcher import JobLauncher
from app.infrastructure.loader.http_dataset_loader import HttpDatasetLoader
from app.infrastructure.loader.local_file_loader import LocalFileLoader
from app.infrastructure.registry.duckdb_ingestion_registry import DuckDBIngestionRegistry
from app.infrastructure.repository.s3_result_repository import S3ResultRepository
from app.infrastructure.storage.local_raw_storage import LocalRawStorage
from app.infrastructure.view.duckdb_view_manager import DuckDBViewManager
from app.usecase.interactor.ingest_file_interactor import IngestFileInteractor
from app.usecase.interactor.run_analysis_interactor import RunAnalysisInteractor
from app.usecase.ports.output.dataset_loader import DatasetLoader
from app.usecase.ports.output.result_repository import ResultRepository


def build_ingestion_components(
    settings: Settings | None = None,
) -> tuple[IngestFileInteractor, DuckDBIngestionRegistry, DuckDBViewManager]:
    """取り込みパイプラインのコンポーネントを構築する"""
    if settings is None:
        settings = Settings.from_env()

    connection = DuckDBConnection(settings.duckdb_path)
    registry = DuckDBIngestionRegistry(connection)
    raw_storage = LocalRawStorage(settings.raw_path)
    view_manager = DuckDBViewManager(connection, settings.raw_path)
    loader = LocalFileLoader()

    interactor = IngestFileInteractor(
        loader=loader,
        registry=registry,
        raw_storage=raw_storage,
        view_manager=view_manager,
    )
    return interactor, registry, view_manager


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
