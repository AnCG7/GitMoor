import json
import os
import sys
import veiltk as vk
from src.utils.path_helper import get_base_path, get_user_data_path

Event = vk.Event


class LocalDataManager:
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
        # app_setting.json 是只读默认配置，位于 _runtime/ 内（通过 --add-data 打包）
        if getattr(sys, 'frozen', False):
            self.app_setting_path = os.path.join(sys._MEIPASS, "app_setting.json")
        else:
            self.app_setting_path = os.path.join(get_base_path(), "app_setting.json")
        # user_setting.json 是运行时生成的用户数据，位于 EXE 同级可写目录
        self.user_setting_path = os.path.join(get_user_data_path(), "saved", "user_setting.json")
        self.config = self.load_config()
        self.on_config_changed = Event()
        self.repo_name = ""
        self.create_result_text = ""
        self.create_result_color_type = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def load_config(self):
        if os.path.exists(self.user_setting_path):
            with open(self.user_setting_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
        else:
            user_config = {
                "bare_repo_path": "",
                "work_repo_path": "",
                "enable_lfs": False,
                "git_exe_path": "",
                "theme": "light",
                "language": "zh-Hans",
                "gitignore_template": "no_template",
                "gitattributes_template": "no_template"
            }
        
        if os.path.exists(self.app_setting_path):
            with open(self.app_setting_path, 'r', encoding='utf-8') as f:
                app_config = json.load(f)
        else:
            app_config = {
                "title": "Git仓库管理工具",
                "default_window_size": "900x600",
                "min_window_size": "800x500"
            }
        
        config = app_config.copy()
        config.update(user_config)
        return config
    
    def save_config(self):
        user_config = {
            "bare_repo_path": self.config.get("bare_repo_path", ""),
            "work_repo_path": self.config.get("work_repo_path", ""),
            "enable_lfs": self.config.get("enable_lfs", False),
            "git_exe_path": self.config.get("git_exe_path", ""),
            "theme": self.config.get("theme", "light"),
            "language": self.config.get("language", "zh-Hans"),
            "gitignore_template": self.config.get("gitignore_template", "no_template"),
            "gitattributes_template": self.config.get("gitattributes_template", "no_template")
        }
        
        os.makedirs(os.path.dirname(self.user_setting_path), exist_ok=True)
        with open(self.user_setting_path, 'w', encoding='utf-8') as f:
            json.dump(user_config, f, indent=2, ensure_ascii=False)
    
    def get_value_value(self, key, default=None):
        return self.config.get(key, default)
    
    def set_value(self, key, value):
        self.config[key] = value
        self.save_config()
        self.on_config_changed.broadcast(key, value)
    
    def update(self, config_dict):
        self.config.update(config_dict)
        self.save_config()
        for key, value in config_dict.items():
            self.on_config_changed.broadcast(key, value)
    
    def get_config(self):
        return self.config
    
    def save_path(self, path_type, path):
        self.config[path_type] = path
        self.save_config()
    
    def get_path(self, path_type, default=""):
        return self.config.get(path_type, default)
    
    def get_repo_name(self):
        return self.repo_name
    
    def set_repo_name(self, repo_name):
        self.repo_name = repo_name
    
    def get_create_result(self):
        return self.create_result_text, self.create_result_color_type
    
    def set_create_result(self, text, color_type):
        self.create_result_text = text
        self.create_result_color_type = color_type