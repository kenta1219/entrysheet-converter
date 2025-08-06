from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
from datetime import datetime


@dataclass
class FileInfo:
    """ファイル情報エンティティ"""
    filename: str
    content: bytes
    size: int
    
    @property
    def extension(self) -> str:
        """ファイル拡張子を取得"""
        return Path(self.filename).suffix.lower()


@dataclass
class CellReference:
    """セル参照エンティティ"""
    cells: List[str]  # 例: ["F41"] または ["F45", "F47", "F49"]
    is_sum: bool = False  # 合計が必要かどうか
    is_concat: bool = False  # 文字列連結が必要かどうか
    separator: str = ""  # 連結時のセパレータ
    format_rules: dict = None  # セル別フォーマットルール
    
    @classmethod
    def single_cell(cls, cell: str) -> 'CellReference':
        """単一セル参照を作成"""
        return cls(cells=[cell], is_sum=False, is_concat=False, separator="", format_rules=None)
    
    @classmethod
    def sum_cells(cls, cells: List[str]) -> 'CellReference':
        """合計セル参照を作成"""
        return cls(cells=cells, is_sum=True, is_concat=False, separator="", format_rules=None)
    
    @classmethod
    def concat_cells(cls, cells: List[str], separator: str = "", format_rules: dict = None) -> 'CellReference':
        """文字列連結セル参照を作成"""
        return cls(cells=cells, is_sum=False, is_concat=True, separator=separator, format_rules=format_rules)


@dataclass
class ExtractionConfig:
    """データ抽出設定エンティティ"""
    target_sheet: str = "加盟店申込書_施設名"
    cell_references: List[CellReference] = None
    
    def __post_init__(self):
        """デフォルトのセル参照設定（1行上にシフト修正）"""
        if self.cell_references is None:
            self.cell_references = [
                CellReference.single_cell("F40"),      # E14 (株式会社ＰＯＬＹＶＡＬＥＮＴ)
                CellReference.single_cell("F41"),      # F14 (ｶﾌﾞｼｷｶﾞｲｼｬﾎﾟﾘﾊﾞﾚﾝﾄ)
                CellReference.single_cell("F42"),      # G14 (7010901044955)
                CellReference.single_cell("F43"),      # H14 (4110036)
                CellReference.concat_cells(["F44", "F46", "F48"]),  # I14
                CellReference.concat_cells(["F45", "F47", "F49"]),  # J14
                CellReference.single_cell("F50"),      # K14
                CellReference.single_cell("F88"),      # L14
                CellReference.single_cell("F89"),      # M14
                CellReference.single_cell("F91"),      # N14
                CellReference.concat_cells(["F92", "F94", "F96"]),  # O14
                CellReference.concat_cells(["F93", "F95", "F97"]),  # P14
                CellReference.single_cell("F98"),      # Q14
                CellReference.single_cell("F51"),      # R14
                CellReference.single_cell("F52"),      # S14
                CellReference.concat_cells(["F56", "F58"], separator="　"),  # U14 (全角スペース)
                CellReference.concat_cells(["F57", "F59"], separator=" "),   # V14 (半角スペース)
                CellReference.single_cell("F61"),      # W14
                CellReference.single_cell("F60"),      # X14
                CellReference.single_cell("F62"),      # Y14
                CellReference.concat_cells(["F63", "F65", "F67"], format_rules={"F67": "zenkaku_int"}),  # Z14
                CellReference.concat_cells(["F64", "F66", "F68"], format_rules={"F68": "hankaku_int"}),  # AA14
                CellReference.single_cell("F69"),      # AB14
                CellReference.single_cell("F105"),     # AC14
                CellReference.single_cell("F107"),     # AD14
                CellReference.single_cell("F109"),     # AE14
                CellReference.single_cell("F108"),     # AF14
                CellReference.single_cell("F106"),     # AG14
            ]


@dataclass
class WriteConfig:
    """データ書き込み設定エンティティ"""
    target_sheet: str = "店子申請一覧"
    target_row: int = 14
    target_columns: List[str] = None
    
    def __post_init__(self):
        """デフォルトの出力列設定"""
        if self.target_columns is None:
            self.target_columns = [
                "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S",
                "U", "V", "W", "X", "Y", "Z", "AA", "AB", "AC", "AD", "AE", "AF", "AG"
            ]


@dataclass
class ExtractedData:
    """抽出されたデータエンティティ"""
    values: List[str]
    source_sheet: str
    source_references: List[CellReference]
    
    @property
    def count(self) -> int:
        """抽出されたデータの件数"""
        return len(self.values)
    
    @property
    def is_empty(self) -> bool:
        """データが空かどうか"""
        return len(self.values) == 0


@dataclass
class ProcessingResult:
    """処理結果エンティティ"""
    success: bool
    output_filename: str
    output_content: Optional[bytes] = None
    extracted_count: int = 0
    error_message: Optional[str] = None
    
    @classmethod
    def success_result(cls, filename: str, content: bytes, count: int) -> 'ProcessingResult':
        """成功結果を作成"""
        return cls(
            success=True,
            output_filename=filename,
            output_content=content,
            extracted_count=count
        )
    
    @classmethod
    def error_result(cls, error_message: str) -> 'ProcessingResult':
        """エラー結果を作成"""
        return cls(
            success=False,
            output_filename="",
            error_message=error_message
        )


@dataclass
class CellMapping:
    """セルマッピング情報"""
    target: str  # 出力先セル (例: "E16")
    source: str  # 参照元セル (例: "F40" or "F44+F46+F48")
    type: str = "single"  # "single", "concat_cells"
    separator: str = ""  # 結合時のセパレータ
    format_rules: dict = None  # フォーマットルール

    def __post_init__(self):
        if self.format_rules is None:
            self.format_rules = {}


@dataclass
class TemplateMapping:
    """テンプレートマッピング情報"""
    source_sheet: str
    target_sheet: str
    target_row: int
    cell_mappings: List[CellMapping]


@dataclass
class TemplateInfo:
    """テンプレート情報エンティティ"""
    id: str
    name: str
    filename: str
    output_filename: str
    description: str
    is_active: bool = True
    mapping: TemplateMapping = None


@dataclass
class BatchProcessRequest:
    """一括処理リクエストエンティティ"""
    xlsb_file: 'FileInfo'
    facility_name: str
    selected_templates: List[str]
    process_date: datetime


@dataclass
class BatchProcessResult:
    success: bool
    zip_filename: Optional[str] = None
    output_path: Optional[str] = None   # ←追加
    output_filename: Optional[str] = None  # ←追加
    processed_files: List[str] = None
    error_message: str = ""

    @classmethod
    def success_result(
        cls,
        zip_filename: str,
        output_path: str,
        processed_files: List[str],
        output_filename: Optional[str] = None
    ) -> 'BatchProcessResult':
        return cls(
            success=True,
            zip_filename=zip_filename,
            output_path=output_path,
            output_filename=output_filename or zip_filename,
            processed_files=processed_files
        )

    @classmethod
    def error_result(cls, error_message: str) -> 'BatchProcessResult':
        return cls(
            success=False,
            output_filename="",
            error_message=error_message
        )


@dataclass
class ValidationResult:
    """バリデーション結果エンティティ"""
    is_valid: bool
    error_message: Optional[str] = None
    
    @classmethod
    def valid(cls) -> 'ValidationResult':
        """有効な結果を作成"""
        return cls(is_valid=True)
    
    @classmethod
    def invalid(cls, message: str) -> 'ValidationResult':
        """無効な結果を作成"""
        return cls(is_valid=False, error_message=message)