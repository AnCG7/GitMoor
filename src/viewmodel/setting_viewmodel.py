import veiltk as vk
from src.viewmodel.base_viewmodel import BaseViewModel
from src.manager.localdata_manager import LocalDataManager
from src.manager.git_manager import GitManager
from src.utils.utils import Utils

Event = vk.Event
UIStyleManager = vk.UIStyleManager
LocalizationManager = vk.LocalizationManager


class SettingViewModel(BaseViewModel):
    def __init__(self):
        super().__init__()
        self.local_data_manager = LocalDataManager.get_instance()
        self.styles = UIStyleManager.get_instance()
        self.localization = LocalizationManager.get_instance()
        self.git_manager = GitManager.get_instance()
        self.on_settings_updated = Event()

    @staticmethod
    def _to_localized_text(message):
        formatted = Utils.format_localized_message(message)
        return vk.LocalizedText(formatted, text_type=vk.LocalizedText.TextType.STRING)
    
    def update_settings(self, theme, language, git_exe_path):
        try:
            config = self.local_data_manager.get_config()
            current_theme = config.get("theme", self.styles.default_theme)
            current_language = config.get("language", self.localization.default_language)
            current_git_path = config.get("git_exe_path", "")
            
            if theme != current_theme:
                self.styles.set_theme(theme)
                self.local_data_manager.update({"theme": theme})
            
            if language != current_language:
                self.localization.set_language(language)
                self.local_data_manager.update({"language": language})
            
            if git_exe_path != current_git_path:
                self.local_data_manager.update({"git_exe_path": git_exe_path})
            
            self.on_settings_updated.broadcast(True, vk.LocalizedText("settings_update_success"))
        except Exception as e:
            self.on_settings_updated.broadcast(False, self._to_localized_text(f"settings_update_error: {str(e)}"))
    
    def get_settings(self):
        return self.local_data_manager.get_config()
    
    def check_git_path(self, git_exe_path):
        self.git_manager.set_git_exe_path(git_exe_path)
        valid, validate_message = self.git_manager.validate_git_executable(git_exe_path)
        compatible = True
        version_message = None
        if valid:
            compatible, version_message = self.git_manager.is_version_compatible()
        return valid, self._to_localized_text(validate_message), compatible, self._to_localized_text(version_message) if version_message else None
    
    def destroy(self):
        super().destroy()
