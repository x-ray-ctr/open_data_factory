"""K8s Jobエントリーポイント"""

from app.interface.job.analysis_job_controller import run_from_env
from app.wiring import build_usecase


def main():
    """Jobのメイン関数"""
    # ユースケースを構築
    usecase = build_usecase()

    # 環境変数から実行
    run_from_env(usecase)


if __name__ == "__main__":
    main()
