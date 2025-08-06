"""一括処理コントローラー"""
from fastapi import HTTPException, UploadFile, Form
from fastapi.responses import FileResponse
from urllib.parse import quote
from datetime import datetime
from typing import List
import logging

from ...domain.entities import FileInfo, BatchProcessRequest
from ...application.batch_use_cases import BatchProcessingUseCase
from ...infrastructure.template_repository import TemplateRepository

logger = logging.getLogger(__name__)


class BatchProcessingController:
    """一括処理コントローラー
    
    xlsbファイルを複数のテンプレートで一括処理し、
    ZIPファイルとしてダウンロード可能な形式で返すコントローラー
    """
    
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
        """一括処理エンドポイント
        
        Args:
            xlsb_file: アップロードされたxlsbファイル
            facility_name: 施設名（ファイル名に使用）
            selected_templates: 処理対象テンプレートIDのリスト
            
        Returns:
            FileResponse: 処理済みファイルを含むZIPファイル
            
        Raises:
            HTTPException: バリデーションエラーまたは処理エラー
        """
        logger.info(f"一括処理開始 - 施設名: {facility_name}, 選択テンプレート数: {len(selected_templates)}")
        
        # 入力バリデーション
        self._validate_inputs(facility_name, selected_templates)
        
        # ファイル情報の作成
        xlsb_file_info = await self._create_file_info(xlsb_file)
        
        # 処理リクエストの作成
        request = self._create_batch_request(xlsb_file_info, facility_name, selected_templates)
        
        # 一括処理の実行
        result = self._batch_use_case.process_multiple_templates(request)
        
        # 結果の検証
        self._validate_result(result)
        
        return self._create_zip_response(result)
    
    def get_available_templates(self) -> dict:
        """利用可能なテンプレート一覧を取得
        
        Returns:
            dict: テンプレート情報のリスト
            
        Raises:
            HTTPException: テンプレート取得エラー
        """
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
            logger.error(f"テンプレート情報取得エラー: {str(e)}")
            raise HTTPException(status_code=500, detail=f"テンプレート情報の取得に失敗しました: {str(e)}")
    
    def _validate_inputs(self, facility_name: str, selected_templates: List[str]) -> None:
        """入力値のバリデーション"""
        if not facility_name.strip():
            raise HTTPException(status_code=400, detail="施設名を入力してください")
        
        filtered_templates = [t for t in selected_templates if t.strip()]
        if not filtered_templates:
            raise HTTPException(status_code=400, detail="処理対象のテンプレートを選択してください")
    
    async def _create_file_info(self, xlsb_file: UploadFile) -> FileInfo:
        """UploadFileからFileInfoエンティティを作成"""
        xlsb_content = await xlsb_file.read()
        return FileInfo(
            filename=xlsb_file.filename or "unknown.xlsb",
            content=xlsb_content,
            size=len(xlsb_content)
        )
    
    def _create_batch_request(
        self,
        xlsb_file_info: FileInfo,
        facility_name: str,
        selected_templates: List[str]
    ) -> BatchProcessRequest:
        """一括処理リクエストを作成"""
        filtered_templates = [t for t in selected_templates if t.strip()]
        return BatchProcessRequest(
            xlsb_file=xlsb_file_info,
            facility_name=facility_name.strip(),
            selected_templates=filtered_templates,
            process_date=datetime.now()
        )
    
    def _validate_result(self, result) -> None:
        """処理結果の検証"""
        if not hasattr(result, 'success') or not result.success:
            error_msg = getattr(result, 'error_message', '不明なエラーが発生しました')
            logger.error(f"一括処理エラー: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
    
    def _create_zip_response(self, result) -> FileResponse:
        """ZIPファイルのレスポンスを作成
        
        Args:
            result: 一括処理結果
            
        Returns:
            FileResponse: ZIPファイルのダウンロードレスポンス
        """
        # 日本語ファイル名をURLエンコード
        encoded_filename = quote(result.zip_filename)
        
        # Content-Dispositionヘッダーを設定（日本語対応）
        headers = {
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
        
        return FileResponse(
            path=result.output_path,
            media_type="application/zip",
            filename=result.zip_filename,  # fallback用に指定
            headers=headers
        )


