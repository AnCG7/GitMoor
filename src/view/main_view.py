import veiltk as vk
from enum import Enum
from src.view.base_view import BaseView
from src.view.create_view import CreateView
from src.view.setting_view import SettingView
from src.view.aboutus_view import AboutView
from src.viewmodel.main_viewmodel import MainViewModel
from src.utils.utils import Utils


class Page(Enum):
    CREATE = 0
    SETTING = 1
    ABOUT = 2


class MainView(BaseView):
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.main_viewmodel = MainViewModel.get_instance()
        self.custom_menu = None

        super().__init__(root)

        vk.App.get_instance().on_close.add_listener(self.on_closing)

        self.show_page(Page.CREATE)

    def on_create(self):
        self.pack(fill='both', expand=True)

        menu_items = [
            {'text': vk.LocalizedText("create"), 'page': CreateView},
            {'text': vk.LocalizedText("settings"), 'page': SettingView},
            {'text': vk.LocalizedText("about"), 'page': AboutView}
        ]

        self.custom_menu = vk.Menu(
            self,
            menu_items=menu_items,
            position=vk.MenuPosition.Left,
            page_mode=vk.PageMode.Destroy,
            initial_item_index=Page.CREATE.value
        )
        self.custom_menu.on_select.add_listener(self.on_menu_select)
        self.custom_menu.pack(fill='both', expand=True)

        self.after(100, self._check_git_on_startup)

    def _check_git_on_startup(self):
        success, git_path, message = self.main_viewmodel.check_git_on_startup()

        if success and git_path:
            # 自动找到 Git：弹窗告知用户路径，并提醒可在设置中更改
            success_msg = Utils.format_localized_message(f"git_auto_found_success: {git_path}")
            vk.Alert.show_normal(
                master=self,
                title=vk.LocalizedText("git_check"),
                message=vk.LocalizedText(success_msg, text_type=vk.LocalizedText.TextType.STRING)
            )
        elif not success:
            vk.Alert.show_normal(
                master=self,
                title=vk.LocalizedText("git_check"),
                message=message
            )

    def on_start(self):
        pass

    def on_stop(self):
        pass

    def on_destroy(self):
        pass

    def on_menu_select(self, selected_index, selected_text, page_instance):
        pass

    def show_page(self, page):
        if self.custom_menu:
            self.custom_menu.select_item(page.value)

    def on_closing(self):
        self.destroy()
        vk.App.get_instance().shutdown()
