from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path

from src.infrastructure.container import container
from src.infrastructure.config import OUTPUT_FILENAME


def create_app() -> FastAPI:
    """FastAPIアプリケーションを作成"""
    
    # 設定を取得
    config = container.get_config()
    
    # FastAPIアプリケーションを初期化
    app = FastAPI(
        title="エントリーシート変換アプリ (Clean Architecture)",
        description="xlsbファイルからデータを抽出し、xlsxテンプレートに転記するWebアプリケーション",
        version="2.0.0"
    )
    
    # CORS設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 静的ファイル配信を設定
    static_path = Path(__file__).parent / "src" / "web" / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    # コントローラーを取得
    file_processing_controller = container.get_file_processing_controller()
    health_controller = container.get_health_controller()
    web_controller = container.get_web_controller()
    
    @app.get("/", response_class=HTMLResponse)
    async def get_upload_form():
        """アップロードフォームを返す"""
        return web_controller.get_upload_form()
    
    @app.post("/process")
    async def process_files(
        xlsb_file: UploadFile = File(...),
        template_file: UploadFile = File(...)
    ):
        """ファイル処理エンドポイント"""
        return await file_processing_controller.process_files(xlsb_file, template_file)
    
    @app.get("/health")
    async def health_check():
        """ヘルスチェックエンドポイント"""
        return health_controller.check_health()
    
    @app.get("/config")
    async def get_config():
        """現在の設定を返す（デバッグ用）"""
        return {
            "max_file_size": config.max_file_size,
            "source_sheet_name": config.source_sheet_name,
            "target_sheet_name": config.target_sheet_name,
            "output_filename": OUTPUT_FILENAME
        }
    
    return app


# アプリケーションインスタンスを作成
app = create_app()


if __name__ == "__main__":
    config = container.get_config()
    uvicorn.run(
        "main_clean:app",
        host=config.host,
        port=config.port,
        reload=True
    )