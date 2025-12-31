# Polars Analysis Service

クリーンアーキテクチャに基づいたPolars分析サービス（Polars × uv × K8s Job）

## 環境構築

### 前提条件

- Python 3.11以上
- [uv](https://github.com/astral-sh/uv) パッケージマネージャー

### uvのインストール

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# または Homebrew (macOS)
brew install uv
```

### 依存関係のインストール

```bash
# プロジェクトルートで実行
make install

# または直接実行
uv sync

# 開発用依存（Jupyter等）も含める場合
uv sync --extra dev
```

## 環境変数の設定

以下の環境変数を設定します：

```bash
export S3_BUCKET="your-analysis-bucket"
export S3_PREFIX="analysis-results/daily"  # オプション（デフォルト値あり）
export DATASET_URL="https://example.com/data.csv"  # Job実行時のみ必要
export TARGET_DATE="2024-01-01"  # Job実行時のみ必要（YYYY-MM-DD形式）
```

## 実行方法

### Makefileコマンド（推奨）

```bash
# APIサーバーを起動
make dev

# K8s Jobを実行（環境変数が必要）
make job

# Jupyter Notebookを起動
make notebook

# 依存関係をインストール
make install
```

### 1. APIサーバーの起動

FastAPIサーバーを起動します：

```bash
# Makefileを使用（推奨）
make dev

# または直接実行
uv run python -m app.main_api
```

サーバーは `http://localhost:8000` で起動します。

APIドキュメントは以下で確認できます：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 2. K8s Jobの実行

環境変数を設定してJobを実行します：

```bash
# 環境変数を設定
export DATASET_URL="https://example.com/data.csv"
export TARGET_DATE="2024-01-01"
export S3_BUCKET="your-analysis-bucket"

# Makefileを使用（推奨）
make job

# または直接実行
uv run python -m app.main_job
```

### 3. Dockerコンテナでの実行

#### APIサーバー

```bash
# イメージをビルド
docker build -t polars-service:latest .

# APIサーバーを起動
docker run -p 8000:8000 \
  -e S3_BUCKET="your-analysis-bucket" \
  -e S3_PREFIX="analysis-results/daily" \
  polars-service:latest \
  uv run python -m app.main_api
```

#### K8s Job

```bash
docker run \
  -e DATASET_URL="https://example.com/data.csv" \
  -e TARGET_DATE="2024-01-01" \
  -e S3_BUCKET="your-analysis-bucket" \
  polars-service:latest \
  uv run python -m app.main_job
```

## APIエンドポイント

### POST `/analysis/run`

分析を直接実行します（開発・テスト用）

**リクエスト例：**

```bash
curl -X POST "http://localhost:8000/analysis/run" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_url": "https://example.com/data.csv",
    "target_date": "2024-01-01"
  }'
```

**レスポンス例：**

```json
{
  "success": true,
  "result_path": "s3://your-analysis-bucket/analysis-results/daily/2024-01-01/result.parquet",
  "message": "Analysis completed successfully"
}
```

### POST `/analysis/jobs`

Kubernetes Jobを作成して起動します

**リクエスト例：**

```bash
curl -X POST "http://localhost:8000/analysis/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_url": "https://example.com/data.csv",
    "target_date": "2024-01-01"
  }'
```

### GET `/analysis/jobs/{job_id}`

Jobの状態を取得します

**リクエスト例：**

```bash
curl "http://localhost:8000/analysis/jobs/analysis-2024-01-01"
```

## 開発・テスト

### Notebookでの実行

開発・検証用のNotebookを使用できます：

```bash
# Makefileを使用（推奨）
make notebook

# または直接実行
uv run jupyter notebook notebooks/
```

`notebooks/integration.ipynb` が自動的に開きます。

**注意**: Notebookを実行するには、開発用依存をインストールする必要があります：
```bash
uv sync --extra dev
```

### ローカルテスト

```python
from app.wiring import build_usecase
from app.usecase.dto.run_analysis_input import RunAnalysisInput
from app.domain.value_object.dataset import Dataset
from app.domain.value_object.target_date import TargetDate
from datetime import date

# ユースケースを構築
usecase = build_usecase()

# 入力データを構築
input_data = RunAnalysisInput(
    dataset=Dataset(url="https://example.com/data.csv"),
    target_date=TargetDate(value=date.today()),
)

# 分析を実行
output = usecase.run(input_data)
print(output)
```

## プロジェクト構造

```
src/app/
├── domain/                # エンタープライズルール（最内層）
│   ├── model/            # ドメインモデル
│   ├── value_object/     # 値オブジェクト
│   └── service/          # ドメインサービス（Polarsロジック）
│
├── usecase/              # アプリケーションルール
│   ├── ports/            # ポート（インターフェース）
│   ├── interactor/       # インタラクター（ユースケース実装）
│   └── dto/              # データ転送オブジェクト
│
├── interface/            # 入口（Controller / Presenter）
│   ├── api/              # FastAPIコントローラー
│   ├── job/              # K8s Jobコントローラー
│   └── presenter/        # プレゼンター
│
├── infrastructure/       # 外部世界（実装）
│   ├── loader/           # データローダー
│   ├── repository/       # リポジトリ
│   ├── k8s/              # Kubernetes統合
│   └── config/           # 設定
│
├── wiring.py             # 依存注入（Composition Root）
├── main_api.py           # FastAPIエントリーポイント
└── main_job.py           # K8s Jobエントリーポイント
```

## Makefileコマンド一覧

| コマンド | 説明 |
|---------|------|
| `make install` | 依存関係をインストール |
| `make dev` | APIサーバーを起動 |
| `make job` | K8s Jobを実行（環境変数が必要） |
| `make notebook` | Jupyter Notebookを起動 |
| `make test` | テストを実行（今後実装予定） |
| `make lint` | リンターを実行（今後実装予定） |
| `make fmt` | コードフォーマット（今後実装予定） |

## 設計原則

- ✅ **依存は常に内向き**（Domain ← UseCase ← Interface ← Infrastructure）
- ✅ **Job / API / Notebook は同じ UseCase を呼ぶ**
- ✅ **Polars は Domain / UseCase に閉じ込める**
- ✅ **I/O・環境変数・S3 は Infrastructure 層に分離**

## ライセンス

MIT