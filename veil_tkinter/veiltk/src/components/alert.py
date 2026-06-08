import tkinter as tk
import tkinter.font as tkfont
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
        self._button_frame.pack(side='bottom', fill='x', pady=(12, 0))

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
        self._tk_window.update_idletasks()
        
        # 基于宽度定制扁平化最大高度（360 * 0.72 ≈ 260px），视觉紧凑精致
        max_height = int(self._width * 0.72)
        # 配合 container 新 padx=12 计算可用宽度 (360 - 12*2 = 336)
        available_width = self._width - 24
        
        font_obj = tkfont.Font(font=self._styles.get_style().font.normal)
        char_width = max(1, font_obj.measure('0'))
        line_height_px = font_obj.metrics('linespace')
        
        # === 1. 临时 pack 获取准确行数 ===
        # 必须 pack 后才能让 Tk 几何管理器分配像素宽度，否则 displaylines 返回错误值
        self._content_text.set_width(max(1, int(available_width / char_width)))
        self._content_text.pack(side='top', fill='x', pady=(8, 0))
        self._content_text.set_line_height(1)
        self._tk_window.update_idletasks()
        
        line_count = self._content_text.get_line_count()
        
        # 设置实际行数高度，测量 widget 真实 reqheight
        self._content_text.set_line_height(line_count)
        self._tk_window.update_idletasks()
        content_req_h = self._content_text.get_root_tk().winfo_reqheight()
        
        # 测算完毕，解包
        self._content_text.pack_forget()
        
        # === 2. 计算总高度，判断是否溢出 ===
        title_h = self._title_label.get_root_tk().winfo_reqheight()
        btn_h = self._button_frame.get_root_tk().winfo_reqheight()
        # fixed_h: container pady=16*2 + btn_pady=12 + content_pady=8
        fixed_h = 32 + 12 + 8 + title_h + btn_h
        total_req_height = fixed_h + content_req_h + 2  # +2 补偿窗口边框
        
        # 重置布局
        self._top_spacer.get_root_tk().pack_forget()
        self._bottom_spacer.get_root_tk().pack_forget()
        self._title_label.get_root_tk().pack_forget()
        
        if total_req_height > max_height:
            self._height = max_height
            # 溢出：Always 滚动条 + 窄宽度（预留滚动条空间）
            self._content_text.set_scrollbar_mode(ScrollbarMode.Always)
            
            self._content_text.set_width(max(1, int((available_width - 15) / char_width)))
            available_content_h = max_height - fixed_h
            visible_lines = max(1, int(available_content_h / line_height_px))
            self._content_text.set_line_height(visible_lines)
            # pack_propagate(False) 防止内部 tk_text 随 expand 撑大
            root_frame = self._content_text.get_root_tk()
            root_frame.pack_propagate(False)
            root_frame.configure(height=available_content_h)
            
            self._title_label.pack(side='top', fill='x')
            self._content_text.pack(side='top', fill='both', expand=True, pady=(8, 0))
        else:
            # 方案B：height = line_count + 1，让末尾隐藏 \n 也可见，使 yview() 返回 (0,1)
            # Text 组件自身的 _on_mouse_wheel 检测到内容未溢出后会自然拦截滚轮
            self._content_text.set_line_height(line_count + 1)
            self._height = max(total_req_height + line_height_px, 140)
            self._content_text.set_scrollbar_mode(ScrollbarMode.Never)
            
            self._top_spacer.pack(side='top', fill='both', expand=True)
            self._title_label.pack(side='top', fill='x')
            self._content_text.pack(side='top', fill='x', expand=False, pady=(8, 0))
            self._bottom_spacer.pack(side='top', fill='both', expand=True)
        
        self._tk_window.update_idletasks()
        self._apply_content_alignment()
        self._center_on_app()

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