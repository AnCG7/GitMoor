import veiltk as vk
from src.view.base_view import BaseView
from src.viewmodel.setting_viewmodel import SettingViewModel
from src.utils.utils import Utils
from src.manager.git_manager import GitManager


class SettingView(BaseView):
    def __init__(self, parent):
        self.styles = vk.UIStyleManager.get_instance()
        self.localization = vk.LocalizationManager.get_instance()
        self.setting_viewmodel = SettingViewModel()
        self._is_loading = False
        self.default_padx = 6
        self.default_pady = 6

        self._git_exe_path = ""

        super().__init__(parent)

    def on_create(self):
        self.grid_columnconfigure(1, weight=1)

        theme_label = vk.Label(self, text=vk.LocalizedText("theme"))
        theme_label.grid(row=0, column=0, sticky='w', pady=self.default_pady, padx=self.default_padx)

        self.theme_combobox = self._create_theme_combobox(0)

        language_label = vk.Label(self, text=vk.LocalizedText("language"))
        language_label.grid(row=1, column=0, sticky='w', pady=self.default_pady, padx=self.default_padx)

        self.language_combobox = self._create_language_combobox(1)

        git_path_label = vk.Label(self, text=vk.LocalizedText("git_exe_path"))
        git_path_label.grid(row=2, column=0, sticky='w', pady=self.default_pady, padx=self.default_padx)

        self._create_browse_row(2, self.select_git_exe)

        self.git_check_text = vk.Text(self, text=vk.LocalizedText("git_path_not_set"), wrap_mode=vk.TextWrapMode.Char)
        self.git_check_text.set_mode(vk.TextMode.Label)
        self.git_check_text.set_selectable_copyable(True)
        self.git_check_text.grid(row=3, column=0, columnspan=3, sticky='ew', pady=self.default_pady, padx=self.default_padx)

        self._register_vm_listener(self.setting_viewmodel.on_settings_updated, self.on_settings_updated)

        self.load_settings()

        self.theme_combobox.on_select.add_listener(self._on_theme_selected)
        self.language_combobox.on_select.add_listener(self._on_language_selected)

    def _create_theme_combobox(self, row):
        themes = self.styles.supported_themes
        combobox = vk.Combobox(self)
        combobox.set_options([vk.LocalizedText(t) for t in themes])
        combobox.grid(row=row, column=1, sticky='ew', pady=self.default_pady, padx=self.default_padx)

        return combobox

    def _create_language_combobox(self, row):
        languages = self.localization.supported_languages
        combobox = vk.Combobox(self)
        combobox.set_options([vk.LocalizedText(f"language_{lang}") for lang in languages])
        combobox.grid(row=row, column=1, sticky='ew', pady=self.default_pady, padx=self.default_padx)

        return combobox

    def _create_browse_row(self, row, command):
        self._git_exe_browse = vk.BrowseEntry(self)
        self._git_exe_browse.on_entry_text_changed.add_listener(self._on_git_path_changed)
        self._git_exe_browse.on_browse_clicked.add_listener(command)
        self._git_exe_browse.grid(row=row, column=1, sticky='ew', pady=self.default_pady, padx=self.default_padx)

    def load_settings(self):
        self._is_loading = True
        settings = self.setting_viewmodel.get_settings()

        theme = settings.get("theme", self.styles.default_theme)
        themes = self.styles.supported_themes
        if theme in themes:
            theme_index = themes.index(theme)
            self.theme_combobox.set_selected_index(theme_index)

        language = settings.get("language", self.localization.default_language)
        languages = self.localization.supported_languages
        if language in languages:
            lang_index = languages.index(language)
            self.language_combobox.set_selected_index(lang_index)

        git_path = settings.get("git_exe_path", "")
        self._git_exe_path = git_path
        if git_path:
            self._git_exe_browse.set_text(vk.LocalizedText(git_path, text_type=vk.LocalizedText.TextType.STRING))
        self._is_loading = False

        self.check_git_path(git_path)

    def select_git_exe(self):
        path = Utils.askopenfilename(filetypes=GitManager.get_executable_filetypes())
        if path:
            self._git_exe_path = path
            self._git_exe_browse.set_text(vk.LocalizedText(path, text_type=vk.LocalizedText.TextType.STRING))
            self._update_settings()

    def check_git_path(self, git_exe_path):
        git_message = ""
        color_type = vk.LabelColorType.Warning
        if git_exe_path:
            valid, validate_message, compatible, version_message = self.setting_viewmodel.check_git_path(git_exe_path)
            if valid:
                if not compatible:
                    git_message = f"{vk.LocalizedText('git_version_incompatible').get_text()}\n{version_message.get_text()}"
                else:
                    git_message = validate_message.get_text()
                    color_type = vk.LabelColorType.Success
            else:
                git_message = validate_message.get_text()
                color_type = vk.LabelColorType.Error
        else:
            git_message = vk.LocalizedText("git_path_not_set").get_text()

        self.git_check_text.set_text(vk.LocalizedText(git_message, text_type=vk.LocalizedText.TextType.STRING))
        fg_color = Utils.get_label_color(color_type)
        self.git_check_text.tag_configure("msg_color", foreground=fg_color)
        self.git_check_text.tag_add("msg_color", "1.0", "end")

    def _on_theme_selected(self, index, value):
        if self._is_loading:
            return
        self._update_settings()

    def _on_language_selected(self, index, value):
        if self._is_loading:
            return
        self._update_settings()

    def _on_git_path_changed(self, text):
        if self._is_loading:
            return
        self._git_exe_path = text
        self._update_settings()

    def _update_settings(self):
        themes = self.styles.supported_themes
        languages = self.localization.supported_languages

        theme_index = self.theme_combobox.get_selected_index()
        theme = themes[theme_index] if 0 <= theme_index < len(themes) else 'light'

        lang_index = self.language_combobox.get_selected_index()
        language = languages[lang_index] if 0 <= lang_index < len(languages) else 'zh-Hans'

        self.setting_viewmodel.update_settings(theme, language, self._git_exe_path)

    def on_settings_updated(self, success, message):
        if success:
            settings = self.setting_viewmodel.get_settings()
            git_exe_path = settings.get("git_exe_path", "")
            self.check_git_path(git_exe_path)

    def on_destroy(self):
        pass
