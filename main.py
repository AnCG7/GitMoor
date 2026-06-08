import sys
import os

# PyInstaller 打包时，veiltk 已通过 --paths / --collect-submodules 打包进 _internal/，
# 无需手动添加到 sys.path。
if not getattr(sys, 'frozen', False):
    veiltk_dir = os.path.join(os.path.dirname(__file__), "veil_tkinter")
    sys.path.insert(0, veiltk_dir)

import veiltk as vk
from src.manager.localdata_manager import LocalDataManager
from src.view.main_view import MainView
from src.utils.path_helper import get_base_path


class GitMoor:
    def __init__(self):
        # get_base_path() 在开发和打包环境下都能返回正确的资源根目录
        base_path = get_base_path()
        vk.setup(base_path)

        self.local_data_manager = LocalDataManager.get_instance()
        config = self.local_data_manager.get_config()

        saved_theme = config.get("theme", "light")
        saved_language = config.get("language", "zh-Hans")

        vk.UIStyleManager.get_instance().set_theme(saved_theme)
        vk.LocalizationManager.get_instance().set_language(saved_language)

        assets_dir = os.path.join(base_path, "assets")
        icon_dir = os.path.join(assets_dir, "images", "icon")
        icon_paths = [
            os.path.join(icon_dir, "icon16.png"),
            os.path.join(icon_dir, "icon32.png"),
            os.path.join(icon_dir, "icon64.png"),
            os.path.join(icon_dir, "icon256.png"),
        ]
        self.app = vk.App(
            title=vk.LocalizedText("app_title", text_type=vk.LocalizedText.TextType.LOCALIZED),
            width=900,
            height=600,
            icons=icon_paths
        )

        root_tk = self.app.get_root_tk()
        min_size = config.get("min_window_size", "800x500").split("x")
        self.app.set_min_size(int(min_size[0]), int(min_size[1]))

        self.app.center_on_screen()
        self.main_view = MainView(self.app, config)

    def run(self):
        self.app.run()


if __name__ == "__main__":
    app = GitMoor()
    app.run()
