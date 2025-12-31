"""FastAPIエントリーポイント"""
from fastapi import FastAPI
from app.interface.api.analysis_controller import router, get_usecase, get_job_launcher
from app.wiring import build_usecase, build_job_launcher
from app.infrastructure.config.settings import Settings


def create_app() -> FastAPI:
    """
    FastAPIアプリケーションを作成する
    
    Returns:
        FastAPIアプリケーション
    """
    app = FastAPI(title="Polars Analysis Service", version="0.1.0")
    
    # 設定を読み込む
    settings = Settings.from_env()
    
    # 依存関係を構築
    usecase = build_usecase(settings)
    job_launcher = build_job_launcher(settings)
    
    # 依存注入用の関数を上書き
    async def get_usecase_impl():
        return usecase
    
    async def get_job_launcher_impl():
        return job_launcher
    
    # グローバル関数を上書き
    import app.interface.api.analysis_controller as controller_module
    controller_module.get_usecase = get_usecase_impl
    controller_module.get_job_launcher = get_job_launcher_impl
    
    # ルーターを登録
    app.include_router(router)
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

