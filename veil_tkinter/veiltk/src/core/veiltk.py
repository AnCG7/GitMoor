import os
from .manager.localization_manager import LocalizationManager


class VeilTk:
    _project_path = None
    _initialized = False

    @classmethod
    def setup(cls, project_path):
        cls._project_path = os.path.abspath(project_path)
        cls._initialized = True

        localization_path = os.path.join(cls._project_path, "assets", "localization")
        LocalizationManager.get_instance().set_localization_path(localization_path)

    @classmethod
    def get_project_path(cls):
        return cls._project_path
