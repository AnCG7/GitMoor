import os
import tkinter as tk
from abc import ABC
from .application import App
from .view import View
from .manager.ui_style_manager import UIStyleManager
from .manager.localization_manager import LocalizedText


class Window(ABC):
    def __init__(self, master=None, title=None, width=800, height=600, icons=None):
        if title is not None and not isinstance(title, LocalizedText):
            raise TypeError("title 参数必须是 LocalizedText 类型")
        self._master = self._get_or_validate_master(master)
        self._title = title or LocalizedText("Window")
        self._width = width
        self._height = height
        self._icons = list(icons) if icons else []
        self._icon_images = []
        self._tk_window = None
        self._min_width = None
        self._min_height = None
        self._max_width = None
        self._max_height = None
        self._styles = UIStyleManager.get_instance()
        self._build_widget()

    @staticmethod
    def _get_or_validate_master(master):
        if master is None:
            return App.get_instance()
        if not isinstance(master, (App, Window, View)):
            raise TypeError("master 必须是 App, Window 或 View 类型")
        return master

    def _build_widget(self):
        master_tk = self._master.get_root_tk()
        self._tk_window = tk.Toplevel(master_tk)
        self._tk_window.title(self._title.get_text() if hasattr(self._title, 'get_text') else self._title)
        self._tk_window.geometry(f"{self._width}x{self._height}")
        if self._icons:
            self._apply_icon()
        self._apply_bg_color()
        self._register_listeners()
        self._bind_map_events()

    def _apply_icon(self):
        if not self._icons:
            return
        ext = os.path.splitext(self._icons[0])[1].lower()
        if ext == '.ico':
            self._tk_window.iconbitmap(self._icons[0])
        else:
            try:
                self._icon_images = [tk.PhotoImage(file=p) for p in self._icons]
                self._tk_window.iconphoto(True, *self._icon_images)
            except tk.TclError:
                pass

    def _apply_bg_color(self):
        bg_color = self._styles.get_style().component.window.bg.color
        self._tk_window.configure(bg=bg_color)

    def _register_listeners(self):
        self._styles.on_theme_changed.add_listener(self._on_theme_changed_internal)

    def _unregister_listeners(self):
        self._styles.on_theme_changed.remove_listener(self._on_theme_changed_internal)

    def _bind_map_events(self):
        if self._tk_window:
            self._map_bind_id = self._tk_window.bind('<Map>', self._on_map_event, add='+')
            self._unmap_bind_id = self._tk_window.bind('<Unmap>', self._on_unmap_event, add='+')

    def _unbind_map_events(self):
        if self._tk_window:
            try:
                if hasattr(self, '_map_bind_id') and self._map_bind_id:
                    self._tk_window.unbind('<Map>', self._map_bind_id)
                    self._map_bind_id = None
                if hasattr(self, '_unmap_bind_id') and self._unmap_bind_id:
                    self._tk_window.unbind('<Unmap>', self._unmap_bind_id)
                    self._unmap_bind_id = None
            except Exception:
                pass

    def _on_map_event(self, event):
        if event.widget is self._tk_window:
            self._on_appeared()

    def _on_unmap_event(self, event):
        if event.widget is self._tk_window:
            self._on_disappeared()

    def _on_appeared(self):
        pass

    def _on_disappeared(self):
        pass

    def _on_destroy(self):
        self._on_disappeared()
        self._unbind_map_events()
        self._unregister_listeners()
        if self._tk_window:
            self._tk_window.destroy()
            self._tk_window = None

    def _on_theme_changed_internal(self, theme):
        self._apply_bg_color()

    def get_root_tk(self):
        return self._tk_window

    def set_title(self, title):
        if title is not None and not isinstance(title, LocalizedText):
            raise TypeError("title 参数必须是 LocalizedText 类型")
        self._title = title
        display_title = title.get_text() if hasattr(title, 'get_text') else title
        self._tk_window.title(display_title)

    def set_size(self, width, height):
        self._width = width
        self._height = height
        self._tk_window.geometry(f"{width}x{height}")

    def set_min_size(self, width, height):
        if self._max_width is not None and self._max_height is not None:
            if width > self._max_width or height > self._max_height:
                print(f"Warning: min_size({width}, {height}) exceeds max_size({self._max_width}, {self._max_height}), ignored")
                return
        self._min_width = width
        self._min_height = height
        self._tk_window.minsize(width, height)

    def set_max_size(self, width, height):
        if self._min_width is not None and self._min_height is not None:
            if width < self._min_width or height < self._min_height:
                print(f"Warning: max_size({width}, {height}) is less than min_size({self._min_width}, {self._min_height}), ignored")
                return
        self._max_width = width
        self._max_height = height
        self._tk_window.maxsize(width, height)

    def after(self, delay_ms, callback=None):
        if self._tk_window:
            return self._tk_window.after(delay_ms, callback)

    def after_cancel(self, after_id):
        if self._tk_window and after_id:
            self._tk_window.after_cancel(after_id)

    def show(self):
        self._tk_window.wait_window()

    def close(self):
        self._on_destroy()
