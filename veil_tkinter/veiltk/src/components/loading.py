import tkinter as tk
from enum import Enum
from ..core.window import Window
from ..core.application import App
from ..core.utils.utils import Utils
from .frame import Frame
from .label import Label
from .loading_views.loading_line import LoadingLineView
from .loading_views.loading_chase import LoadingChaseView
from .loading_views.loading_rect import LoadingRectView
from ..core.manager.localization_manager import LocalizedText


class LoadingStyle(Enum):
    Rect = "rect"
    Chase = "chase"
    Line = "line"


class Loading(Window):
    def __init__(self, master=None, message=None, style_type=LoadingStyle.Rect):
        if message is not None and not isinstance(message, LocalizedText):
            raise TypeError("message 参数必须是 LocalizedText 类型")

        super().__init__(master, LocalizedText(""), width=200, height=150)
        self._message = message
        self._style_type = style_type
        self._loading_view = None
        self._message_label = None
        self._container = None
        self._root_tk = None
        self._auto_close_id = None
        self._internal_bind_ids = []
        self._setup_content()
        self._enable_center_tracking()

    def _build_widget(self):
        super()._build_widget()
        self._tk_window.overrideredirect(True)
        self._tk_window.resizable(False, False)
        border_color = self._styles.get_style().component.window.overlay_border.color
        self._tk_window.config(highlightbackground=border_color, highlightthickness=1, highlightcolor=border_color)

    def _setup_content(self):
        self._container = Frame(self)
        self._container.pack(fill='both', expand=True, padx=20, pady=20)

        top_spacer = Frame(self._container)
        top_spacer.pack(fill='both', expand=True)

        self._view_frame = Frame(self._container, height=40)
        self._view_frame.pack(fill='x')
        self._view_frame.pack_propagate(False)

        self._loading_view = self._create_loading_view()
        self._loading_view.pack(in_=self._view_frame.get_root_tk(), expand=True)

        if self._message:
            self._message_label = Label(self._container, text=self._message, anchor="center", justify=tk.CENTER)
            self._message_label.pack(pady=(10, 0))

        bottom_spacer = Frame(self._container)
        bottom_spacer.pack(fill='both', expand=True)

    def _create_loading_view(self):
        if self._style_type == LoadingStyle.Line:
            return LoadingLineView(self._view_frame)
        elif self._style_type == LoadingStyle.Chase:
            return LoadingChaseView(self._view_frame)
        else:
            return LoadingRectView(self._view_frame)

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
        self._tk_window.geometry(f"+{root_x + offset_x}+{root_y + offset_y}")

    def _enable_center_tracking(self):
        self._root_tk = self._get_app_root_tk()
        self._internal_bind_ids.append((self._root_tk, '<Configure>', self._root_tk.bind('<Configure>', self._on_window_configure, add='+')))
        self._center_on_app()

    def _disable_center_tracking(self):
        for widget, sequence, funcid in self._internal_bind_ids:
            try:
                widget.unbind(sequence, funcid)
            except Exception:
                pass
        self._internal_bind_ids.clear()

    def _on_window_configure(self, event):
        if event.widget is self._root_tk:
            self._center_on_app()

    def _on_theme_changed_internal(self, theme):
        super()._on_theme_changed_internal(theme)
        border_color = self._styles.get_style().component.window.overlay_border.color
        self._tk_window.config(highlightbackground=border_color, highlightcolor=border_color)

    def show(self):
        self._center_on_app()
        self._tk_window.grab_set()
        self._tk_window.wait_window()

    def show_with_duration(self, duration):
        if duration is not None and duration > 0:
            self._auto_close_id = self._tk_window.after(int(duration * 1000), self.close)
        self._center_on_app()
        self._tk_window.grab_set()
        self._tk_window.wait_window()

    def _on_destroy(self):
        if self._auto_close_id:
            self._tk_window.after_cancel(self._auto_close_id)
            self._auto_close_id = None
        self._disable_center_tracking()
        if self._tk_window and self._tk_window.winfo_exists():
            self._tk_window.grab_release()
        super()._on_destroy()

    def set_message(self, message):
        if message is not None and not isinstance(message, LocalizedText):
            raise TypeError("message 参数必须是 LocalizedText 类型")
        self._message = message
        if self._message_label:
            self._message_label.set_text(message)

    @staticmethod
    def show(master=None, message=None, style_type=LoadingStyle.Rect, duration=None):
        loading = Loading(master, message=message, style_type=style_type)
        if duration is not None:
            loading.show_with_duration(duration)
        else:
            loading.show()
        return loading
