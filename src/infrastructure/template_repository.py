"""テンプレート管理リポジトリ"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from ..domain.entities import TemplateInfo, TemplateMapping, CellMapping


class TemplateRepository:
    """テンプレート管理リポジトリ"""
    
    def __init__(self, templates_dir: str = "src/templates"):
        self.templates_dir = Path(templates_dir)
        self.config_file = self.templates_dir / "template_config.json"
        self._templates_cache: Optional[Dict[str, TemplateInfo]] = None
    
    def get_all_templates(self) -> List[TemplateInfo]:
        """全てのテンプレート情報を取得"""
        self._load_templates_if_needed()
        return [template for template in self._templates_cache.values() if template.is_active]
    
    def get_template(self, template_id: str) -> Optional[TemplateInfo]:
        """指定されたIDのテンプレート情報を取得"""
        self._load_templates_if_needed()
        return self._templates_cache.get(template_id)
    
    def get_template_file_path(self, template_id: str) -> Optional[Path]:
        """テンプレートファイルのパスを取得"""
        template = self.get_template(template_id)
        if template:
            return self.templates_dir / template.filename
        return None
    
    def get_template_content(self, template_id: str) -> Optional[bytes]:
        """テンプレートファイルの内容を取得"""
        file_path = self.get_template_file_path(template_id)
        if file_path and file_path.exists():
            with open(file_path, 'rb') as f:
                return f.read()
        
        # ファイルが見つからない場合の詳細なエラー情報
        template = self.get_template(template_id)
        if template:
            raise FileNotFoundError(
                f"テンプレートファイルが見つかりません: {template.filename}\n"
                f"期待されるパス: {file_path}\n"
                f"テンプレートディレクトリ: {self.templates_dir}\n"
                f"テンプレートファイルを {self.templates_dir} ディレクトリに配置してください。"
            )
        else:
            raise ValueError(f"テンプレートID '{template_id}' が見つかりません。")
    
    def _load_templates_if_needed(self):
        """必要に応じてテンプレート設定を読み込み"""
        if self._templates_cache is None:
            self._load_templates()
    
    def _load_templates(self):
        """テンプレート設定ファイルを読み込み"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self._templates_cache = {}
            for template_data in config_data.get('templates', []):
                # マッピング情報を処理
                mapping = None
                if 'mapping' in template_data:
                    mapping_data = template_data['mapping']
                    cell_mappings = []
                    
                    for cell_data in mapping_data.get('cell_mappings', []):
                        cell_mapping = CellMapping(
                            target=cell_data['target'],
                            source=cell_data['source'],
                            type=cell_data.get('type', 'single'),
                            separator=cell_data.get('separator', ''),
                            format_rules=cell_data.get('format_rules', {})
                        )
                        cell_mappings.append(cell_mapping)
                    
                    mapping = TemplateMapping(
                        source_sheet=mapping_data['source_sheet'],
                        target_sheet=mapping_data['target_sheet'],
                        target_row=mapping_data['target_row'],
                        cell_mappings=cell_mappings,
                        multi_file_start_row=mapping_data.get('multi_file_start_row')
                    )
                
                template = TemplateInfo(
                    id=template_data['id'],
                    name=template_data['name'],
                    filename=template_data['filename'],
                    output_filename=template_data['output_filename'],
                    description=template_data['description'],
                    is_active=template_data.get('is_active', True),
                    mapping=mapping
                )
                self._templates_cache[template.id] = template
                
        except Exception as e:
            raise Exception(f"テンプレート設定の読み込みに失敗しました: {str(e)}")
    
    def reload_templates(self):
        """テンプレート設定を再読み込み"""
        self._templates_cache = None
        self._load_templates()