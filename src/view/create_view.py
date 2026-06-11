import veiltk as vk
from src.view.base_view import BaseView
from src.viewmodel.create_viewmodel import CreateViewModel
from src.manager.template_manager import TemplateManager
from src.utils.utils import Utils


class CreateView(BaseView):
    def __init__(self, parent):
        self.create_viewmodel = CreateViewModel()
        self.template_manager = TemplateManager.get_instance()
        self.default_padx = 6
        self.default_pady = 6
        self._loading = None

        self._bare_repo_path = ""
        self._work_repo_path = ""
        self._repo_name = ""
        self._result_text = ""

        super().__init__(parent)

    def on_create(self):
        self.grid_columnconfigure(1, weight=1)

        bare_label = vk.Label(self, text=vk.LocalizedText("bare_repo_path"))
        bare_label.grid(row=0, column=0, sticky='w', pady=self.default_pady, padx=self.default_padx)

        saved_bare_path = self.create_viewmodel.get_path("bare_repo_path")
        self._bare_repo_path = saved_bare_path or ""
        self._create_browse_row(0, self._bare_repo_path, self.select_bare_repo_path, "_bare_repo_path")

        work_label = vk.Label(self, text=vk.LocalizedText("work_repo_path"))
        work_label.grid(row=1, column=0, sticky='w', pady=self.default_pady, padx=self.default_padx)

        saved_work_path = self.create_viewmodel.get_path("work_repo_path")
        self._work_repo_path = saved_work_path or ""
        self._create_browse_row(1, self._work_repo_path, self.select_work_repo_path, "_work_repo_path")

        repo_label = vk.Label(self, text=vk.LocalizedText("repo_name"))
        repo_label.grid(row=2, column=0, sticky='w', pady=self.default_pady, padx=self.default_padx)

        saved_repo_name = self.create_viewmodel.get_repo_name()
        self._repo_name = saved_repo_name or ""
        self._create_entry_row(2, self._repo_name)

        gitignore_label = vk.Label(self, text=vk.LocalizedText("gitignore_template"))
        gitignore_label.grid(row=3, column=0, sticky='w', pady=self.default_pady, padx=self.default_padx)

        gitignore_templates = self.template_manager.get_gitignore_templates()
        self.gitignore_combobox = self._create_template_combobox_row(3, gitignore_templates, "gitignore_template")

        enable_lfs = self.create_viewmodel.get_enable_lfs()
        checkbox = vk.CheckButton(
            self,
            text=vk.LocalizedText("enable_lfs")
        )
        if enable_lfs:
            checkbox.select()
        checkbox.on_select.add_listener(self._on_enable_lfs_changed)
        checkbox.grid(row=4, column=0, columnspan=2, sticky='w', pady=self.default_pady, padx=self.default_padx)

        gitattributes_label = vk.Label(self, text=vk.LocalizedText("gitattributes_template"))
        gitattributes_label.grid(row=5, column=0, sticky='w', pady=self.default_pady, padx=self.default_padx)

        gitattributes_templates = self.template_manager.get_gitattributes_templates()
        self.gitattributes_combobox = self._create_template_combobox_row(5, gitattributes_templates, "gitattributes_template")
        self.gitattributes_combobox.set_disabled(not enable_lfs)

        self.execute_button = vk.NormalButton(
            self,
            text=vk.LocalizedText("create"),
            style_type=vk.ButtonStyleType.Primary
        )
        self.execute_button.on_click.add_listener(self.execute)
        self.execute_button.grid(row=6, column=1, sticky='e', pady=20, padx=6)

        result_frame = vk.Frame(self)
        result_frame.grid(row=7, column=0, columnspan=3, sticky='ew', pady=10, padx=6)
        result_frame.grid_columnconfigure(0, weight=1)

        self.result_text = vk.Text(result_frame, text=vk.LocalizedText("", text_type=vk.LocalizedText.TextType.STRING), wrap_mode=vk.TextWrapMode.Char)
        self.result_text.set_mode(vk.TextMode.Label)
        self.result_text.set_selectable(True)
        self.result_text.set_copyable(True)
        self.result_text.grid(row=0, column=0, sticky='ew')

        self.copy_button = vk.NormalButton(
            result_frame,
            text=vk.LocalizedText("copy"),
            style_type=vk.ButtonStyleType.Secondary,
            size=vk.ButtonSize.Small
        )
        self.copy_button.on_click.add_listener(self.copy_error_message)
        self.copy_button.grid(row=0, column=1, padx=(10, 0), sticky='e')
        self.copy_button.hide(True)

        self._register_vm_listener(self.create_viewmodel.on_create_completed, self.on_create_completed)

        saved_text, saved_color_type = self.create_viewmodel.get_result()
        if saved_text:
            self._result_text = saved_text
            self.result_text.set_text(vk.LocalizedText(self._result_text, text_type=vk.LocalizedText.TextType.STRING))
            if saved_color_type is not None:
                fg_color = Utils.get_label_color(saved_color_type)
                self.result_text.tag_configure("msg_color", foreground=fg_color)
                self.result_text.tag_add("msg_color", "1.0", "end")
                self.copy_button.hide(saved_color_type == vk.LabelColorType.Success)

    def _create_entry_row(self, row, value):
        entry = vk.Entry(self)
        if value:
            entry.set_text(vk.LocalizedText(value, text_type=vk.LocalizedText.TextType.STRING))
        entry.on_entry_text_changed.add_listener(self._on_repo_name_changed)
        entry.on_focus_out.add_listener(lambda e=entry: self._on_entry_focus_out(e))
        entry.grid(row=row, column=1, sticky='ew', pady=self.default_pady, padx=self.default_padx)
        self._repo_name_entry = entry

    def _create_browse_row(self, row, value, command, attr_name):
        browse_entry = vk.BrowseEntry(self)
        if value:
            browse_entry.set_text(vk.LocalizedText(value, text_type=vk.LocalizedText.TextType.STRING))
        browse_entry.on_entry_text_changed.add_listener(lambda text, a=attr_name: self._on_browse_text_changed(a, text))
        browse_entry.on_focus_out.add_listener(lambda be=browse_entry, a=attr_name: self._on_browse_focus_out(be, a))
        browse_entry.on_browse_clicked.add_listener(command)
        browse_entry.grid(row=row, column=1, sticky='ew', pady=self.default_pady, padx=self.default_padx)
        setattr(self, f"{attr_name}_browse", browse_entry)

    def _create_template_combobox_row(self, row, values, setting_key):
        def template_to_display(template_key):
            if template_key in ("no_template", "empty_template"):
                return vk.LocalizedText(template_key)
            return vk.LocalizedText(template_key, text_type=vk.LocalizedText.TextType.STRING)

        combobox = vk.Combobox(self)
        combobox.set_options([template_to_display(v) for v in values])
        combobox.grid(row=row, column=1, sticky='ew', pady=self.default_pady, padx=self.default_padx)

        saved_template = self.create_viewmodel.get_template_setting(setting_key)
        if saved_template in values:
            combobox.set_selected_index(values.index(saved_template))
        elif values:
            combobox.set_selected_index(0)

        def on_template_selected(index, display):
            actual_value = values[index]
            self.create_viewmodel.save_template_setting(setting_key, actual_value)

        combobox.on_select.add_listener(on_template_selected)

        return combobox

    def _on_browse_text_changed(self, attr_name, text):
        setattr(self, attr_name, text)
        if attr_name == "_bare_repo_path":
            self.create_viewmodel.save_path("bare_repo_path", text)
        elif attr_name == "_work_repo_path":
            self.create_viewmodel.save_path("work_repo_path", text)

    def _on_browse_focus_out(self, browse_entry, attr_name):
        """失去焦点时矫正路径：去除首尾空白"""
        current = getattr(self, attr_name, "")
        normalized = self.create_viewmodel.normalize_text(current)
        if normalized != current:
            setattr(self, attr_name, normalized)
            browse_entry.set_text(vk.LocalizedText(normalized, text_type=vk.LocalizedText.TextType.STRING))
            if attr_name == "_bare_repo_path":
                self.create_viewmodel.save_path("bare_repo_path", normalized)
            elif attr_name == "_work_repo_path":
                self.create_viewmodel.save_path("work_repo_path", normalized)

    def _on_entry_focus_out(self, entry):
        """失去焦点时矫正仓库名：去除首尾空白"""
        normalized = self.create_viewmodel.normalize_text(self._repo_name)
        if normalized != self._repo_name:
            self._repo_name = normalized
            entry.set_text(vk.LocalizedText(normalized, text_type=vk.LocalizedText.TextType.STRING))
            self.create_viewmodel.set_repo_name(normalized)

    def _on_repo_name_changed(self, text):
        self._repo_name = text
        self.create_viewmodel.set_repo_name(text)

    def select_bare_repo_path(self):
        path = Utils.askdirectory()
        if path:
            self._bare_repo_path = path
            self._bare_repo_path_browse.set_text(vk.LocalizedText(path, text_type=vk.LocalizedText.TextType.STRING))
            self.create_viewmodel.save_path("bare_repo_path", path)

    def select_work_repo_path(self):
        path = Utils.askdirectory()
        if path:
            self._work_repo_path = path
            self._work_repo_path_browse.set_text(vk.LocalizedText(path, text_type=vk.LocalizedText.TextType.STRING))
            self.create_viewmodel.save_path("work_repo_path", path)

    def toggle_gitattributes(self, enable):
        self.gitattributes_combobox.set_disabled(not enable)
        self.create_viewmodel.set_enable_lfs(enable)

    def execute(self):
        # 点击创建前矫正所有输入值并更新界面
        bare = self.create_viewmodel.normalize_text(self._bare_repo_path)
        work = self.create_viewmodel.normalize_text(self._work_repo_path)
        name = self.create_viewmodel.normalize_text(self._repo_name)

        if bare != self._bare_repo_path:
            self._bare_repo_path = bare
            self._bare_repo_path_browse.set_text(vk.LocalizedText(bare, text_type=vk.LocalizedText.TextType.STRING))
            self.create_viewmodel.save_path("bare_repo_path", bare)
        if work != self._work_repo_path:
            self._work_repo_path = work
            self._work_repo_path_browse.set_text(vk.LocalizedText(work, text_type=vk.LocalizedText.TextType.STRING))
            self.create_viewmodel.save_path("work_repo_path", work)
        if name != self._repo_name:
            self._repo_name = name
            self._repo_name_entry.set_text(vk.LocalizedText(name, text_type=vk.LocalizedText.TextType.STRING))
            self.create_viewmodel.set_repo_name(name)

        gitignore_template = self.create_viewmodel.get_template_setting("gitignore_template")
        enable_lfs = self.create_viewmodel.get_enable_lfs()
        gitattributes_template = self.create_viewmodel.get_template_setting("gitattributes_template")

        self._loading = vk.Loading(
            master=self,
            message=vk.LocalizedText("creating_repo"),
            style_type=vk.LoadingStyle.Rect
        )
        self._loading.get_root_tk().grab_set()
        self.after(100, lambda: self._do_create(
            self._bare_repo_path, self._work_repo_path, self._repo_name,
            gitignore_template, enable_lfs, gitattributes_template
        ))

    def _do_create(self, bare_repo_path, work_repo_path, repo_name,
                   gitignore_template, enable_lfs, gitattributes_template):
        self.create_viewmodel.create_repo(
            bare_repo_path, work_repo_path, repo_name,
            gitignore_template, enable_lfs, gitattributes_template
        )

    def on_create_completed(self, success, message):
        if self._loading is not None:
            self._loading.close()
            self._loading = None

        if success:
            self._result_text = f"{vk.LocalizedText('success').get_text()}: {message.get_text()}"
            self.result_text.set_text(vk.LocalizedText(self._result_text, text_type=vk.LocalizedText.TextType.STRING))
            self._apply_result_color(vk.LabelColorType.Success)
            self.copy_button.hide(True)
            self.create_viewmodel.save_result(self._result_text, vk.LabelColorType.Success)
        else:
            self._result_text = f"{vk.LocalizedText('failed').get_text()}: {message.get_text()}"
            self.result_text.set_text(vk.LocalizedText(self._result_text, text_type=vk.LocalizedText.TextType.STRING))
            self._apply_result_color(vk.LabelColorType.Error)
            self.copy_button.hide(False)
            self.create_viewmodel.save_result(self._result_text, vk.LabelColorType.Error)

    def _apply_result_color(self, color_type):
        """通过 tag 为 result_text 设置前景色"""
        fg_color = Utils.get_label_color(color_type)
        self.result_text.tag_configure("msg_color", foreground=fg_color)
        self.result_text.tag_add("msg_color", "1.0", "end")

    def copy_error_message(self):
        if self._result_text:
            Utils.clipboard_copy(self._result_text)

    def _on_enable_lfs_changed(self):
        current = self.create_viewmodel.get_enable_lfs()
        new_value = not current
        self.toggle_gitattributes(new_value)

    def on_destroy(self):
        pass
