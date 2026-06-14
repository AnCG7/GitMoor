import tkinter as tk
from ..core.window import Window
from ..core.application import App
from ..core.utils.utils import Utils
from .label import Label
from .frame import Frame
from .normal_button import NormalButton, ButtonStyleType
from ..core.manager.localization_manager import LocalizedText
from .text import Text, TextMode, TextWrapMode
from .scroll_listbox import ScrollbarMode


class Alert(Window):
    def __init__(self, master=None, title=None, content=None):
        if title is not None and not isinstance(title, LocalizedText):
            raise TypeError("title 参数必须是 LocalizedText 类型")
        if content is not None and not isinstance(content, LocalizedText):
            raise TypeError("content 参数必须是 LocalizedText 类型")

        title = title or LocalizedText("Alert")
        content = content or LocalizedText("")

        super().__init__(master, title, width=360, height=180)
        self._content = content
        self._button_frame = None
        self._root_tk = None
        self._internal_bind_ids = []
        self._setup_content()
        self._enable_center_tracking()

    def _build_widget(self):
        super()._build_widget()
        self._tk_window.overrideredirect(True)
        self._tk_window.resizable(False, False)
        border_color = self._styles.get_style().component.window.overlay_border.color
        self._tk_window.config(highlightbackground=border_color, highlightthickness=1, highlightcolor=border_color)
        self._tk_window.protocol("WM_DELETE_WINDOW", self.close)

    def _setup_content(self):
        # 缩减内边距（padx 20→12, pady 20→16），为文本和滚动条释放横向空间
        self._container = Frame(self)
        self._container.pack(fill='both', expand=True, padx=12, pady=16)

        # 将按钮容器独立放在底部，保证永远可见
        self._button_frame = Frame(self._container)
        self._button_frame.pack(side='bottom', fill='x', pady=(8, 0))

        # 中间内容区域包装，支持小内容居中或大内容滚动
        self._center_wrapper = Frame(self._container)
        self._center_wrapper.pack(side='top', fill='both', expand=True)

        self._top_spacer = Frame(self._center_wrapper)
        self._bottom_spacer = Frame(self._center_wrapper)

        title_font = self._styles.get_style().font.title
        self._title_label = Label(self._center_wrapper, text=self._title, font=title_font, anchor="center", justify=tk.CENTER)

        # 使用 Text 组件（Label模式）替代 raw tk.Text + canvas + scrollbar
        self._content_text = Text(
            self._center_wrapper,
            text=self._content,
            wrap_mode=TextWrapMode.Char,
            scrollbar_mode=ScrollbarMode.Never,
        )
        self._content_text.set_mode(TextMode.Label)

        # 预配置对齐标签
        self._content_text.tag_configure('content_center', justify=tk.CENTER)
        self._content_text.tag_configure('content_left', justify=tk.LEFT)

    def _adjust_size(self):
        # 先隐藏窗口，避免布局计算过程中的中间状态被用户看到（消除闪烁）
        self._tk_window.withdraw()
        self._tk_window.update_idletasks()

        # 基于宽度定制扁平化最大高度（360 * 0.72 ≈ 260px），视觉紧凑精致
        max_height = int(self._width * 0.72)

        # === 0. 计算固定区域高度 ===
        title_h = self._title_label.get_root_tk().winfo_reqheight()
        btn_h = self._button_frame.get_root_tk().winfo_reqheight()
        # fixed_h: container pady=16*2 + btn_pady=8 + content_pady=8
        fixed_h = 32 + 8 + 8 + title_h + btn_h
        available_content_h = max_height - fixed_h

        # === 1. 快速预估：用最小字号判断内容是否明显超长 ===
        # 可用文本宽度 = Alert 宽度 - container padx*2(12*2) - highlightthickness*2(1*2)
        text_area_width = self._width - 24 - 2
        content_str = self._content.get_text() if self._content else ""

        is_definitely_overflow = Utils.is_content_overflow(
            text=content_str,
            available_width=text_area_width,
            available_height=available_content_h,
        )

        # 重置布局
        self._top_spacer.get_root_tk().pack_forget()
        self._bottom_spacer.get_root_tk().pack_forget()
        self._title_label.get_root_tk().pack_forget()

        if is_definitely_overflow:
            # === 快速路径：内容明显超长，直接走滚动模式，跳过真实测量 ===
            self._height = max_height
            self._content_text.set_scrollbar_mode(ScrollbarMode.Always)

            self._content_text.pack_propagate(False)
            self._content_text.configure(height=available_content_h)

            self._title_label.pack(side='top', fill='x')
            self._content_text.pack(side='top', fill='both', expand=True, pady=(8, 0))
        else:
            # === 慢速路径：内容量可控，走真实测量获取精确高度 ===
            # 临时 pack 获取真实渲染高度
            self._content_text.pack(side='top', fill='x', pady=(8, 0))
            self._tk_window.update_idletasks()

            content_req_h = self._content_text.get_rendered_content_height()

            # 测算完毕，解包
            self._content_text.pack_forget()

            total_req_height = fixed_h + content_req_h + 2  # +2 补偿窗口边框

            if total_req_height > max_height:
                self._height = max_height
                self._content_text.set_scrollbar_mode(ScrollbarMode.Always)

                self._content_text.pack_propagate(False)
                self._content_text.configure(height=available_content_h)

                self._title_label.pack(side='top', fill='x')
                self._content_text.pack(side='top', fill='both', expand=True, pady=(8, 0))
            else:
                # 未溢出：在真实内容高度基础上多留一行默认行高余量
                one_line_h = self._content_text.get_default_height_for_lines(1) - self._content_text._pady * 2
                content_height = content_req_h + one_line_h
                self._height = max(fixed_h + content_height + 2, 140)
                self._content_text.set_scrollbar_mode(ScrollbarMode.Never)
                self._content_text.pack_propagate(False)
                self._content_text.configure(height=content_height)

                self._top_spacer.pack(side='top', fill='both', expand=True)
                self._title_label.pack(side='top', fill='x')
                self._content_text.pack(side='top', fill='x', expand=False, pady=(8, 0))
                self._bottom_spacer.pack(side='top', fill='both', expand=True)

        self._tk_window.update_idletasks()
        self._apply_content_alignment()
        self._center_on_app()
        # 布局完成后再显示窗口，避免闪烁
        self._tk_window.deiconify()

    def _apply_content_alignment(self):
        """根据内容行数动态调整对齐方式：单行居中，多行左对齐"""
        try:
            text = self._content_text.get_content_text()
            has_newlines = '\n' in text
            line_count = self._content_text.get_line_count()
            is_multiline = has_newlines or line_count > 1

            if is_multiline:
                self._content_text.tag_remove('content_center', '1.0', 'end')
                self._content_text.tag_add('content_left', '1.0', 'end')
            else:
                self._content_text.tag_remove('content_left', '1.0', 'end')
                self._content_text.tag_add('content_center', '1.0', 'end')
        except Exception:
            pass

    def _get_app_root_tk(self):
        app = App.get_instance()
        return app.get_root_tk() if app else self._master.get_root_tk()

    def _center_on_app(self):
        root_tk = self._get_app_root_tk()
        root_tk.update_idletasks()
        root_width = root_tk.winfo_width()
        root_height = root_tk.winfo_height()
        root_x = root_tk.winfo_x()
        root_y = root_tk.winfo_y()

        offset_x, offset_y = Utils.center_rect(root_width, root_height, self._width, self._height)

        # 将宽、高和坐标位置组合成一个 geometry 字符串，一次性生效
        self._tk_window.geometry(f"{self._width}x{self._height}+{root_x + offset_x}+{root_y + offset_y}")

    def _enable_center_tracking(self):
        self._root_tk = self._get_app_root_tk()
        self._internal_bind_ids.append((self._root_tk, '<Configure>', self._root_tk.bind('<Configure>', self._on_window_configure, add='+')))
        self._center_on_app()

    def _on_window_configure(self, event):
        if event.widget is self._root_tk:
            self._center_on_app()

    def _unbind_events(self):
        for widget, sequence, funcid in self._internal_bind_ids:
            try:
                widget.unbind(sequence, funcid)
            except Exception:
                pass
        self._internal_bind_ids.clear()

    def _on_theme_changed_internal(self, theme):
        super()._on_theme_changed_internal(theme)
        border_color = self._styles.get_style().component.window.overlay_border.color
        self._tk_window.config(highlightbackground=border_color, highlightcolor=border_color)

    def add_button(self, button):
        button.on_click.add_listener(self.close)
        button.pack(side='right', padx=5)

    def get_button_frame(self):
        return self._button_frame

    def show(self):
        self._adjust_size()
        self._tk_window.grab_set()
        self._tk_window.wait_window()

    def _on_destroy(self):
        self._unbind_events()
        if self._tk_window and self._tk_window.winfo_exists():
            self._tk_window.grab_release()
        super()._on_destroy()

    @staticmethod
    def show_confirm(master=None, title=None, content=None, ok_btn_text=None, cancel_btn_text=None,
                     ok_callback=None, cancel_callback=None):
        if title is not None and not isinstance(title, LocalizedText):
            raise TypeError("title 参数必须是 LocalizedText 类型")
        if content is not None and not isinstance(content, LocalizedText):
            raise TypeError("content 参数必须是 LocalizedText 类型")
        if ok_btn_text is not None and not isinstance(ok_btn_text, LocalizedText):
            raise TypeError("ok_btn_text 参数必须是 LocalizedText 类型")
        if cancel_btn_text is not None and not isinstance(cancel_btn_text, LocalizedText):
            raise TypeError("cancel_btn_text 参数必须是 LocalizedText 类型")

        ok_btn_text = ok_btn_text or LocalizedText("OK")
        cancel_btn_text = cancel_btn_text or LocalizedText("Cancel")

        alert = Alert(master, title, content)

        cancel_btn = NormalButton(alert.get_button_frame(), text=cancel_btn_text, style_type=ButtonStyleType.Secondary)
        if cancel_callback:
            cancel_btn.on_click.add_listener(cancel_callback)

        ok_btn = NormalButton(alert.get_button_frame(), text=ok_btn_text, style_type=ButtonStyleType.Primary)
        if ok_callback:
            ok_btn.on_click.add_listener(ok_callback)

        alert.add_button(cancel_btn)
        alert.add_button(ok_btn)

        alert.show()
        return alert

    @staticmethod
    def show_normal(master=None, title=None, message=None, ok_btn_text=None, ok_callback=None):
        if title is not None and not isinstance(title, LocalizedText):
            raise TypeError("title 参数必须是 LocalizedText 类型")
        if message is not None and not isinstance(message, LocalizedText):
            raise TypeError("message 参数必须是 LocalizedText 类型")
        if ok_btn_text is not None and not isinstance(ok_btn_text, LocalizedText):
            raise TypeError("ok_btn_text 参数必须是 LocalizedText 类型")

        ok_btn_text = ok_btn_text or LocalizedText("OK")

        alert = Alert(master, title, message)

        ok_btn = NormalButton(alert.get_button_frame(), text=ok_btn_text, style_type=ButtonStyleType.Primary)
        if ok_callback:
            ok_btn.on_click.add_listener(ok_callback)

        alert.add_button(ok_btn)

        alert.show()
        return alert