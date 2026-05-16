"""FastAPIエントリーポイント"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.config.settings import Settings
from app.infrastructure.watcher.dropzone_watcher import DropzoneWatcher
from app.wiring import build_ingestion_components, build_job_launcher, build_usecase


def create_app() -> FastAPI:
    """FastAPIアプリケーションを作成する"""
    settings = Settings.from_env()

    usecase = build_usecase(settings)
    job_launcher = build_job_launcher(settings)
    ingest_interactor, registry, view_manager = build_ingestion_components(settings)
    watcher = DropzoneWatcher(ingest_interactor, settings.dropzone_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        watcher.start()
        yield
        watcher.stop()

    app = FastAPI(
        title="Open Data Factory",
        version="0.2.0",
        lifespan=lifespan,
    )

    from app.interface.api.analysis_controller import (
        get_job_launcher,
        get_usecase,
        router as analysis_router,
    )
    from app.interface.api.ingestion_controller import (
        get_ingest_usecase,
        get_registry,
        get_view_manager,
        router as ingestion_router,
    )

    app.dependency_overrides[get_usecase] = lambda: usecase
    app.dependency_overrides[get_job_launcher] = lambda: job_launcher
    app.dependency_overrides[get_ingest_usecase] = lambda: ingest_interactor
    app.dependency_overrides[get_registry] = lambda: registry
    app.dependency_overrides[get_view_manager] = lambda: view_manager

    app.include_router(analysis_router)
    app.include_router(ingestion_router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
