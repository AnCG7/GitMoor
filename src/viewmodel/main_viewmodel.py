import veiltk as vk
from src.viewmodel.base_viewmodel import BaseViewModel
from src.manager.localdata_manager import LocalDataManager
from src.manager.git_manager import GitManager
from src.utils.utils import Utils


class MainViewModel(BaseViewModel):
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        self.local_data_manager = LocalDataManager.get_instance()
        self.git_manager = GitManager.get_instance()
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @staticmethod
    def _to_localized_text(message):
        formatted = Utils.format_localized_message(message)
        return vk.LocalizedText(formatted, text_type=vk.LocalizedText.TextType.STRING)
    
    def get_config(self):
        return self.local_data_manager.get_config()
    
    def update_config(self, config):
        self.local_data_manager.update(config)
        return True
    
    def get_git_exe_path(self):
        config = self.get_config()
        return config.get("git_exe_path", "")
    
    def set_git_exe_path(self, git_exe_path):
        config = self.get_config()
        config["git_exe_path"] = git_exe_path
        return self.update_config(config)
    
    def check_git_on_startup(self):
        saved_git_path = self.get_git_exe_path()
        enable_lfs = self.local_data_manager.get_value_value("enable_lfs", False)
        success, git_path, message = self.git_manager.check_git_on_startup(saved_git_path, enable_lfs)
        
        if success and git_path:
            self.set_git_exe_path(git_path)
        
        return success, git_path, self._to_localized_text(message)
    
    def destroy(self):
        super().destroy()
