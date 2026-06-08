import sys
import os
import tkinter as tk

demo_dir = os.path.dirname(os.path.abspath(__file__))
veiltk_dir = os.path.dirname(demo_dir)
sys.path.insert(0, veiltk_dir)

import veiltk as vk
from veiltk.src.components.progress import Orientation


class ThemeSwitcher(vk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self._setup_ui()

    def _setup_ui(self):
        vk.Label(self, text=vk.LocalizedText("样式切换:")).pack(side='left', padx=(0, 10))

        self._light_btn = vk.NormalButton(
            self,
            text=vk.LocalizedText("Light"),
            size=vk.ButtonSize.Small
        )
        self._light_btn.on_click.add_listener(self._on_light_click)
        self._light_btn.pack(side='left', padx=5)

        self._dark_btn = vk.NormalButton(
            self,
            text=vk.LocalizedText("Dark"),
            size=vk.ButtonSize.Small
        )
        self._dark_btn.on_click.add_listener(self._on_dark_click)
        self._dark_btn.pack(side='left', padx=5)

        self._update_buttons()

    def _update_buttons(self):
        current_theme = vk.UIStyleManager.get_instance().get_theme()
        if current_theme == 'light':
            self._light_btn.set_disabled(True)
            self._dark_btn.set_disabled(False)
        else:
            self._light_btn.set_disabled(False)
            self._dark_btn.set_disabled(True)

    def _on_light_click(self):
        vk.UIStyleManager.get_instance().set_theme('light')
        self._update_buttons()

    def _on_dark_click(self):
        vk.UIStyleManager.get_instance().set_theme('dark')
        self._update_buttons()


class ButtonPage(vk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self._setup_ui()

    def _setup_ui(self):
        vk.Label(self, text=vk.LocalizedText("Button 组件演示")).pack(anchor='w', pady=(0, 10))

        vk.NormalButton(
            self,
            text=vk.LocalizedText("普通按钮"),
            style_type=vk.ButtonStyleType.Primary,
            size=vk.ButtonSize.Normal
        ).pack(pady=5)

        vk.NormalButton(
            self,
            text=vk.LocalizedText("次要按钮"),
            style_type=vk.ButtonStyleType.Secondary,
            size=vk.ButtonSize.Normal
        ).pack(pady=5)

        btn = vk.NormalButton(
            self,
            text=vk.LocalizedText("禁用按钮"),
            style_type=vk.ButtonStyleType.Primary
        )
        btn.set_disabled(True)
        btn.pack(pady=5)

        vk.NormalButton(
            self,
            text=vk.LocalizedText("小按钮"),
            size=vk.ButtonSize.Small
        ).pack(pady=5)

        vk.NormalButton(
            self,
            text=vk.LocalizedText("大按钮"),
            size=vk.ButtonSize.Large
        ).pack(pady=5)


class EntryPage(vk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self._setup_ui()

    def _setup_ui(self):
        vk.Label(self, text=vk.LocalizedText("Entry 组件演示")).pack(anchor='w', pady=(0, 10))

        vk.Label(self, text=vk.LocalizedText("普通输入框:")).pack(anchor='w')
        vk.Entry(self).pack(fill='x', pady=5)

        vk.Label(self, text=vk.LocalizedText("禁用输入框:")).pack(anchor='w')
        entry = vk.Entry(self)
        entry.set_disabled(True)
        entry.pack(fill='x', pady=5)

        vk.Label(self, text=vk.LocalizedText("只读输入框:")).pack(anchor='w')
        entry = vk.Entry(self)
        entry.set_is_readonly(True)
        entry.set_text(vk.LocalizedText("只读内容"))
        entry.pack(fill='x', pady=5)


class TextPage(vk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self._setup_ui()

    def _setup_ui(self):
        vk.Label(self, text=vk.LocalizedText("Text 组件演示")).pack(anchor='w', pady=(0, 10))

        vk.Label(self, text=vk.LocalizedText("普通编辑模式 (Normal):")).pack(anchor='w')
        text_normal = vk.Text(self, wrap_mode=vk.TextWrapMode.Word)
        text_normal.set_width(50)
        text_normal.set_line_height(3)
        text_normal.insert('1.0', "这是普通编辑模式，支持多行编辑、撤销重做、复制粘贴。\nTab 键插入制表符，Ctrl+Tab 切换焦点。")
        text_normal.pack(fill='x', pady=(0, 10))

        vk.Label(self, text=vk.LocalizedText("只读模式 (Readonly) - 可选中可复制:")).pack(anchor='w')
        text_ro = vk.Text(self)
        text_ro.set_mode(vk.TextMode.Readonly)
        text_ro.set_width(50)
        text_ro.set_line_height(2)
        text_ro.insert('1.0', "只读模式下可以选中文本并复制，但不可编辑。\n适合展示日志、配置文件等内容。")
        text_ro.pack(fill='x', pady=(0, 10))

        vk.Label(self, text=vk.LocalizedText("禁用模式 (Disable):")).pack(anchor='w')
        text_disabled = vk.Text(self)
        text_disabled.set_mode(vk.TextMode.Disable)
        text_disabled.set_width(50)
        text_disabled.set_line_height(2)
        text_disabled.insert('1.0', "禁用模式下不可交互、不可选择、不可聚焦。")
        text_disabled.pack(fill='x', pady=(0, 10))

        vk.Label(self, text=vk.LocalizedText("标签模式 (Label) - 无边框装饰:")).pack(anchor='w')
        text_label = vk.Text(self)
        text_label.set_mode(vk.TextMode.Label)
        text_label.set_width(50)
        text_label.set_line_height(2)
        text_label.insert('1.0', "Label 模式去掉边框装饰，适合作为信息展示面板。")
        text_label.pack(fill='x', pady=(0, 10))

        vk.Label(self, text=vk.LocalizedText("富文本 - set_text + tag_add:")).pack(anchor='w', pady=(5, 0))
        text_rich = vk.Text(self, wrap_mode=vk.TextWrapMode.Word)
        text_rich.set_mode(vk.TextMode.Readonly)
        text_rich.set_width(50)
        text_rich.set_line_height(5)
        text_rich.set_text(vk.LocalizedText(
            "红色大字 + 蓝色斜体 + 绿色下划线\n"
            "这是一个多色多风格的富文本演示。\n"
            "不同标签可以叠加在同一段文字上。\n"
            "补充一些文字超过高度。\n"
            "补充一些文字超过高度。\n"
        ))
        text_rich.tag_configure('red_big', foreground='red', font=('Arial', 14, 'bold'))
        text_rich.tag_configure('blue_italic', foreground='blue', font=('Arial', 12, 'italic'))
        text_rich.tag_configure('green_underline', foreground='green', font=('Arial', 12, 'underline'))
        text_rich.tag_add('red_big', '1.0', '1.4')
        text_rich.tag_add('blue_italic', '1.7', '1.11')
        text_rich.tag_add('green_underline', '1.13', '1.17')
        text_rich.pack(fill='x')


class ComboboxPage(vk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self._setup_ui()

    def _setup_ui(self):
        vk.Label(self, text=vk.LocalizedText("Combobox 组件演示")).pack(anchor='w', pady=(0, 10))

        vk.Label(self, text=vk.LocalizedText("普通下拉框:")).pack(anchor='w')
        combo = vk.Combobox(self)
        combo.set_options([vk.LocalizedText("选项 1"), vk.LocalizedText("选项 2"), vk.LocalizedText("选项 3"), vk.LocalizedText("选项 4")])
        combo.pack(fill='x', pady=5)

        vk.Label(self, text=vk.LocalizedText("禁用下拉框:")).pack(anchor='w')
        combo = vk.Combobox(self)
        combo.set_options([vk.LocalizedText("禁用选项 A"), vk.LocalizedText("禁用选项 B")])
        combo.set_disabled(True)
        combo.pack(fill='x', pady=5)


class CheckButtonPage(vk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self._setup_ui()

    def _setup_ui(self):
        vk.Label(self, text=vk.LocalizedText("CheckButton 组件演示")).pack(anchor='w', pady=(0, 10))

        vk.CheckButton(self, text=vk.LocalizedText("普通复选框")).pack(anchor='w', pady=5)

        check = vk.CheckButton(self, text=vk.LocalizedText("已选中复选框"))
        check.select()
        check.pack(anchor='w', pady=5)

        check = vk.CheckButton(self, text=vk.LocalizedText("禁用复选框"))
        check.set_disabled(True)
        check.pack(anchor='w', pady=5)

        check = vk.CheckButton(self, text=vk.LocalizedText("禁用已选中"))
        check.select()
        check.set_disabled(True)
        check.pack(anchor='w', pady=5)


class LinkButtonPage(vk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self._setup_ui()

    def _setup_ui(self):
        vk.Label(self, text=vk.LocalizedText("LinkButton 组件演示")).pack(anchor='w', pady=(0, 10))

        vk.LinkButton(
            self,
            text=vk.LocalizedText("普通链接按钮"),
            url="https://www.example.com"
        ).pack(anchor='w', pady=5)

        btn = vk.LinkButton(self, text=vk.LocalizedText("禁用链接按钮"))
        btn.set_disabled(True)
        btn.pack(anchor='w', pady=5)


class ScrollListboxPage(vk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self._setup_ui()

    def _setup_ui(self):
        vk.Label(self, text=vk.LocalizedText("ScrollListbox 组件演示")).pack(anchor='w', pady=(0, 10))

        vk.Label(self, text=vk.LocalizedText("普通列表:")).pack(anchor='w')
        listbox = vk.ScrollListbox(self, height=5)
        for i in range(1, 15):
            listbox.insert("end", vk.LocalizedText(f"列表项 {i}"))
        listbox.pack(fill='both', expand=True, pady=5)

        vk.Label(self, text=vk.LocalizedText("禁用列表:")).pack(anchor='w')
        listbox = vk.ScrollListbox(self, height=5)
        for i in range(1, 15):
            listbox.insert("end", vk.LocalizedText(f"禁用项 {i}"))
        listbox.set_disabled(True)
        listbox.pack(fill='both', expand=True, pady=5)


class ProgressPage(vk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self._setup_ui()

    def _setup_ui(self):
        vk.Label(self, text=vk.LocalizedText("Progress 组件演示")).pack(anchor='w', pady=(0, 10))

        vk.Label(self, text=vk.LocalizedText("水平进度条 (0%):")).pack(anchor='w')
        self._progress_0 = vk.Progress(self, orientation=Orientation.Horizontal)
        self._progress_0.set_value(0.0)
        self._progress_0.pack(fill='x', pady=5)

        vk.Label(self, text=vk.LocalizedText("水平进度条 (50%):")).pack(anchor='w')
        self._progress_50 = vk.Progress(self, orientation=Orientation.Horizontal)
        self._progress_50.set_value(0.5)
        self._progress_50.pack(fill='x', pady=5)

        vk.Label(self, text=vk.LocalizedText("水平进度条 (100%):")).pack(anchor='w')
        self._progress_100 = vk.Progress(self, orientation=Orientation.Horizontal)
        self._progress_100.set_value(1.0)
        self._progress_100.pack(fill='x', pady=5)

        vk.Label(self, text=vk.LocalizedText("禁用进度条:")).pack(anchor='w')
        progress_disabled = vk.Progress(self, orientation=Orientation.Horizontal)
        progress_disabled.set_value(0.6)
        progress_disabled.set_disabled(True)
        progress_disabled.pack(fill='x', pady=5)


class MessageBoxPage(vk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self._setup_ui()

    def _setup_ui(self):
        vk.Label(self, text=vk.LocalizedText("MessageBox 组件演示")).pack(anchor='w', pady=(0, 10))

        btn_confirm = vk.NormalButton(
            self,
            text=vk.LocalizedText("确认对话框 (Confirm)"),
            style_type=vk.ButtonStyleType.Primary
        )
        btn_confirm.on_click.add_listener(self._on_confirm)
        btn_confirm.pack(pady=5)

        btn_normal = vk.NormalButton(
            self,
            text=vk.LocalizedText("普通对话框 (Normal)"),
            style_type=vk.ButtonStyleType.Primary
        )
        btn_normal.on_click.add_listener(self._on_normal)
        btn_normal.pack(pady=5)

        btn_long = vk.NormalButton(
            self,
            text=vk.LocalizedText("超长内容对话框"),
            style_type=vk.ButtonStyleType.Primary
        )
        btn_long.on_click.add_listener(self._on_long_content)
        btn_long.pack(pady=5)

        btn_rect = vk.NormalButton(
            self,
            text=vk.LocalizedText("Loading - Rect"),
            style_type=vk.ButtonStyleType.Primary
        )
        btn_rect.on_click.add_listener(self._on_loading_rect)
        btn_rect.pack(pady=5)

        btn_chase = vk.NormalButton(
            self,
            text=vk.LocalizedText("Loading - Chase"),
            style_type=vk.ButtonStyleType.Primary
        )
        btn_chase.on_click.add_listener(self._on_loading_chase)
        btn_chase.pack(pady=5)

        btn_line = vk.NormalButton(
            self,
            text=vk.LocalizedText("Loading - Line"),
            style_type=vk.ButtonStyleType.Primary
        )
        btn_line.on_click.add_listener(self._on_loading_line)
        btn_line.pack(pady=5)

    def _on_confirm(self):
        vk.Alert.show_confirm(
            master=self,
            title=vk.LocalizedText("确认"),
            content=vk.LocalizedText("确定要执行此操作吗？")
        )

    def _on_normal(self):
        vk.Alert.show_normal(
            master=self,
            title=vk.LocalizedText("提示"),
            message=vk.LocalizedText("操作已完成。")
        )

    def _on_loading_rect(self):
        vk.Loading.show(
            master=self,
            message=vk.LocalizedText("加载中..."),
            style_type=vk.LoadingStyle.Rect,
            duration=3
        )

    def _on_loading_chase(self):
        vk.Loading.show(
            master=self,
            message=vk.LocalizedText("加载中..."),
            style_type=vk.LoadingStyle.Chase,
            duration=3
        )

    def _on_loading_line(self):
        vk.Loading.show(
            master=self,
            message=vk.LocalizedText("加载中..."),
            style_type=vk.LoadingStyle.Line,
            duration=3
        )

    def _on_long_content(self):
        vk.Alert.show_normal(
            master=self,
            title=vk.LocalizedText("提示"),
            message=vk.LocalizedText("这是一段超长的提示内容，用于测试 Alert 组件在内容较多时的显示效果。当消息文本非常长的时候，Alert 窗口应该能够自动调整高度以适应内容，同时保持宽度固定，文字自动换行。这个功能确保了用户能够完整阅读所有提示信息，而不会因为窗口大小限制导致内容被截断。感谢您的耐心阅读！测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容测试填充内容")
        )


class LabelPage(vk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self._setup_ui()

    def _setup_ui(self):
        vk.Label(self, text=vk.LocalizedText("Label 组件演示")).pack(anchor='w', pady=(0, 10))

        vk.Label(self, text=vk.LocalizedText("普通标签 (Normal):")).pack(anchor='w')
        label_normal = vk.Label(self, text=vk.LocalizedText("这是默认颜色的标签"))
        label_normal.pack(anchor='w', pady=5)

        vk.Label(self, text=vk.LocalizedText("警告标签 (Warning):")).pack(anchor='w')
        label_warning = vk.Label(self, text=vk.LocalizedText("这是一条警告信息"))
        label_warning.set_color_type(vk.LabelColorType.Warning)
        label_warning.pack(anchor='w', pady=5)

        vk.Label(self, text=vk.LocalizedText("错误标签 (Error):")).pack(anchor='w')
        label_error = vk.Label(self, text=vk.LocalizedText("这是一条错误信息"))
        label_error.set_color_type(vk.LabelColorType.Error)
        label_error.pack(anchor='w', pady=5)

        vk.Label(self, text=vk.LocalizedText("成功标签 (Success):")).pack(anchor='w')
        label_success = vk.Label(self, text=vk.LocalizedText("这是一条成功信息"))
        label_success.set_color_type(vk.LabelColorType.Success)
        label_success.pack(anchor='w', pady=5)

        vk.Label(self, text=vk.LocalizedText("自适应换行标签:")).pack(anchor='w', pady=(15, 0))
        label_wrap = vk.Label(
            self,
            text=vk.LocalizedText("这是一段很长的文本，当容器宽度不足时自动换行显示。responsive_wrap 功能会根据父容器宽度自动调整文字换行位置。"),
            responsive_wrap=True
        )
        label_wrap.pack(anchor='w', pady=5, fill='x')


def main():
    app = vk.App(title=vk.LocalizedText("VeilTK 组件演示"), width=900, height=600)
    app.center_on_screen()

    icon_path = os.path.join(demo_dir, "testicon.png")
    if os.path.exists(icon_path):
        icon_image = tk.PhotoImage(file=icon_path)
        app.get_root_tk().iconphoto(True, icon_image)
        app._icon_image = icon_image  # 防止垃圾回收

    header_frame = vk.Frame(app)
    header_frame.pack(fill='x', pady=10, padx=10)

    title_label = vk.Label(header_frame, text=vk.LocalizedText("VeilTK 组件演示"))
    title_label.pack(side='left')

    theme_switcher = ThemeSwitcher(header_frame)
    theme_switcher.pack(side='right', padx=20)

    menu_items = [
        {'text': vk.LocalizedText("Label"),          'page': LabelPage},
        {'text': vk.LocalizedText("Button"),        'page': ButtonPage},
        {'text': vk.LocalizedText("Entry"),          'page': EntryPage},
        {'text': vk.LocalizedText("Text"),           'page': TextPage},
        {'text': vk.LocalizedText("Combobox"),       'page': ComboboxPage},
        {'text': vk.LocalizedText("CheckButton"),     'page': CheckButtonPage},
        {'text': vk.LocalizedText("LinkButton"),     'page': LinkButtonPage},
        {'text': vk.LocalizedText("ScrollListbox"),  'page': ScrollListboxPage},
        {'text': vk.LocalizedText("Progress"),      'page': ProgressPage},
        {'text': vk.LocalizedText("MessageBox"),     'page': MessageBoxPage},
    ]

    menu = vk.Menu(
        app,
        menu_items=menu_items,
        position=vk.MenuPosition.Left,
        page_mode=vk.PageMode.Cache,
        menu_width=180
    )
    menu.pack(fill='both', expand=True)

    app.run()


if __name__ == "__main__":
    main()
