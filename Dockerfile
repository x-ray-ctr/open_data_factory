FROM python:3.11-slim

# uvのインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 依存関係をコピー
COPY pyproject.toml uv.lock* ./

# 依存関係をインストール
RUN uv sync --frozen

# ソースコードをコピー
COPY src/ ./src/

# エントリーポイント
# API用: CMD ["uv", "run", "python", "-m", "app.main_api"]
# Job用: CMD ["uv", "run", "python", "-m", "app.main_job"]

