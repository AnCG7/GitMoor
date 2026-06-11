import os
import tkinter as tk
from .manager.ui_style_manager import UIStyleManager
from .manager.event_manager import Event
from .manager.localization_manager import LocalizedText


class App:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if App._instance is None:
            App._instance = super().__new__(cls)
        return App._instance

    @classmethod
    def get_instance(cls):
        if App._instance is None:
            print("Error: App instance has not been created yet!")
            return None
        return App._instance

    def __init__(self, title=None, width=800, height=600, icons=None):
        if hasattr(self, '_initialized'):
            return
        if title is not None and not isinstance(title, LocalizedText):
            raise TypeError("title 参数必须是 LocalizedText 类型")
        self._initialized = True
        self._title = title or LocalizedText("Application")
        self._width = width
        self._height = height
        self._icons = list(icons) if icons else []
        self._icon_images = []
        self._min_width = None
        self._min_height = None
        self._max_width = None
        self._max_height = None
        self.on_close = Event()
        self._styles = UIStyleManager.get_instance()
        self._build_widget()

    def _build_widget(self):
        self._tk = tk.Tk()
        self._tk.withdraw()  # 先隐藏窗口，避免显示时闪烁
        self._tk.title(self._title.get_text() if hasattr(self._title, 'get_text') else self._title)
        self._tk.geometry(f"{self._width}x{self._height}")
        self._tk.protocol("WM_DELETE_WINDOW", self._on_close_internal)
        if self._icons:
            self._apply_icon()
        self._apply_bg_color()
        self._register_listeners()

    def _apply_icon(self):
        if not self._icons:
            return
        ext = os.path.splitext(self._icons[0])[1].lower()
        if ext == '.ico':
            self._tk.iconbitmap(self._icons[0])
        else:
            try:
                self._icon_images = [tk.PhotoImage(file=p) for p in self._icons]
                self._tk.iconphoto(True, *self._icon_images)
            except tk.TclError:
                pass

    def _apply_bg_color(self):
        bg_color = self._styles.get_style().component.window.bg.color
        self._tk.configure(bg=bg_color)

    def _register_listeners(self):
        self._styles.on_theme_changed.add_listener(self._on_theme_changed_internal)

    def _unregister_listeners(self):
        self._styles.on_theme_changed.remove_listener(self._on_theme_changed_internal)

    def _on_theme_changed_internal(self, theme):
        self._apply_bg_color()

    def center_on_screen(self):
        screen_width = self._tk.winfo_screenwidth()
        screen_height = self._tk.winfo_screenheight()
        x = (screen_width - self._width) // 2
        y = (screen_height - self._height) // 2
        self._tk.geometry(f"{self._width}x{self._height}+{x}+{y}")

    def get_root_tk(self):
        return self._tk

    def set_size(self, width, height):
        self._width = width
        self._height = height
        self._tk.geometry(f"{width}x{height}")

    def set_min_size(self, width, height):
        if self._max_width is not None and self._max_height is not None:
            if width > self._max_width or height > self._max_height:
                print(f"Warning: min_size({width}, {height}) exceeds max_size({self._max_width}, {self._max_height}), ignored")
                return
        self._min_width = width
        self._min_height = height
        self._tk.minsize(width, height)

    def set_max_size(self, width, height):
        if self._min_width is not None and self._min_height is not None:
            if width < self._min_width or height < self._min_height:
                print(f"Warning: max_size({width}, {height}) is less than min_size({self._min_width}, {self._min_height}), ignored")
                return
        self._max_width = width
        self._max_height = height
        self._tk.maxsize(width, height)

    def _on_close_internal(self):
        self.on_close.broadcast()
        self.shutdown()

    def after(self, delay_ms, callback=None):
        if self._tk:
            return self._tk.after(delay_ms, callback)

    def after_cancel(self, after_id):
        if self._tk and after_id:
            self._tk.after_cancel(after_id)

    def clipboard_set(self, text):
        self._tk.clipboard_clear()
        self._tk.clipboard_append(text)

    def clipboard_get(self):
        return self._tk.clipboard_get()

    def run(self):
        self._tk.deiconify()  # 所有配置完成后再显示窗口
        self._tk.mainloop()

    def shutdown(self):
        self._unregister_listeners()
        if self._tk:
            self._tk.destroy()
            self._tk = None
        App._instance = None
