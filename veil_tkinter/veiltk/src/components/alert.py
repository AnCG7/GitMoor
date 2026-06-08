import tkinter as tk
from ..core.window import Window
from ..core.application import App
from ..core.utils.utils import Utils
from .label import Label
from .frame import Frame
from .normal_button import NormalButton, ButtonStyleType
from ..core.manager.localization_manager import LocalizedText
from .scrollbar import Scrollbar, Orientation


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
        self._scrollable = False
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
        self._container = Frame(self)
        self._container.pack(fill='both', expand=True, padx=20, pady=20)

        # 将按钮容器独立放在底部，保证永远可见
        self._button_frame = Frame(self._container)
        self._button_frame.pack(side='bottom', fill='x', pady=(15, 0))

        # 中间内容区域包装，支持小内容居中或大内容滚动
        self._center_wrapper = Frame(self._container)
        self._center_wrapper.pack(side='top', fill='both', expand=True)

        self._top_spacer = Frame(self._center_wrapper)
        self._bottom_spacer = Frame(self._center_wrapper)

        title_font = self._styles.get_style().font.title
        self._title_label = Label(self._center_wrapper, text=self._title, font=title_font, anchor="center", justify=tk.CENTER)
        
        self._content_area = Frame(self._center_wrapper)
        
        # 滚动区域设置
        self._canvas = tk.Canvas(self._content_area.get_root_tk(), highlightthickness=0, borderwidth=0)
        self._scrollbar = Scrollbar(self._content_area, orientation=Orientation.Vertical)
        
        bg_color = self._styles.get_style().component.frame.bg.color
        self._canvas.config(bg=bg_color)
        
        self._canvas_frame = tk.Frame(self._canvas, background=bg_color)
        self._canvas_window = self._canvas.create_window((0, 0), window=self._canvas_frame, anchor='nw')

        self._content_label = Label(self._canvas_frame, text=self._content, anchor="center", justify=tk.CENTER, responsive_wrap=True)
        self._content_label.pack(fill='both', expand=True)

        # 绑定滚动事件
        self._canvas.config(yscrollcommand=self._sync_scrollbar)
        self._scrollbar.on_scroll.add_listener(self._on_scrollbar_scroll)

        self._internal_bind_ids.append((self._canvas_frame, "<Configure>", self._canvas_frame.bind("<Configure>", self._on_canvas_frame_configure, add='+')))
        self._internal_bind_ids.append((self._canvas, "<Configure>", self._canvas.bind("<Configure>", self._on_canvas_configure, add='+')))

        self._bind_mouse_wheel_events()

    def _sync_scrollbar(self, first, last):
        self._scrollbar.set_position(float(first), float(last))

    def _on_scrollbar_scroll(self, fraction):
        self._canvas.yview_moveto(fraction)

    def _on_canvas_frame_configure(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _bind_mouse_wheel_events(self):
        widgets = [
            self._canvas, 
            self._canvas_frame, 
            self._content_label.get_root_tk()
        ]
        for widget in widgets:
            self._internal_bind_ids.append((widget, '<Enter>', widget.bind('<Enter>', self._on_enter_scroll_area, add='+')))
            self._internal_bind_ids.append((widget, '<Leave>', widget.bind('<Leave>', self._on_leave_scroll_area, add='+')))
            self._internal_bind_ids.append((widget, '<MouseWheel>', widget.bind('<MouseWheel>', self._on_mouse_wheel, add='+')))

    def _on_enter_scroll_area(self, event):
        self._mouse_inside = True

    def _on_leave_scroll_area(self, event):
        self._mouse_inside = False

    def _on_mouse_wheel(self, event):
        if not getattr(self, '_mouse_inside', False):
            return
        
        # 如果高度没有超过最大值，强制禁止滚动行为
        if not self._scrollable:
            return
            
        yview = self._canvas.yview()
        # 加入极小误差范围判断，避免浮点数或 1px 边距导致的微小滚动
        if len(yview) == 2 and yview[0] <= 0.001 and yview[1] >= 0.999:
            return
            
        delta = -1 if event.delta > 0 else 1
        self._canvas.yview_scroll(delta, "units")
        return "break"

    def _adjust_size(self):
        self._tk_window.update_idletasks()
        
        screen_height = self._tk_window.winfo_screenheight()
        max_height = screen_height // 2
        available_width = self._width - 40
        
        content_label = self._content_label.get_root_tk()
        if hasattr(content_label, 'winfo_reqheight'):
            content_label.config(wraplength=available_width)
            
        self._tk_window.update_idletasks()
        
        title_h = self._title_label.get_root_tk().winfo_reqheight()
        btn_h = self._button_frame.get_root_tk().winfo_reqheight()
        content_req_h = self._canvas_frame.winfo_reqheight()
        
        # 计算所需固定区域及间距的高度: padx, pady=20(上下40) + btn的pady=15 + content的pady=8
        fixed_h = 40 + 15 + 8 + title_h + btn_h
        total_req_height = fixed_h + content_req_h
        
        # 重置布局避免重复计算或冲突
        self._top_spacer.get_root_tk().pack_forget()
        self._bottom_spacer.get_root_tk().pack_forget()
        self._title_label.get_root_tk().pack_forget()
        self._content_area.get_root_tk().pack_forget()
        
        if total_req_height > max_height:
            self._height = max_height
            self._scrollable = True
            
            self._scrollbar.pack(side='right', fill='y')
            self._canvas.pack(side='left', fill='both', expand=True)
            
            # 为滚动条留出空间，重新计算自动换行
            if hasattr(content_label, 'winfo_reqheight'):
                content_label.config(wraplength=available_width - 15)
                self._tk_window.update_idletasks()
                
            self._title_label.pack(side='top', fill='x')
            self._content_area.pack(side='top', fill='both', expand=True, pady=(8, 0))
            
        else:
            self._height = max(total_req_height, 140)
            self._scrollable = False
            
            self._scrollbar.pack_forget()
            self._canvas.pack(side='left', fill='both', expand=True)
            
            self._top_spacer.pack(side='top', fill='both', expand=True)
            self._title_label.pack(side='top', fill='x')
            self._content_area.pack(side='top', fill='x', expand=False, pady=(8, 0))
            self._canvas.config(height=self._canvas_frame.winfo_reqheight())
            self._bottom_spacer.pack(side='top', fill='both', expand=True)
            
        self._tk_window.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        
        # 在高度计算完毕后，统一设置尺寸和位置实现居中，避免两次 geometry 导致闪烁
        self._center_on_app()

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
        
        bg_color = self._styles.get_style().component.frame.bg.color
        if hasattr(self, '_canvas'):
            self._canvas.config(bg=bg_color)
        if hasattr(self, '_canvas_frame'):
            self._canvas_frame.config(bg=bg_color)

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