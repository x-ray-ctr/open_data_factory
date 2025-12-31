# Polars Analysis Service

Clean Architecture based data analysis service with Polars, FastAPI, and Kubernetes Jobs.

## Quick Start

```bash
# Install dependencies
make install

# Start API server
make dev
```

Visit `http://localhost:8000/docs` for API documentation.

## Features

- **Clean Architecture** - Strict layer separation with dependency inversion
- **Polars Integration** - High-performance data processing
- **Multiple Entry Points** - API, K8s Job, and Notebook support
- **Type Safe** - Full type hints with Pydantic

## Usage

### API Server

```bash
make dev
```

### K8s Job

```bash
export DATASET_URL="https://example.com/data.csv"
export TARGET_DATE="2024-01-01"
export S3_BUCKET="your-bucket"

make job
```

### Development

```bash
# Install dev dependencies
uv sync --extra dev

# Start Jupyter
make notebook
```

## API

### Run Analysis

```bash
curl -X POST "http://localhost:8000/analysis/run" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_url": "https://example.com/data.csv",
    "target_date": "2024-01-01"
  }'
```

### Create Job

```bash
curl -X POST "http://localhost:8000/analysis/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_url": "https://example.com/data.csv",
    "target_date": "2024-01-01"
  }'
```

### Get Job Status

```bash
curl "http://localhost:8000/analysis/jobs/{job_id}"
```

## Environment Variables

```bash
S3_BUCKET=your-bucket              # Required
S3_PREFIX=analysis-results/daily   # Optional
DATASET_URL=https://...            # Required for jobs
TARGET_DATE=2024-01-01             # Required for jobs
```

## Architecture

```
src/app/
├── domain/          # Business logic (Polars)
├── usecase/         # Application rules
├── interface/       # Controllers (API/Job)
└── infrastructure/  # External adapters
```

**Design Principles:**
- Dependencies point inward (Domain ← UseCase ← Interface ← Infrastructure)
- Single UseCase shared across API, Job, and Notebook
- Polars isolated in Domain layer
- I/O operations in Infrastructure layer

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)

## Installation

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
make install
```

## Docker

```bash
# Build
docker build -t polars-service:latest .

# Run API
docker run -p 8000:8000 \
  -e S3_BUCKET=your-bucket \
  polars-service:latest \
  uv run python -m app.main_api

# Run Job
docker run \
  -e DATASET_URL=https://... \
  -e TARGET_DATE=2024-01-01 \
  -e S3_BUCKET=your-bucket \
  polars-service:latest \
  uv run python -m app.main_job
```

## Commands

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies |
| `make dev` | Start API server |
| `make job` | Run K8s job |
| `make notebook` | Start Jupyter |
| `make test` | Run tests |
| `make lint` | Run linter |
| `make fmt` | Format code |
| `make check` | Run lint and format |
| `make setup-k8s` | Setup Kubernetes cluster (kind) |
| `make build-image` | Build Docker image |
| `make load-image` | Build and load image to kind |
| `make clean-k8s` | Delete Kubernetes cluster |
| `make reset-k8s` | Reset Kubernetes cluster (delete and recreate) |
| `make clean-image` | Delete Docker image |

## Kubernetes

```bash
# Setup local Kubernetes cluster
make setup-k8s

# Build and load Docker image
make load-image

# Reset cluster (if needed)
make reset-k8s

# Create a Job via API
curl -X POST "http://localhost:8000/analysis/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_url": "https://example.com/data.csv",
    "target_date": "2024-01-01"
  }'
```

詳細なコマンドリファレンスは [KUBERNETES.md](./KUBERNETES.md) を参照してください。

## License

MIT
