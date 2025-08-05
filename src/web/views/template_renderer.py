"""テンプレートレンダリング機能"""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any
from ...infrastructure.config import OUTPUT_FILENAME


class TemplateRenderer:
    """HTMLテンプレートレンダリングクラス"""
    
    def __init__(self):
        # テンプレートディレクトリのパスを設定
        template_dir = Path(__file__).parent.parent / "templates"
        self._env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
    
    def render(self, template_name: str, context: Dict[str, Any] = None) -> str:
        """テンプレートをレンダリング"""
        if context is None:
            context = {}
        
        template = self._env.get_template(template_name)
        return template.render(**context)
    
    def render_upload_form(self) -> str:
        """アップロードフォームをレンダリング"""
        context = {
            "title": "エントリーシート変換アプリ",
            "max_file_size": "10MB",
            "output_filename": OUTPUT_FILENAME
        }
        return self.render("upload_form.html", context)