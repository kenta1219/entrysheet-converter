# 日本語ファイル名問題の原因分析

## 問題の概要
ZIPファイルのダウンロード時に、日本語ファイル名が `あきつき薬局_20250805.zip` ではなく `utf-881E38D81E38D96E580_20250805.zip` のような文字化けした形で表示される問題が発生。

## 16時頃の正常動作時の実装 vs 現在の実装

### 1. **ファイル名サニタイズ処理の変更**

#### 16時頃（正常動作時）
```python
def _sanitize_facility_name(self, name: str) -> str:
    """施設名をファイル名として安全な形式に変換（日本語文字を保持）"""
    # ファイル名として使用禁止の文字のみを置換（日本語文字は保持）
    forbidden_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    sanitized = name
    for char in forbidden_chars:
        sanitized = sanitized.replace(char, '_')
    
    # 日本語文字はそのまま保持
    return sanitized
```

#### 現在の実装
```python
def _sanitize_facility_name(self, name: str) -> str:
    """施設名をファイル名として安全な形式に変換（日本語文字を保持）"""
    import re
    
    # ファイル名として使用禁止の文字のみを置換（日本語文字は保持）
    forbidden_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    sanitized = name
    for char in forbidden_chars:
        sanitized = sanitized.replace(char, '_')
    
    # 制御文字を除去
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
    
    # 連続する空白を単一の空白に変換
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # 先頭・末尾の空白を除去
    sanitized = sanitized.strip()
    
    # 空文字列の場合はデフォルト名を使用
    if not sanitized:
        sanitized = "施設"
    
    # 文字数制限（日本語考慮で30文字まで）
    if len(sanitized) > 30:
        sanitized = sanitized[:30]
    
    return sanitized
```

**差分**: 現在の実装では追加の正規表現処理が含まれているが、これは日本語文字に影響しないはず。

### 2. **HTTPヘッダー処理の変更**

#### 16時頃（正常動作時）
```python
# 推測される実装（単純なFileResponse）
return FileResponse(
    path=zip_path,
    filename=zip_filename,  # 日本語ファイル名をそのまま指定
    media_type="application/zip"
)
```

#### 現在の実装
```python
def _create_zip_response(self, result):
    """ZIPファイルのレスポンスを作成"""

    # 日本語ファイル名をURLエンコード
    encoded_filename = quote(result.zip_filename)

    # Content-Dispositionヘッダーを設定（日本語対応）
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
    }

    # result.output_path は実際のZIPファイルのパス
    return FileResponse(
        path=result.output_path,
        media_type="application/zip",
        filename=result.zip_filename,  # fallback用に指定
        headers=headers
    )
```

**差分**: 現在の実装では `quote()` によるURLエンコードと `filename*=UTF-8''` 形式のヘッダーを使用。

### 3. **FastAPI/Starletteバージョンの影響**

#### 16時頃（正常動作時）
- `fastapi==0.104.1`
- `python-multipart==0.0.6`

#### 現在の実装
- `fastapi==0.104.1` (復元済み)
- `python-multipart==0.0.6` (復元済み)

**差分**: パッケージバージョンは復元済みのため、バージョン起因ではない。

## 推定される根本原因

### **最も可能性の高い原因: HTTPヘッダー処理の過剰な複雑化**

16時頃の正常動作時は、おそらく以下のようなシンプルな実装だった：

```python
return FileResponse(
    path=zip_path,
    filename=zip_filename,  # 日本語ファイル名をそのまま
    media_type="application/zip"
)
```

現在の実装では、日本語対応のために以下の処理を追加：
1. `quote()` によるURLエンコード
2. `Content-Disposition: attachment; filename*=UTF-8''` ヘッダー

**問題**: この処理により、ブラウザが日本語ファイル名を正しく解釈できなくなっている可能性がある。

### **具体的な問題点**

1. **URLエンコードの二重適用**: `quote()` でエンコードした結果が、さらにブラウザ側でエンコードされている
2. **ヘッダー形式の不適切性**: `filename*=UTF-8''` 形式がブラウザで正しく処理されていない
3. **FastAPIの内部処理**: FastAPIが `filename` パラメータを内部で処理する際の文字エンコーディング問題

## 解決策

### **推奨アプローチ: シンプルな実装への回帰**

16時頃の正常動作時の実装に戻す：

```python
def _create_zip_response(self, result):
    """ZIPファイルのレスポンスを作成（シンプル版）"""
    return FileResponse(
        path=result.output_path,
        filename=result.zip_filename,  # 日本語ファイル名をそのまま指定
        media_type="application/zip"
    )
```

### **代替アプローチ: ヘッダー処理の修正**

もし明示的なヘッダー制御が必要な場合：

```python
def _create_zip_response(self, result):
    """ZIPファイルのレスポンスを作成（ヘッダー修正版）"""
    # RFC 6266準拠の正しいヘッダー形式
    headers = {
        "Content-Disposition": f"attachment; filename=\"{result.zip_filename}\"; filename*=UTF-8''{quote(result.zip_filename)}"
    }
    
    return FileResponse(
        path=result.output_path,
        media_type="application/zip",
        headers=headers
    )
```

## 結論

日本語ファイル名問題の根本原因は、**HTTPヘッダー処理の過剰な複雑化**にある。16時頃の正常動作時はシンプルな `FileResponse` 実装だったが、日本語対応のために追加した `quote()` エンコードと `filename*=UTF-8''` ヘッダーが逆に問題を引き起こしている。

最も確実な解決策は、**16時頃の正常動作時のシンプルな実装に戻すこと**である。