"""一括処理ユースケース"""
import zipfile
import tempfile
import re
import logging
from datetime import datetime
from typing import List, Dict
from pathlib import Path

from ..domain.entities import (
    BatchProcessRequest, BatchProcessResult, FileInfo, TemplateInfo, ProcessingResult
)
from ..infrastructure.template_repository import TemplateRepository
from ..infrastructure.repositories import TemplateBasedFileProcessingRepository

logger = logging.getLogger(__name__)


class BatchProcessingUseCase:
    """一括処理ユースケース
    
    xlsbファイルを複数のテンプレートで一括処理し、
    ZIPファイルとして結果を返すビジネスロジック
    """
    
    def __init__(
        self,
        template_repository: TemplateRepository
    ):
        self._template_repository = template_repository
        self._file_processor = TemplateBasedFileProcessingRepository()
    
    def process_multiple_templates(
        self,
        request: BatchProcessRequest
    ) -> BatchProcessResult:
        """複数テンプレートを一括処理してZIPファイルを生成
        
        Args:
            request: 一括処理リクエスト
            
        Returns:
            BatchProcessResult: 処理結果（成功時はZIPファイルパス含む）
        """
        logger.info(f"一括処理開始 - 施設名: {request.facility_name}, テンプレート数: {len(request.selected_templates)}")
        
        try:
            # 1. 選択されたテンプレートを取得
            templates = self._get_selected_templates(request.selected_templates)
            if not templates:
                logger.warning("処理対象のテンプレートが見つかりません")
                return BatchProcessResult.error_result("処理対象のテンプレートが見つかりません")
            
            # 2. 各テンプレートに対して処理実行
            processed_files = self._process_templates(request.xlsb_file, templates)
            
            if not processed_files:
                logger.error("全てのテンプレート処理が失敗しました")
                return BatchProcessResult.error_result("全てのテンプレート処理が失敗しました")
            
            # 3. ZIPファイル作成
            zip_path = self._create_zip_file(processed_files)
            zip_filename = self._generate_zip_filename(request.facility_name, request.process_date)
            
            logger.info(f"一括処理完了 - 処理済みファイル数: {len(processed_files)}")
            return BatchProcessResult.success_result(
                zip_filename=zip_filename,
                output_path=str(zip_path),
                processed_files=list(processed_files.keys()),
                output_filename=zip_filename
            )
            
        except Exception as e:
            logger.error(f"一括処理中にエラーが発生: {str(e)}")
            return BatchProcessResult.error_result(f"一括処理中にエラーが発生しました: {str(e)}")
    
    def _get_selected_templates(self, template_ids: List[str]) -> List[TemplateInfo]:
        """選択されたテンプレート情報を取得
        
        Args:
            template_ids: テンプレートIDのリスト
            
        Returns:
            List[TemplateInfo]: 有効なテンプレート情報のリスト
        """
        templates = []
        for template_id in template_ids:
            template = self._template_repository.get_template(template_id)
            if template and template.is_active:
                templates.append(template)
            else:
                logger.warning(f"テンプレートが見つからないか無効です: {template_id}")
        return templates
    
    def _process_templates(self, xlsb_file: FileInfo, templates: List[TemplateInfo]) -> Dict[str, bytes]:
        """複数テンプレートの処理を実行
        
        Args:
            xlsb_file: 入力xlsbファイル
            templates: 処理対象テンプレートのリスト
            
        Returns:
            Dict[str, bytes]: 処理済みファイル（ファイル名 -> コンテンツ）
        """
        processed_files = {}
        
        for template in templates:
            try:
                result = self._process_single_template(xlsb_file, template)
                if result.success:
                    processed_files[template.output_filename] = result.output_content
                    logger.info(f"テンプレート処理成功: {template.name}")
                else:
                    logger.warning(f"テンプレート処理失敗: {template.name} - {result.error_message}")
            except Exception as e:
                logger.error(f"テンプレート {template.name} の処理でエラー: {str(e)}")
                continue
        
        return processed_files
    
    def _process_single_template(self, xlsb_file: FileInfo, template: TemplateInfo) -> ProcessingResult:
        """単一テンプレートに対して処理実行
        
        Args:
            xlsb_file: 入力xlsbファイル
            template: 処理対象テンプレート
            
        Returns:
            ProcessingResult: 処理結果
        """
        # テンプレートファイルの内容を取得
        template_content = self._template_repository.get_template_content(template.id)
        if not template_content:
            raise Exception(f"テンプレートファイルが見つかりません: {template.filename}")
        
        # テンプレートファイル情報を作成
        template_file_info = FileInfo(
            filename=template.filename,
            content=template_content,
            size=len(template_content)
        )
        
        try:
            # テンプレート固有の処理を実行
            result_content = self._file_processor.process_with_template_mapping(
                xlsb_file, template_file_info, template
            )
            
            return ProcessingResult.success_result(
                template.output_filename,
                result_content,
                len(template.mapping.cell_mappings) if template.mapping else 0
            )
            
        except Exception as e:
            return ProcessingResult.error_result(f"テンプレート処理エラー: {str(e)}")
    
    def _create_zip_file(self, files: Dict[str, bytes]) -> Path:
        """ZIPファイルを作成し、ファイルパスを返す
        
        Args:
            files: ファイル名とコンテンツの辞書
            
        Returns:
            Path: 作成されたZIPファイルのパス
        """
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        try:
            with zipfile.ZipFile(temp.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for filename, content in files.items():
                    zipf.writestr(filename, content)
            logger.info(f"ZIPファイル作成完了: {temp.name}")
            return Path(temp.name)
        except Exception as e:
            logger.error(f"ZIPファイル作成エラー: {str(e)}")
            raise
    
    def _generate_zip_filename(self, facility_name: str, process_date: datetime) -> str:
        """ZIPファイル名を生成
        
        Args:
            facility_name: 施設名
            process_date: 処理日時
            
        Returns:
            str: 生成されたZIPファイル名
        """
        sanitized_name = self._sanitize_facility_name(facility_name)
        date_str = process_date.strftime("%Y%m%d")
        filename = f"{sanitized_name}_{date_str}.zip"
        
        logger.debug(f"ZIPファイル名生成: {filename}")
        return filename
    
    def _sanitize_facility_name(self, name: str) -> str:
        """施設名をファイル名として安全な形式に変換（日本語文字を保持）
        
        Args:
            name: 元の施設名
            
        Returns:
            str: サニタイズされた施設名
        """
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