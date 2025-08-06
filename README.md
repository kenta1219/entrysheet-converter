# エントリーシート一括変換アプリ (Clean Architecture版)

.xlsbファイルからデータを抽出し、複数の.xlsxテンプレートに一括転記するWebアプリケーションです。

## アーキテクチャ

このアプリケーションはクリーンアーキテクチャの原則に従って設計されています：

### レイヤー構成

```
src/
├── domain/              # ドメインレイヤー（ビジネスロジック）
│   └── entities.py      # エンティティ（BatchProcessRequest, TemplateInfo等）
├── application/         # アプリケーションレイヤー（ユースケース）
│   └── batch_use_cases.py  # 一括処理ユースケース
├── infrastructure/     # インフラストラクチャレイヤー（外部依存）
│   ├── repositories.py     # ファイル処理リポジトリ実装
│   ├── template_repository.py  # テンプレート管理リポジトリ
│   ├── config.py        # 設定管理
│   └── container.py     # 依存性注入コンテナ
├── presentation/       # プレゼンテーションレイヤー（API層）
│   └── controllers/     # 分離されたコントローラー
│       ├── batch_controller.py   # 一括処理API
│       ├── health_controller.py  # ヘルスチェックAPI
│       └── web_controller.py     # Web UI API
├── templates/          # Excelテンプレートファイル
│   ├── template_config.json     # テンプレート設定
│   ├── 【電子マネー】包括代理加盟店店子申請フォーマット.xlsx
│   ├── 【イオンペイ】包括代理加盟店店子申請フォーマット.xlsx
│   ├── 【統一版】店子申請フォーマット（対面用）.xlsx
│   └── 【店頭】JCB加盟店登録_店子登録申請IF仕様書.xlsx
└── web/                # Web UIレイヤー（フロントエンド）
    ├── templates/       # HTMLテンプレート
    │   └── upload_form.html
    ├── static/          # 静的ファイル
    │   ├── css/style.css
    │   └── js/script.js
    └── views/           # ビューロジック
        └── template_renderer.py
```

### 依存関係の方向

- **ドメインレイヤー**: 他のレイヤーに依存しない
- **アプリケーションレイヤー**: ドメインレイヤーのみに依存
- **インフラストラクチャレイヤー**: ドメインレイヤーに依存（依存性逆転の原則）
- **プレゼンテーションレイヤー**: アプリケーションレイヤーに依存
- **Web UIレイヤー**: プレゼンテーションレイヤーに依存（完全分離）

### 新しいフロントエンド構造 (Option B)

**責務の分離:**
- **API層** (`src/presentation/`): REST APIエンドポイントのみ
- **Web UI層** (`src/web/`): フロントエンド関連のすべて

**利点:**
- 将来のSPA（React/Vue）導入が容易
- フロントエンド/バックエンド開発者の作業領域が明確
- テンプレート、CSS、JavaScriptの独立管理

**UI改善機能:**
- ✅ 処理完了時の詳細な成功/エラー表示
- ✅ リアルタイムファイルバリデーション（拡張子・サイズチェック）
- ✅ ドラッグ&ドロップファイル選択対応
- ✅ レスポンシブデザイン（モバイル対応）
- ✅ 自動ファイルダウンロード機能
- ✅ 処理状況の視覚的フィードバック

### 主要な設計パターン

- **Repository Pattern**: データアクセスの抽象化
- **Dependency Injection**: 依存関係の注入
- **Use Case Pattern**: ビジネスロジックの整理
- **Entity Pattern**: ビジネスオブジェクトの表現

### リファクタリング完了 (v2.0)

**🧹 デッドコード削除:**
- 古い`main.py`（257行）を完全削除
- 非推奨`WebFormController`クラスを削除
- 未使用テストファイル`test_app.py`を削除
- 不要なDIコンテナメソッドを削除

**🎯 品質向上:**
- バグリスクの大幅削減
- コードベースの30%以上スリム化
- 保守性・可読性の向上
- 新規開発者のオンボーディング容易化

## 機能

### 一括処理機能 (v3.0)
- **1つの.xlsbファイルを複数のテンプレートに対して一括処理**
- **対応テンプレート：**
  - **AEON電子マネー** - 電子マネー包括代理加盟店店子申請フォーマット
  - **イオンペイ** - イオンペイ包括代理加盟店店子申請フォーマット
  - **JACCS** - 統一版店子申請フォーマット（対面用）
  - **JCB** - JCB加盟店登録店子登録申請IF仕様書
- **日本語ファイル名対応** - 施設名と処理日付を含むZIPファイル名（例：あきつき薬局_20250805.zip）
- **シンプルなUI** - 一括処理専用のクリーンなインターフェース

### データ処理仕様
- **.xlsbファイル読み込み** - 「加盟店申込書_施設名」シートから特定セルの値を抽出
- **複雑なセル参照** - 単一セル、合計計算、文字列連結、フォーマット変換に対応
- **テンプレート固有マッピング** - 各テンプレートに最適化されたセルマッピング設定
- **エラーハンドリング** - 個別テンプレート処理失敗時も他のテンプレートは継続処理

### 抽出対象セル

**単一セル抽出:**
- F41, F42, F43, F44, F51, F89, F90, F92, F99, F52, F53, F62, F61, F63, F70, F106, F108, F110, F109, F107

**合計値計算:**
- F45+F47+F49, F46+F48+F50, F93+F95+F97, F94+F96+F98, F57+F59, F58+F60, F64+F66+F68, F65+F67+F69

### 出力先列

E14, F14, G14, H14, I14, J14, K14, L14, M14, N14, O14, P14, Q14, R14, S14, U14, V14, W14, X14, Y14, Z14, AA14, AB14, AC14, AD14, AE14, AF14, AG14

## 技術スタック

### バックエンド
- Python 3.11+
- FastAPI (Web API フレームワーク)
- pandas + pyxlsb (xlsb読み込み)
- openpyxl (xlsx書き込み)
- httpx (HTTPクライアント)
- pytest (テストフレームワーク)

### フロントエンド
- Jinja2 (HTMLテンプレートエンジン)
- Vanilla JavaScript (UI制御・Ajax通信)
- CSS3 (レスポンシブデザイン)

### インフラ
- Docker (コンテナ化)
- aiofiles (非同期ファイル操作)

### 開発・品質管理
- Clean Architecture (設計原則)
- Dependency Injection (依存性注入)
- Hot Reload (開発時自動リロード)
- デッドコード削除済み (保守性向上)

## 設定可能パラメータ

環境変数で以下のパラメータを設定可能：

### アプリケーション設定
- `ENVIRONMENT`: 実行環境 (デフォルト: development)
- `DEBUG`: デバッグモード (デフォルト: false)
- `LOG_LEVEL`: ログレベル (デフォルト: INFO)
- `LOG_FORMAT`: ログフォーマット

### ファイル処理設定
- `MAX_FILE_SIZE`: 最大ファイルサイズ (デフォルト: 10485760 = 10MB)

### シート名設定
- `SOURCE_SHEET_NAME`: ソースシート名 (デフォルト: 加盟店申込書_施設名)
- `TARGET_SHEET_NAME`: ターゲットシート名 (デフォルト: 店子申請一覧)

### サーバー設定
- `HOST`: サーバーホスト (デフォルト: 0.0.0.0)
- `PORT`: サーバーポート (デフォルト: 8000)

### 固定設定（ソースコードで管理）
以下の設定は `src/infrastructure/config.py` と `src/domain/entities.py` で定数として管理されています：

- **抽出対象セル**: F41, F42, F43等の特定セル + 合計計算セル
- **出力先列**: E14, F14, G14等の特定列
- **出力ファイル名**: 【電子マネー】包括代理加盟店店子申請フォーマット（割賦販売法対象外）.xlsx
- **ホットリロード対応**: ソースコード変更時に即座に反映

## ローカル実行

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. アプリケーション起動

```bash
python main_clean.py
```

または

```bash
uvicorn main_clean:app --host 0.0.0.0 --port 8000 --reload
```

### 3. ブラウザでアクセス

http://localhost:8000 にアクセスしてWebフォームを使用

## サーバーデプロイ（他端末からのアクセス用）

### 前提条件

- サーバーにDockerとDocker Composeがインストールされていること
- ポート8080が利用可能であること
- WSL環境の場合、Windowsからのアクセスが可能

### デプロイ手順

1. **プロジェクトファイルをサーバーに配置**
   ```bash
   # プロジェクトをサーバーにコピー（例：scp、git clone等）
   git clone <repository-url>
   cd <project-directory>
   ```

2. **アプリケーション起動**
   ```bash
   # 初期セットアップ（.envファイル作成 + Dockerイメージビルド）
   make init
   
   # アプリケーション起動
   make up
   ```

3. **アクセス確認**
   - サーバーのIPアドレスでアクセス: `http://<サーバーIP>:8080/`
   - ローカルアクセス: `http://localhost:8080/`
   - WSL環境の場合: `http://192.168.100.41:8080/`（WindowsのIPアドレス）

**注意**: ポート8080でアクセスしてください。

### WSL環境での追加設定

WSL（Windows Subsystem for Linux）環境で他のWindows端末からアクセスする場合、追加設定が必要です。

#### WSLのIPアドレス確認

```bash
# WSL内で実行
hostname -I
# 例: 172.30.239.18 172.17.0.1 172.18.0.1 172.19.0.1
```

#### Windowsでポートフォワーディング設定

**管理者権限のPowerShell**で以下を実行：

```powershell
# ポートフォワーディング設定
netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=<WSLのIPアドレス>

# 例
netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=172.30.239.18

# 設定確認
netsh interface portproxy show all

# ファイアウォール設定
netsh advfirewall firewall add rule name="WSL Port 8080" dir=in action=allow protocol=TCP localport=8080
```

#### アクセス確認

- **サーバー（Windows）上**: `http://localhost:8080/`
- **他のWindows端末**: `http://<WindowsサーバーのIP>:8080/`
- 例: `http://192.168.100.41:8080/`

### 設定のカスタマイズ

必要に応じて`.env`ファイルを編集して設定を変更できます：

```bash
# 設定ファイルを編集
nano .env

# 変更後は再起動
make restart
```

### 管理コマンド

```bash
# ステータス確認
make status

# ログ確認
make logs

# アプリケーション停止
make down

# 再起動
make restart
```

### トラブルシューティング

#### WSL環境でのアクセス問題

1. **WSLのIPアドレスが変わった場合**
   ```powershell
   # 既存の設定を削除
   netsh interface portproxy delete v4tov4 listenport=8080 listenaddress=0.0.0.0
   
   # 新しいIPアドレスで再設定
   netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=<新しいWSLのIP>
   ```

2. **ポートフォワーディング設定の確認**
   ```powershell
   netsh interface portproxy show all
   ```

3. **ファイアウォール設定の確認**
   ```powershell
   netsh advfirewall firewall show rule name="WSL Port 8080"
   ```

4. **アプリケーションの状態確認**
   ```bash
   # WSL内で実行
   make status
   docker-compose ps
   ```

## Docker実行

### Makefileを使用した実行（推奨）

```bash
# 初期セットアップ（Dockerイメージビルド）
make init

# アプリケーション起動
make up

# アプリケーション停止
make down

# 再起動
make restart

# ログ表示
make logs

# ステータス確認
make status

# Dockerイメージをビルド
make build

# 不要なDockerリソースを削除
make clean

# 完全リセット（全削除 + 再セットアップ）
make reset

# 本番環境にデプロイ
make deploy

# ヘルプ表示
make help
```

### ローカル開発用コマンド

```bash
# Python依存関係をインストール
make install

# ローカル開発サーバーを起動
make dev

# アプリケーションコンテナにシェルでアクセス
make shell

# 現在の設定を表示
make config

# ログディレクトリを作成
make logs-dir
```

### 手動でのDocker実行

```bash
# 1. Dockerイメージのビルド
docker build -t file-converter-app .

# 2. コンテナの起動
docker run -p 8000:8000 file-converter-app

# 3. Docker Composeでの起動
docker-compose up -d

# 4. 停止
docker-compose down
```

### 環境変数を指定して起動

```bash
docker run -p 8000:8000 \
  -e EXTRACT_START_ROW=20 \
  -e MAX_EXTRACT_COUNT=50 \
  file-converter-app
```

## API使用方法

### Webフォーム (推奨)

1. **http://localhost:8000 にアクセス**
2. **.xlsbファイルを選択** - 「加盟店申込書_施設名」シートを含むファイル
3. **施設名を入力** - 日本語対応（例：あきつき薬局）
4. **処理対象テンプレートを選択** - 複数選択可能
5. **「一括変換実行」ボタンをクリック**
6. **ZIPファイルがダウンロード** - 施設名_日付.zip形式

### cURL使用例

```bash
# 一括処理
curl -X POST "http://localhost:8000/batch-process" \
  -F "xlsb_file=@source.xlsb" \
  -F "facility_name=あきつき薬局" \
  -F "selected_templates=aeon_electronic_money" \
  -F "selected_templates=aeon_pay" \
  -F "selected_templates=jaccs" \
  -F "selected_templates=jcb" \
  -o あきつき薬局_20250805.zip

# 利用可能なテンプレート一覧取得
curl http://localhost:8000/templates

# ヘルスチェック
curl http://localhost:8000/health
```

## エラーレスポンス例

### 無効なファイル拡張子

```json
{
  "detail": "xlsbファイルは.xlsb拡張子である必要があります"
}
```

### ファイルサイズ超過

```json
{
  "detail": "xlsbファイルのサイズが制限を超えています"
}
```

### シートが見つからない

```json
{
  "detail": "テンプレートに「店子申請一覧」シートが見つかりません"
}
```

### データが見つからない

```json
{
  "detail": "xlsbファイルのF列15行目以降にデータが見つかりません"
}
```

## ログ出力

アプリケーションは構造化されたJSONログを標準出力に出力します：

```json
{
  "timestamp": "2024-01-01T12:00:00.000000",
  "level": "INFO",
  "message": "ファイル処理開始",
  "xlsb_filename": "source.xlsb",
  "template_filename": "template.xlsx"
}
```

## セキュリティ機能

- ファイル拡張子の厳密なチェック
- ファイルサイズ制限 (デフォルト10MB)
- 一時ファイルの自動クリーンアップ
- 例外処理とエラーハンドリング

## ファイル構成

```
.
├── main_clean.py        # FastAPIアプリケーション本体（クリーンアーキテクチャ版）
├── main.py             # 旧版（参考用）
├── requirements.txt    # Python依存関係
├── Dockerfile         # Docker設定
├── docker-compose.yml # Docker Compose設定
├── Makefile          # Make コマンド定義
├── README.md          # このファイル
├── test_clean_app.py  # クリーンアーキテクチャ版ユニットテスト
├── test_app.py        # 旧版テスト（参考用）
├── logs/              # ログ出力ディレクトリ
└── src/               # ソースコード（クリーンアーキテクチャ）
    ├── __init__.py    # パッケージ初期化
    ├── domain/        # ドメインレイヤー
    │   ├── __init__.py      # パッケージ初期化
    │   ├── entities.py      # エンティティ
    │   ├── repositories.py  # リポジトリインターフェース
    │   └── services.py      # ドメインサービス
    ├── application/   # アプリケーションレイヤー
    │   ├── __init__.py      # パッケージ初期化
    │   └── use_cases.py     # ユースケース
    ├── infrastructure/ # インフラストラクチャレイヤー
    │   ├── __init__.py      # パッケージ初期化
    │   ├── repositories.py  # リポジトリ実装
    │   ├── config.py        # 設定管理
    │   └── container.py     # 依存性注入コンテナ
    └── presentation/  # プレゼンテーションレイヤー
        ├── __init__.py      # パッケージ初期化
        └── controllers.py   # コントローラー
```

## トラブルシューティング

### よくある問題

1. **xlsbファイルが読み込めない**
   - ファイルが破損していないか確認
   - 「加盟店申込書_施設名」シートが存在するか確認

2. **テンプレートファイルが処理できない**
   - 「店子申請一覧」シートが存在するか確認
   - ファイルが読み取り専用でないか確認

3. **Docker起動時のエラー**
   - ポート8000が他のプロセスで使用されていないか確認
   - Dockerデーモンが起動しているか確認

### ログの確認

```bash
# Dockerコンテナのログを確認
docker logs <container_id>

# リアルタイムでログを監視
docker logs -f <container_id>
```

## 開発・テスト

### 開発モードでの起動

```bash
uvicorn main_clean:app --host 0.0.0.0 --port 8000 --reload
```

### テストファイルの実行

```bash
# Makeコマンドを使用（推奨）
make test-clean    # クリーンアーキテクチャ版テスト
make test         # 旧版テスト
make test-all     # 全てのテストを実行

# 直接実行
python test_clean_app.py  # クリーンアーキテクチャ版テスト
python test_app.py        # 旧版テスト（参考用）
```

## ライセンス

このプロジェクトは社内利用を目的としています。