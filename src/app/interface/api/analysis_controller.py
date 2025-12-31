"""分析APIのコントローラー"""

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.domain.value_object.dataset import Dataset
from app.domain.value_object.target_date import TargetDate
from app.infrastructure.k8s.job_launcher import JobLauncher
from app.interface.presenter.analysis_presenter import AnalysisPresenter
from app.usecase.dto.run_analysis_input import RunAnalysisInput
from app.usecase.ports.input.run_analysis_usecase import RunAnalysisUseCase

router = APIRouter(prefix="/analysis", tags=["analysis"])


# 依存関係の取得関数（main_api.pyで設定される）
def get_usecase() -> RunAnalysisUseCase:
    """ユースケースを取得する（main_api.pyで上書きされる）"""
    raise RuntimeError("UseCase not configured")


def get_job_launcher() -> JobLauncher:
    """Job起動器を取得する（main_api.pyで上書きされる）"""
    raise RuntimeError("JobLauncher not configured")


class AnalysisRequest(BaseModel):
    """分析リクエスト"""

    dataset_url: str
    target_date: str


class AnalysisResponse(BaseModel):
    """分析レスポンス"""

    success: bool
    result_path: str | None
    message: str


@router.post("/jobs", response_model=AnalysisResponse)
async def create_analysis_job(
    request: AnalysisRequest,
    job_launcher: JobLauncher = Depends(get_job_launcher),
) -> AnalysisResponse:
    """
    分析Jobを作成して起動する

    Args:
        request: 分析リクエスト
        usecase: 分析実行ユースケース
        job_launcher: Job起動器

    Returns:
        分析レスポンス
    """
    try:
        # Jobを起動
        job_id = job_launcher.launch_job(
            job_name=f"analysis-{request.target_date}",
            dataset_url=request.dataset_url,
            target_date=request.target_date,
        )

        return AnalysisResponse(
            success=True,
            result_path=None,
            message=f"Job {job_id} started",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/jobs", response_model=list[dict[str, Any]])
async def list_jobs(
    job_launcher: JobLauncher = Depends(get_job_launcher),
) -> list[dict[str, Any]]:
    """
    Jobの一覧を取得する

    Args:
        job_launcher: Job起動器

    Returns:
        Jobの状態のリスト
    """
    try:
        jobs = job_launcher.list_jobs()
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/jobs/{job_id}", response_model=dict[str, Any])
async def get_job_status(
    job_id: str,
    job_launcher: JobLauncher = Depends(get_job_launcher),
) -> dict[str, Any]:
    """
    Jobの状態を取得する

    Args:
        job_id: Job ID
        job_launcher: Job起動器

    Returns:
        Jobの状態
    """
    try:
        status = job_launcher.get_job_status(job_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/run", response_model=AnalysisResponse)
async def run_analysis(
    request: AnalysisRequest,
    usecase: RunAnalysisUseCase = Depends(get_usecase),
) -> AnalysisResponse:
    """
    分析を直接実行する（開発・テスト用）

    Args:
        request: 分析リクエスト
        usecase: 分析実行ユースケース

    Returns:
        分析レスポンス
    """
    try:
        # 入力データを構築
        input_data = RunAnalysisInput(
            dataset=Dataset(url=request.dataset_url),
            target_date=TargetDate(value=date.fromisoformat(request.target_date)),
        )

        # 分析を実行
        output = usecase.run(input_data)

        # プレゼンターで変換
        response_data = AnalysisPresenter.present(output)

        return AnalysisResponse(**response_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
