# AI Benchmark Rankings

主要AIモデルのベンチマークスコアを比較するランキングサイト。

**Live site**: https://reisun.github.io/ai-benchmark-rankings/

## Features

- 6つのベンチマーク指標でAIモデルを比較（Arena ELO, MMLU, HumanEval, SWE-bench, MATH, GPQA Diamond）
- ソート可能なランキングテーブル
- レーダーチャートによる視覚的比較（最大5モデル選択可能）
- ダークモードのモダンUI / レスポンシブ対応

## Data Pipeline

GitHub Actionsにより自動デプロイ:

- **トリガー**: `main`ブランチへのpush / 毎日09:00 JST / 手動実行
- **データ取得**: `scripts/fetch_data.py` が公開APIからベンチマークデータを取得
- **タイムスタンプ**: デプロイ時刻が「最終更新日時」としてサイトに反映

### 手動でデータ更新

`data/benchmarks.json` を直接編集してpushすることでも更新可能。

## Tech Stack

- HTML / CSS / Vanilla JS
- Chart.js (レーダーチャート)
- GitHub Actions (CI/CD)
- GitHub Pages (ホスティング)
