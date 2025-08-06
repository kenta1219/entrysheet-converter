"""一括処理ユースケース"""
import zipfile
import tempfile
from datetime import datetime
from typing import List, Dict
from pathlib import Path

from ..domain.entities import (
    BatchProcessRequest, BatchProcessResult, FileInfo, TemplateInfo
)
from ..infrastructure.template_repository import TemplateRepository
from ..infrastructure.repositories import TemplateBasedFileProcessingRepository


class BatchProcessingUseCase:
    """一括処理ユースケース"""
    
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
        """複数テンプレートを一括処理してZIPファイルを生成"""
        
        try:
            # 1. 選択されたテンプレートを取得
            templates = self._get_selected_templates(request.selected_templates)
            if not templates:
                return BatchProcessResult.error_result("処理対象のテンプレートが見つかりません")
            
            # 2. 各テンプレートに対して処理実行
            processed_files = {}
            for template in templates:
                try:
                    result = self._process_single_template(request.xlsb_file, template)
                    if result.success:
                        processed_files[template.output_filename] = result.output_content
                    else:
                        # 個別のテンプレート処理が失敗した場合はスキップ
                        continue
                except Exception as e:
                    # 個別のエラーはログに記録してスキップ
                    print(f"テンプレート {template.name} の処理でエラー: {str(e)}")
                    continue
            
            if not processed_files:
                return BatchProcessResult.error_result("全てのテンプレート処理が失敗しました")
            
            # 3. ZIPファイル作成
            zip_path = self._create_zip_file(processed_files)  # ← bytes → Path に変更

            zip_filename = self._generate_zip_filename(
                request.facility_name, request.process_date
            )
            
            return BatchProcessResult.success_result(
                zip_filename=zip_filename,
                output_path=str(zip_path),
                processed_files=list(processed_files.keys()),  # 出力されたファイル名一覧
                output_filename=zip_filename
            )
            
        except Exception as e:
            return BatchProcessResult.error_result(f"一括処理中にエラーが発生しました: {str(e)}")
    
    def _get_selected_templates(self, template_ids: List[str]) -> List[TemplateInfo]:
        """選択されたテンプレート情報を取得"""
        templates = []
        for template_id in template_ids:
            template = self._template_repository.get_template(template_id)
            if template and template.is_active:
                templates.append(template)
        return templates
    
    def _process_single_template(self, xlsb_file: FileInfo, template: TemplateInfo):
        """単一テンプレートに対して処理実行"""
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
            
            from ..domain.entities import ProcessingResult
            return ProcessingResult.success_result(
                template.output_filename,
                result_content,
                len(template.mapping.cell_mappings) if template.mapping else 0
            )
            
        except Exception as e:
            from ..domain.entities import ProcessingResult
            return ProcessingResult.error_result(f"テンプレート処理エラー: {str(e)}")
    
    def _create_zip_file(self, files: Dict[str, bytes]) -> Path:
        """ZIPファイルを作成し、ファイルパスを返す"""
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        with zipfile.ZipFile(temp.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename, content in files.items():
                zipf.writestr(filename, content)
        return Path(temp.name)
    
    def _generate_zip_filename(self, facility_name: str, process_date: datetime) -> str:
        """ZIPファイル名を生成"""
        # 施設名をファイル名として安全な形式に変換
        sanitized_name = self._sanitize_facility_name(facility_name)
        
        date_str = process_date.strftime("%Y%m%d")
        filename = f"{sanitized_name}_{date_str}.zip"
        
        return filename
    
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