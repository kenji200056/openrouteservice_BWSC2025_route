# OpenRouteService Route Generator

高精度なルート生成ツール。OpenRouteServiceを使用してオーストラリアの長距離ルートを100メートル間隔で分析し、緯度・経度・標高データをCSVに出力、インタラクティブマップを生成。

## 特徴

- 🗺️ OpenRouteService APIを使用した高精度ルートプランニング
- 📊 100メートル間隔での詳細なルートデータ生成
- 🏔️ 標高データを含む完全なルート分析
- 📁 CSV形式でのデータエクスポート
- 🌐 Foliumを使用したインタラクティブマップ生成
- 🚗 オーストラリア横断ルート対応

## セットアップ

### 1. 仮想環境の作成と有効化

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. APIキーの設定

1. [OpenRouteService](https://openrouteservice.org/dev/#/signup)で無料APIキーを取得
2. `.env`ファイルを編集:

```bash
ORS_API_KEY=your_api_key_here
```

## 使用方法

基本的な使用:
```bash
python main.py --out route.csv --html route.html
```

オプション:
- `--api-key`: APIキー（環境変数の代わりに直接指定）
- `--out`: 出力CSVファイル名（デフォルト: route.csv）
- `--html`: HTMLマップファイル名（オプション）
- `--interval`: ポイント間隔（メートル、デフォルト: 100）

## 出力

### CSVファイル
- `distance_m`: 開始点からの距離（メートル）
- `latitude`: 緯度
- `longitude`: 経度
- `elevation_m`: 標高（メートル）

### HTMLマップ
- インタラクティブなFoliumマップ
- ルート全体の可視化
- ウェイポイントマーカー

## 技術仕様

- **Python**: 3.11+
- **主要ライブラリ**: OpenRouteService, Shapely, PyProj, Folium
- **座標系**: WGS84 → UTM変換で高精度計算
- **補間**: 1メートル間隔の線形補間
- **標高**: 最近傍法による標高値割り当て

## ライセンス

MIT License