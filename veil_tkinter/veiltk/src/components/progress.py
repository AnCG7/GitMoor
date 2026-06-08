import tkinter as tk
from enum import Enum
from ..core.view import View
from ..core.manager.ui_style_manager import UIStyleManager
from ..core.manager.event_manager import Event


class Orientation(Enum):
    Vertical = "vertical"
    Horizontal = "horizontal"


class Progress(View):
    def __init__(self, master=None, orientation=Orientation.Horizontal, **kwargs):
        if not isinstance(orientation, Orientation):
            raise TypeError("orientation 参数必须是 Orientation 枚举类型")
        self._orientation = orientation
        self._kwargs = kwargs
        self._disabled = False
        self._tk_frame = None
        self._tk_canvas = None
        self._progress_rect = None
        self._value = 0.0
        self._styles = None
        self._internal_bind_ids = []

        self.on_configure = Event()
        
        super().__init__(master, **kwargs)

    def _build_widget(self, master=None, **kwargs):
        master_tk = self._get_master_tk()
            
        self.styles = UIStyleManager.get_instance()
        self._config_styles()

        default_kwargs = {
            "bg": self._styles.trough_color,
            "height": 20 if self._orientation == Orientation.Horizontal else 20,
            "relief": tk.FLAT,
            "borderwidth": 0
        }
        default_kwargs.update(self._kwargs)

        self._tk_frame = tk.Frame(master_tk, **default_kwargs)

        self._tk_canvas = tk.Canvas(
            self._tk_frame,
            bg=self._styles.trough_color,
            highlightthickness=0,
            width=default_kwargs.get("width", 200),
            height=default_kwargs.get("height", 20)
        )
        self._tk_canvas.pack(fill=tk.BOTH, expand=True)

        self._progress_rect = self._tk_canvas.create_rectangle(
            0, 0, 0, default_kwargs.get("height", 20),
            fill=self._styles.bar_color,
            outline=""
        )

        self._internal_bind_ids.append((self._tk_canvas, '<Configure>', self._tk_canvas.bind('<Configure>', self._on_configure_internal, add='+')))

        self.styles.on_theme_changed.add_listener(self._on_theme_changed_internal)

        return self._tk_frame

    def _on_destroy(self):
        self._unbind_internal_events()
        self._unregister_listeners()
        super()._on_destroy()

    def _unbind_internal_events(self):
        for widget, sequence, funcid in self._internal_bind_ids:
            try:
                widget.unbind(sequence, funcid)
            except:
                pass
        self._internal_bind_ids.clear()

    def _on_theme_changed_internal(self, theme):
        self._config_styles()
        self._tk_frame.config(bg=self._styles.trough_color)
        self._tk_canvas.config(bg=self._styles.trough_color)
        self._tk_canvas.itemconfig(self._progress_rect, fill=self._styles.bar_color)

    def _unregister_listeners(self):
        self.styles.on_theme_changed.remove_listener(self._on_theme_changed_internal)

    def _config_styles(self):
        current_style = self.styles.get_style().component.progress
        if self._disabled:
            self._styles = type('ProgressStyles', (), {
                'trough_color': current_style.normal.trough.color if hasattr(current_style.normal, 'trough') else current_style.normal.bg.color,
                'bar_color': current_style.disable.bar.color if hasattr(current_style.disable, 'bar') else current_style.disable.fg.color
            })
        else:
            self._styles = type('ProgressStyles', (), {
                'trough_color': current_style.normal.trough.color if hasattr(current_style.normal, 'trough') else current_style.normal.bg.color,
                'bar_color': current_style.normal.bar.color if hasattr(current_style.normal, 'bar') else current_style.normal.fg.color
            })

    def _on_configure_internal(self, event):
        self.on_configure.broadcast(event)
        self._update_progress()

    def _update_progress(self):
        w = self._tk_canvas.winfo_width()
        h = self._tk_canvas.winfo_height()
        progress_width = w * self._value
        
        if self._orientation == Orientation.Horizontal:
            self._tk_canvas.coords(self._progress_rect, 0, 0, progress_width, h)
        else:
            progress_height = h * self._value
            self._tk_canvas.coords(self._progress_rect, 0, h - progress_height, w, h)

    def set_value(self, value):
        self._value = max(0.0, min(1.0, value))
        self._update_progress()

    def get_value(self):
        return self._value

    def set_disabled(self, disabled):
        self._disabled = disabled
        self._config_styles()
        self._tk_canvas.config(bg=self._styles.trough_color)
        self._tk_canvas.itemconfig(self._progress_rect, fill=self._styles.bar_color)
        self._update_progress()

    def is_disabled(self):
        return self._disabled

    def refresh(self):
        self._config_styles()
        self._tk_canvas.config(bg=self._styles.trough_color)
        self._tk_canvas.itemconfig(self._progress_rect, fill=self._styles.bar_color)
        self._update_progress()
