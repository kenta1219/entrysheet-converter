"""一括処理コントローラー"""
from fastapi import HTTPException, UploadFile, Form
from fastapi.responses import FileResponse
from urllib.parse import quote
from datetime import datetime
from typing import List
import tempfile
import logging

from ...domain.entities import FileInfo, BatchProcessRequest
from ...application.batch_use_cases import BatchProcessingUseCase
from ...infrastructure.template_repository import TemplateRepository

logger = logging.getLogger(__name__)


class BatchProcessingController:
    """一括処理コントローラー"""
    
    def __init__(
        self,
        batch_use_case: BatchProcessingUseCase,
        template_repository: TemplateRepository
    ):
        self._batch_use_case = batch_use_case
        self._template_repository = template_repository
    
    async def batch_process(
        self,
        xlsb_file: UploadFile,
        facility_name: str = Form(...),
        selected_templates: List[str] = Form(default=[])
    ) -> FileResponse:
        """一括処理エンドポイント"""
        
        # ログ出力
        logger.info(f"一括処理開始 - 施設名: {facility_name}, 選択テンプレート数: {len(selected_templates)}")
        
        # 入力バリデーション
        if not facility_name.strip():
            raise HTTPException(status_code=400, detail="施設名を入力してください")
        
        # 空の文字列が含まれている場合は除外
        filtered_templates = [t for t in selected_templates if t.strip()]
        
        if not filtered_templates:
            raise HTTPException(status_code=400, detail="処理対象のテンプレートを選択してください")
        
        # UploadFileからFileInfoエンティティを作成
        xlsb_content = await xlsb_file.read()
        xlsb_file_info = FileInfo(
            filename=xlsb_file.filename or "unknown.xlsb",
            content=xlsb_content,
            size=len(xlsb_content)
        )
        
        # 一括処理リクエストを作成
        request = BatchProcessRequest(
            xlsb_file=xlsb_file_info,
            facility_name=facility_name.strip(),
            selected_templates=filtered_templates,
            process_date=datetime.now()
        )
        
        # 一括処理を実行
        result = self._batch_use_case.process_multiple_templates(request)

        if not hasattr(result, 'success') or not result.success:
            raise HTTPException(status_code=400, detail=getattr(result, 'error_message', '不明なエラーが発生しました'))

        return self._create_zip_response(result)
    
    def get_available_templates(self):
        """利用可能なテンプレート一覧を取得"""
        try:
            templates = self._template_repository.get_all_templates()
            return {
                "templates": [
                    {
                        "id": template.id,
                        "name": template.name,
                        "description": template.description,
                        "output_filename": template.output_filename
                    }
                    for template in templates
                ]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"テンプレート情報の取得に失敗しました: {str(e)}")
    
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


