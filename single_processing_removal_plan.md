# 単体処理機能削除計画

## 削除対象の特定結果

### 🗂️ **削除対象ファイル（完全削除）**

1. **`src/application/use_cases.py`** - 単体処理ユースケース
2. **`src/presentation/controllers/file_controller.py`** - 単体処理コントローラー

### 🔧 **修正対象ファイル（部分削除）**

#### 1. **UI関連**
- **`src/web/templates/upload_form.html`**
  - 削除: 単体処理フォーム（22-40行目）
  - 削除: 区切り線（42行目）
  - 保持: 一括処理フォーム

#### 2. **エンドポイント**
- **`main_clean.py`**
  - 削除: `/process` エンドポイント（60-71行目）
  - 保持: `/batch-process` エンドポイント

#### 3. **依存性注入**
- **`src/infrastructure/container.py`**
  - 削除: `FileProcessingUseCase` import（2行目）
  - 削除: `FileProcessingController` import（6行目）
  - 削除: `get_file_processing_use_case()` メソッド（97-101行目）
  - 削除: `get_file_processing_controller()` メソッド（103-110行目）

#### 4. **エンティティ（部分削除検討）**
- **`src/domain/entities.py`**
  - 検討: `ProcessingResult` クラス（121-146行目）
  - 検討: `ExtractedData` クラス（103-117行目）
  - 検討: `WriteConfig` クラス（87-100行目）
  - 検討: `ExtractionConfig` クラス（46-84行目）
  - **判定**: 一括処理でも使用されているため保持

### 📋 **削除作業の順序**

#### Phase 1: UI削除
1. HTMLから単体処理フォームを削除
2. 機能説明を一括処理のみに更新

#### Phase 2: エンドポイント削除
1. `main_clean.py` から `/process` エンドポイントを削除

#### Phase 3: コントローラー・ユースケース削除
1. `src/presentation/controllers/file_controller.py` を削除
2. `src/application/use_cases.py` を削除

#### Phase 4: 依存性注入の清理
1. `container.py` から単体処理関連のimportとメソッドを削除

#### Phase 5: 動作確認
1. アプリケーション起動確認
2. 一括処理機能の動作確認
3. エラーログの確認

### 🔍 **保持する理由**

#### **エンティティクラス**
- `ExtractionConfig`: 一括処理の `TemplateBasedFileProcessingRepository` で使用
- `ProcessingResult`: 一括処理の `_process_single_template()` で使用
- `ExtractedData`: データ抽出処理で共通使用
- `WriteConfig`: テンプレート処理で共通使用

#### **リポジトリクラス**
- `TemplateBasedFileProcessingRepository`: 一括処理で各テンプレート処理に使用

### ⚠️ **注意事項**

1. **段階的削除**: 一度に全て削除せず、段階的に削除してテストを実行
2. **依存関係の確認**: 削除前に他のファイルでの使用状況を再確認
3. **バックアップ**: 削除前に重要なファイルのバックアップを推奨
4. **テスト実行**: 各段階で動作確認を実施

### 📊 **削除後の期待効果**

- **コードベースの簡素化**: 不要なファイル2個、メソッド4個の削除
- **保守性の向上**: 一括処理のみに集中した設計
- **UI/UXの改善**: シンプルな一括処理専用インターフェース
- **依存関係の整理**: 不要な依存性注入の削除

## 実装準備完了

上記計画に基づいて、段階的に単体処理機能を削除します。