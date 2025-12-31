FROM python:3.11-slim

# uvのインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 依存関係をコピー
COPY pyproject.toml uv.lock* README.md ./

# ソースコードをコピー（依存関係インストールに必要）
COPY src/ ./src/

# 依存関係をインストール（システムにインストール）
RUN uv pip install --system -e .

# PYTHONPATHを設定
ENV PYTHONPATH=/app/src

# エントリーポイント
# API用: CMD ["python", "-m", "app.main_api"]
# Job用: CMD ["python", "-m", "app.main_job"]

