"""複数ファイル処理ユースケース"""
import tempfile
import re
import logging
from datetime import datetime
from typing import List, Dict
from pathlib import Path

from ..domain.entities import (
    MultiFileProcessRequest, MultiFileProcessResult, FileInfo, TemplateInfo, 
    ProcessingResult, RowData, ValidationResult
)
from ..infrastructure.template_repository import TemplateRepository
from ..infrastructure.repositories import TemplateBasedFileProcessingRepository

logger = logging.getLogger(__name__)


class MultiFileProcessingUseCase:
    """複数ファイル→単一テンプレート処理ユースケース
    
    複数のxlsbファイルを1つのテンプレートに順次転記し、
    単一のExcelファイルとして結果を返すビジネスロジック
    """
    
    def __init__(
        self,
        template_repository: TemplateRepository
    ):
        self._template_repository = template_repository
        self._file_processor = TemplateBasedFileProcessingRepository()
    
    def process_multiple_files_to_single_template(
        self,
        request: MultiFileProcessRequest
    ) -> MultiFileProcessResult:
        """複数xlsbファイルを1つのテンプレートに順次転記
        
        Args:
            request: 複数ファイル処理リクエスト
            
        Returns:
            MultiFileProcessResult: 処理結果
        """
        logger.info(f"複数ファイル処理開始 - ファイル数: {len(request.xlsb_files)}, テンプレート: {request.target_template_id}")
        
        try:
            # 1. テンプレート情報を取得
            template = self._get_target_template(request.target_template_id)
            
            # 2. 容量チェック
            validation_result = self._file_processor.validate_template_capacity(
                template, len(request.xlsb_files), request.start_row
            )
            if not validation_result.is_valid:
                return MultiFileProcessResult.error_result(validation_result.error_message)
            
            # 3. 各xlsbファイルからデータを抽出
            row_data_list = self._extract_data_from_multiple_files(request)
            
            if not row_data_list:
                return MultiFileProcessResult.error_result("全てのファイル処理が失敗しました")
            
            # 4. 単一テンプレートに複数行を書き込み
            result_content = self._write_multiple_rows_to_template(
                template, row_data_list
            )
            
            # 5. 出力ファイルを一時保存
            output_path = self._save_result_to_temp_file(result_content)
            
            # 6. 出力ファイル名を生成
            output_filename = self._generate_multi_file_output_name(
                template, len(row_data_list), request.process_date
            )
            
            logger.info(f"複数ファイル処理完了 - 処理済み行数: {len(row_data_list)}")
            return MultiFileProcessResult.success_result(
                output_filename, output_path, len(row_data_list), result_content
            )
            
        except Exception as e:
            logger.error(f"複数ファイル処理エラー: {str(e)}")
            return MultiFileProcessResult.error_result(f"処理中にエラーが発生しました: {str(e)}")
    
    def _get_target_template(self, template_id: str) -> TemplateInfo:
        """対象テンプレート情報を取得"""
        template = self._template_repository.get_template(template_id)
        if not template or not template.is_active:
            raise Exception(f"テンプレートが見つからないか無効です: {template_id}")
        
        if not template.mapping:
            raise Exception(f"テンプレートにマッピング情報がありません: {template_id}")
        
        return template
    
    def _extract_data_from_multiple_files(
        self, 
        request: MultiFileProcessRequest
    ) -> List[RowData]:
        """複数ファイルからデータを抽出"""
        row_data_list = []
        failed_files = []
        
        for i, (xlsb_file, facility_name) in enumerate(
            zip(request.xlsb_files, request.facility_names)
        ):
            try:
                # 各ファイルからデータ抽出
                extracted_data = self._file_processor.extract_data_from_xlsb(xlsb_file)
                
                row_data = RowData(
                    row_number=request.start_row + i,
                    facility_name=facility_name,
                    extracted_values=extracted_data.values,
                    source_filename=xlsb_file.filename
                )
                row_data_list.append(row_data)
                
                logger.info(f"データ抽出成功: {xlsb_file.filename} → 行{row_data.row_number}")
                
            except Exception as e:
                logger.warning(f"ファイル処理失敗: {xlsb_file.filename} - {str(e)}")
                failed_files.append(xlsb_file.filename)
                continue
        
        if failed_files:
            logger.warning(f"処理失敗ファイル: {failed_files}")
        
        return row_data_list
    
    def _write_multiple_rows_to_template(
        self,
        template: TemplateInfo,
        row_data_list: List[RowData]
    ) -> bytes:
        """テンプレートに複数行を書き込み"""
        # テンプレートファイルを取得
        template_content = self._template_repository.get_template_content(template.id)
        if not template_content:
            raise Exception(f"テンプレートファイルが見つかりません: {template.filename}")
        
        template_file_info = FileInfo(
            filename=template.filename,
            content=template_content,
            size=len(template_content)
        )
        
        # 複数行書き込み処理を実行
        return self._file_processor.write_multiple_rows_to_template(
            template_file_info, template, row_data_list
        )
    
    def _save_result_to_temp_file(self, content: bytes) -> str:
        """結果を一時ファイルに保存"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        try:
            temp_file.write(content)
            temp_file.flush()
            logger.info(f"結果ファイル保存: {temp_file.name}")
            return temp_file.name
        except Exception as e:
            logger.error(f"結果ファイル保存エラー: {str(e)}")
            raise
        finally:
            temp_file.close()
    
    def _generate_multi_file_output_name(
        self,
        template: TemplateInfo,
        processed_count: int,
        process_date: datetime
    ) -> str:
        """複数ファイル処理用の出力ファイル名を生成"""
        date_str = process_date.strftime("%Y%m%d")
        base_name = template.output_filename.replace('.xlsx', '')
        filename = f"{base_name}_一括処理_{processed_count}件_{date_str}.xlsx"
        
        logger.debug(f"出力ファイル名生成: {filename}")
        return filename
    
    def _sanitize_facility_name(self, name: str) -> str:
        """施設名をファイル名として安全な形式に変換（日本語文字を保持）"""
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