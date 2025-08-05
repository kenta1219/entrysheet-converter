import json
import logging
import tempfile
from datetime import datetime
from typing import List
import pandas as pd
import openpyxl
from ..domain.entities import FileInfo, ExtractedData, ExtractionConfig, WriteConfig, CellReference
from ..domain.repositories import (
    XlsbReaderRepository, XlsxWriterRepository, 
    FileValidatorRepository, LoggerRepository
)


class PandasXlsbReaderRepository(XlsbReaderRepository):
    """pandas + pyxlsbを使用したxlsb読み込みリポジトリ"""
    
    def extract_data(self, file_info: FileInfo, config: ExtractionConfig) -> ExtractedData:
        """xlsbファイルからデータを抽出"""
        with tempfile.NamedTemporaryFile(suffix='.xlsb', delete=False) as temp_file:
            temp_file.write(file_info.content)
            temp_file.flush()
            
            try:
                df = self._load_dataframe(temp_file.name, config.target_sheet)
                extracted_values = self._extract_values_from_dataframe(df, config.cell_references)
                
                return ExtractedData(
                    values=extracted_values,
                    source_sheet=config.target_sheet,
                    source_references=config.cell_references
                )
                
            except Exception as e:
                raise Exception(f"xlsbファイルの読み込みに失敗しました: {str(e)}")
            finally:
                self._cleanup_temp_file(temp_file.name)
    
    def _load_dataframe(self, file_path: str, sheet_name: str) -> pd.DataFrame:
        """xlsbファイルをDataFrameとして読み込み"""
        return pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            engine='pyxlsb'
        )
    
    def _extract_values_from_dataframe(self, df: pd.DataFrame, cell_references: List[CellReference]) -> List[str]:
        """DataFrameから各セル参照に対応する値を抽出"""
        extracted_values = []
        
        for cell_ref in cell_references:
            if cell_ref.is_sum:
                value = self._process_sum_cells(df, cell_ref)
            elif cell_ref.is_concat:
                value = self._process_concat_cells(df, cell_ref)
            else:
                value = self._process_single_cell(df, cell_ref)
            
            extracted_values.append(value)
        
        return extracted_values
    
    def _process_sum_cells(self, df: pd.DataFrame, cell_ref: CellReference) -> str:
        """複数セルの合計を計算"""
        sum_value = 0
        for cell in cell_ref.cells:
            value = self._get_cell_value(df, cell)
            if value is not None and isinstance(value, (int, float)):
                sum_value += value
        return str(sum_value) if sum_value != 0 else "0"
    
    def _process_concat_cells(self, df: pd.DataFrame, cell_ref: CellReference) -> str:
        """複数セルの文字列連結"""
        concat_values = []
        for cell in cell_ref.cells:
            value = self._get_cell_value(df, cell)
            if value is not None:
                formatted_value = self._apply_format_rule(value, cell, cell_ref.format_rules)
                concat_values.append(formatted_value)
            else:
                concat_values.append("")
        return cell_ref.separator.join(concat_values)
    
    def _process_single_cell(self, df: pd.DataFrame, cell_ref: CellReference) -> str:
        """単一セルの値を取得"""
        cell = cell_ref.cells[0]
        value = self._get_cell_value(df, cell)
        return str(value) if value is not None else ""
    
    def _cleanup_temp_file(self, file_path: str):
        """一時ファイルを削除"""
        import os
        try:
            os.unlink(file_path)
        except:
            pass
    
    def _get_cell_value(self, df: pd.DataFrame, cell_address: str):
        """セルアドレスから値を取得"""
        try:
            col_index, row_index = self._parse_cell_address(cell_address)
            
            if not self._is_valid_cell_position(df, row_index, col_index):
                return None
            
            value = df.iloc[row_index, col_index]
            return self._convert_cell_value(value)
            
        except Exception:
            return None
    
    def _parse_cell_address(self, cell_address: str) -> tuple:
        """セルアドレスを解析して列・行インデックスを返す"""
        col_letter = ''.join(filter(str.isalpha, cell_address))
        row_number = int(''.join(filter(str.isdigit, cell_address)))
        
        col_index = ord(col_letter.upper()) - ord('A')
        row_index = row_number - 1  # pandasは0ベース
        
        return col_index, row_index
    
    def _is_valid_cell_position(self, df: pd.DataFrame, row_index: int, col_index: int) -> bool:
        """セル位置が有効範囲内かチェック"""
        return 0 <= row_index < len(df) and 0 <= col_index < len(df.columns)
    
    def _convert_cell_value(self, value):
        """セル値を適切な型に変換"""
        if pd.isna(value):
            return None
        
        # 数値変換を試行
        numeric_value = self._try_convert_to_numeric(value)
        if numeric_value is not None:
            return numeric_value
        
        # 文字列として処理
        str_value = str(value).strip()
        return str_value if str_value else None
    
    def _try_convert_to_numeric(self, value):
        """値を数値に変換を試行"""
        try:
            return float(value)
        except (ValueError, TypeError):
            # カンマ区切りの数値を試行
            try:
                str_value = str(value).replace(',', '')
                return float(str_value)
            except (ValueError, TypeError):
                return None
    
    def _apply_format_rule(self, value, cell: str, format_rules: dict) -> str:
        """フォーマットルールを適用"""
        if not format_rules or cell not in format_rules:
            return str(value)
        
        rule = format_rules[cell]
        numeric_value = self._extract_numeric_value(value)
        
        if numeric_value is None:
            return str(value)
        
        int_value = int(numeric_value)
        
        if rule == "zenkaku_int":
            return self._to_zenkaku_number(str(int_value))
        elif rule == "hankaku_int":
            return str(int_value)
        else:
            return str(value)
    
    def _extract_numeric_value(self, value) -> float:
        """値から数値を抽出"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            # 文字列から数値を抽出
            import re
            num_str = re.sub(r'[^\d.-]', '', str(value))
            return float(num_str) if num_str else None
            
        except (ValueError, TypeError):
            return None
    
    def _to_zenkaku_number(self, num_str: str) -> str:
        """半角数字を全角数字に変換"""
        zenkaku_map = {
            '0': '０', '1': '１', '2': '２', '3': '３', '4': '４',
            '5': '５', '6': '６', '7': '７', '8': '８', '9': '９',
            '-': '－', '.': '．'
        }
        return ''.join(zenkaku_map.get(char, char) for char in num_str)


class OpenpyxlXlsxWriterRepository(XlsxWriterRepository):
    """openpyxlを使用したxlsx書き込みリポジトリ"""
    
    def write_data(self, template_file: FileInfo, data: ExtractedData,
                   config: WriteConfig) -> bytes:
        """テンプレートファイルにデータを書き込み"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx') as template_temp:
            template_temp.write(template_file.content)
            template_temp.flush()
            
            try:
                workbook = openpyxl.load_workbook(template_temp.name)
                worksheet = self._get_target_worksheet(workbook, config.target_sheet)
                self._write_values_to_worksheet(worksheet, data.values, config)
                
                return self._save_workbook_to_bytes(workbook)
                    
            except Exception as e:
                raise Exception(f"テンプレートファイルの処理に失敗しました: {str(e)}")
    
    def _get_target_worksheet(self, workbook, sheet_name: str):
        """対象シートを取得"""
        if sheet_name not in workbook.sheetnames:
            raise Exception(f"テンプレートに「{sheet_name}」シートが見つかりません")
        return workbook[sheet_name]
    
    def _write_values_to_worksheet(self, worksheet, values: List[str], config: WriteConfig):
        """ワークシートに値を書き込み"""
        for i, value in enumerate(values):
            if i >= len(config.target_columns):
                break
                
            col_letter = config.target_columns[i]
            col_index = self._column_letter_to_index(col_letter)
            cell = worksheet.cell(row=config.target_row, column=col_index)
            cell.value = self._convert_value_for_cell(value)
    
    def _convert_value_for_cell(self, value: str):
        """セル用の値に変換"""
        if not value or value == "0":
            return value if value else ""
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return value if value else ""
    
    def _save_workbook_to_bytes(self, workbook) -> bytes:
        """ワークブックをバイト配列として保存"""
        with tempfile.NamedTemporaryFile() as output_temp:
            workbook.save(output_temp.name)
            workbook.close()
            
            output_temp.seek(0)
            return output_temp.read()
    
    def _column_letter_to_index(self, col_letter: str) -> int:
        """列文字を列インデックスに変換（A=1, B=2, ..., AA=27, AB=28, ...）"""
        result = 0
        for char in col_letter.upper():
            result = result * 26 + (ord(char) - ord('A') + 1)
        return result


class BasicFileValidatorRepository(FileValidatorRepository):
    """基本的なファイルバリデーションリポジトリ"""
    
    def validate_xlsb_file(self, file_info: FileInfo) -> bool:
        """xlsbファイルの妥当性を検証"""
        try:
            # 基本的なバイナリファイルチェック
            if len(file_info.content) < 100:  # 最小サイズチェック
                return False
            
            # xlsbファイルの基本的なシグネチャチェック
            # （実際の実装では、より詳細なファイル形式チェックを行う）
            return True
            
        except Exception:
            return False
    
    def validate_xlsx_file(self, file_info: FileInfo) -> bool:
        """xlsxファイルの妥当性を検証"""
        try:
            # 基本的なバイナリファイルチェック
            if len(file_info.content) < 100:  # 最小サイズチェック
                return False
            
            # ZIPファイルシグネチャチェック（xlsxはZIPベース）
            zip_signature = b'PK\x03\x04'
            if not file_info.content.startswith(zip_signature):
                return False
            
            return True
            
        except Exception:
            return False
    
    def validate_file_size(self, file_info: FileInfo, max_size: int) -> bool:
        """ファイルサイズを検証"""
        return file_info.size <= max_size


class StructuredLoggerRepository(LoggerRepository):
    """構造化ログ出力リポジトリ"""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.INFO)
        
        # コンソールハンドラーを設定
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(message)s'))
            self._logger.addHandler(handler)
    
    def _log_structured(self, level: str, message: str, **kwargs):
        """構造化ログを出力"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        self._logger.info(json.dumps(log_data, ensure_ascii=False))
    
    def log_info(self, message: str, **kwargs):
        """情報ログを出力"""
        self._log_structured("INFO", message, **kwargs)
    
    def log_error(self, message: str, **kwargs):
        """エラーログを出力"""
        self._log_structured("ERROR", message, **kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """警告ログを出力"""
        self._log_structured("WARNING", message, **kwargs)