以下は、**今回確定した分析サービス（Polars × uv × K8s Job）**を
**クリーンアーキテクチャ（CA）に厳密準拠**させた **最終ディレクトリ構成案**です。

> ポイント
>
> * **依存は常に内向き**
> * **Job / API / Notebook は同じ UseCase を叩くだけ**
> * **Polars は Domain / UseCase に閉じ込める**

---

# クリーンアーキテクチャ最終ディレクトリ構成

```
polars-analysis-service/
├── pyproject.toml
├── uv.lock
├── Dockerfile
│
├── src/
│   └── app/
│
│       ├── domain/                # エンタープライズルール
│       │   ├── model/
│       │   │   └── analysis_result.py
│       │   │
│       │   ├── value_object/
│       │   │   ├── dataset.py
│       │   │   └── target_date.py
│       │   │
│       │   └── service/
│       │       └── analyze_service.py
│       │
│       ├── usecase/               # アプリケーションルール
│       │   ├── ports/
│       │   │   ├── input/
│       │   │   │   └── run_analysis_usecase.py
│       │   │   └── output/
│       │   │       ├── dataset_loader.py
│       │   │       └── result_repository.py
│       │   │
│       │   ├── interactor/
│       │   │   └── run_analysis_interactor.py
│       │   │
│       │   └── dto/
│       │       ├── run_analysis_input.py
│       │       └── run_analysis_output.py
│       │
│       ├── interface/             # Controller / Presenter
│       │   ├── api/
│       │   │   └── analysis_controller.py
│       │   │
│       │   ├── job/
│       │   │   └── analysis_job_controller.py
│       │   │
│       │   └── presenter/
│       │       └── analysis_presenter.py
│       │
│       ├── infrastructure/        # 外部世界
│       │   ├── loader/
│       │   │   └── http_dataset_loader.py
│       │   │
│       │   ├── repository/
│       │   │   └── s3_result_repository.py
│       │   │
│       │   ├── k8s/
│       │   │   └── job_launcher.py
│       │   │
│       │   └── config/
│       │       └── settings.py
│       │
│       ├── main_api.py             # FastAPI entrypoint
│       ├── main_job.py             # K8s Job entrypoint
│       │
│       └── wiring.py               # DI（composition root）
│
└── notebooks/
    └── integration.ipynb           # 仮設・最終削除
```

---

# レイヤ別の役割（厳密）

## 1. domain（最内層）

**責務**

* 分析の本質
* ビジネスルール
* Polars を使った *純粋変換*

```python
# domain/service/analyze_service.py
import polars as pl

def analyze(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df.group_by("category")
          .agg(pl.sum("value").alias("total"))
    )
```

❗ I/O・環境変数・S3 を一切知らない

---

## 2. usecase（アプリケーション層）

**責務**

* 処理の流れを定義
* Port を通して外界と通信

```python
# usecase/interactor/run_analysis_interactor.py
class RunAnalysisInteractor:
    def __init__(self, loader, repository, analyzer):
        self.loader = loader
        self.repository = repository
        self.analyzer = analyzer

    def run(self, input):
        df = self.loader.load(input.dataset)
        result = self.analyzer(df)
        self.repository.save(result, input.target_date)
```

---

## 3. interface（入口）

### API Controller

```python
# interface/api/analysis_controller.py
def post_analysis(request):
    return usecase.run(request)
```

### Job Controller

```python
# interface/job/analysis_job_controller.py
def run_from_env():
    input = build_input_from_env()
    usecase.run(input)
```

👉 **API / Job は同じ UseCase を呼ぶ**

---

## 4. infrastructure（外界）

* HTTP / S3 / K8s / Env
* 差し替え前提
* テストではモック

```python
# infrastructure/repository/s3_result_repository.py
def save(df, date):
    df.write_parquet(f"s3://analysis/{date}/result.parquet")
```

---

## 5. wiring（Composition Root）

```python
# wiring.py
def build_usecase():
    loader = HttpDatasetLoader()
    repo = S3ResultRepository()
    analyzer = analyze
    return RunAnalysisInteractor(loader, repo, analyzer)
```

**依存注入はここだけ**

---

# Notebook の位置付け（CA的に正しい）

```
Notebook
  ↓
Interface（仮Controller）
  ↓
UseCase
  ↓
Domain
```

Notebook は **Interface の代替**
＝ 消せるのが正しい。

---

# この構成の強さ

* Job / API / Notebook 完全共存
* Domain が最強にテストしやすい
* Polars 依存が外に漏れない
* 10年保つ構造

---

## 最終確認（YES なら設計完成）

* [ ] Notebook を削除しても動く
* [ ] Domain は Polars 以外を知らない
* [ ] Job と API が同じ UseCase を呼ぶ
* [ ] S3 / HTTP を差し替えられる

---

次の自然なステップは
**① この構成での最小実装コード一式**
**② Terraform + K8s への完全展開**

どちらに進めますか。
