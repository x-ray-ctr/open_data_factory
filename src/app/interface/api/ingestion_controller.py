"""取り込みAPIのコントローラー"""

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.infrastructure.view.duckdb_view_manager import DuckDBViewManager
from app.usecase.dto.ingest_file_input import IngestFileInput
from app.usecase.ports.input.ingest_file_usecase import IngestFileUseCase
from app.usecase.ports.output.ingestion_registry import IngestionRegistry

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


def get_ingest_usecase() -> IngestFileUseCase:
    raise RuntimeError("IngestFileUseCase not configured")


def get_registry() -> IngestionRegistry:
    raise RuntimeError("IngestionRegistry not configured")


def get_view_manager() -> DuckDBViewManager:
    raise RuntimeError("DuckDBViewManager not configured")


class ManualIngestRequest(BaseModel):
    """手動取り込みリクエスト"""

    file_path: str
    dataset_name: str


@router.post("/ingest", response_model=dict[str, Any])
async def manual_ingest(
    request: ManualIngestRequest,
    usecase: IngestFileUseCase = Depends(get_ingest_usecase),
) -> dict[str, Any]:
    """ファイルを手動で取り込む（開発・テスト用）"""
    try:
        output = usecase.run(
            IngestFileInput(file_path=request.file_path, dataset_name=request.dataset_name)
        )
        return {
            "file_id": output.file_id,
            "success": output.success,
            "skipped": output.skipped,
            "raw_path": output.raw_path,
            "message": output.message,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/records", response_model=list[dict[str, Any]])
async def list_records(
    registry: IngestionRegistry = Depends(get_registry),
) -> list[dict[str, Any]]:
    """取り込み済みファイルの一覧を返す"""
    try:
        records = registry.list_records()
        return [asdict(r) for r in records]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/views", response_model=dict[str, list[str]])
async def list_views(
    view_manager: DuckDBViewManager = Depends(get_view_manager),
) -> dict[str, list[str]]:
    """DuckDB に登録された External View の一覧を返す"""
    try:
        return {"views": view_manager.list_views()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
