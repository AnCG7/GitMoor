import os
from src.utils.path_helper import get_base_path

class TemplateManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        base = get_base_path()
        self.gitignore_templates_dir = os.path.join(base, "assets", "templates", "gitignore")
        self.gitattributes_templates_dir = os.path.join(base, "assets", "templates", "gitattributes")
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def get_gitignore_templates(self):
        special_templates = ["no_template", "empty_template"]
        custom_templates = []
        if os.path.exists(self.gitignore_templates_dir):
            for file in os.listdir(self.gitignore_templates_dir):
                if file.endswith(".gitignore"):
                    template_name = file.replace(".gitignore", "")
                    custom_templates.append(template_name)
        # 对自定义模板按字母顺序排序
        custom_templates.sort()
        # 组合特殊模板和排序后的自定义模板
        return special_templates + custom_templates
    
    def get_gitattributes_templates(self):
        special_templates = ["no_template", "empty_template"]
        custom_templates = []
        if os.path.exists(self.gitattributes_templates_dir):
            for file in os.listdir(self.gitattributes_templates_dir):
                if file.endswith(".gitattributes"):
                    template_name = file.replace(".gitattributes", "")
                    custom_templates.append(template_name)
        # 对自定义模板按字母顺序排序
        custom_templates.sort()
        # 组合特殊模板和排序后的自定义模板
        return special_templates + custom_templates
    
    def get_template_content(self, template_type, template_name):
        if template_name == "no_template":
            return None
        elif template_name == "empty_template":
            return ""
        
        if template_type == "gitignore":
            template_dir = self.gitignore_templates_dir
            extension = ".gitignore"
        elif template_type == "gitattributes":
            template_dir = self.gitattributes_templates_dir
            extension = ".gitattributes"
        else:
            return None
        
        template_path = os.path.join(template_dir, f"{template_name}{extension}")
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
