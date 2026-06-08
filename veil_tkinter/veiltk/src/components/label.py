import tkinter as tk
from enum import Enum
from ..core.view import View
from ..core.manager.localization_manager import LocalizationManager, LocalizedText
from ..core.manager.ui_style_manager import UIStyleManager
from ..core.manager.event_manager import Event


class LabelColorType(Enum):
    Normal = "normal"
    Warning = "warning"
    Error = "error"
    Success = "success"

class Label(View):
    def __init__(self, master=None, text=None, responsive_wrap=False, **kwargs):
        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")
        self._text = text
        self._responsive_wrap = responsive_wrap
        self._tk_label = None
        self._styles = None
        self._external_styles = set()
        self._kwargs = kwargs
        self._color_type = LabelColorType.Normal
        self._internal_bind_ids = []

        self.styles = UIStyleManager.get_instance()
        self.localization = LocalizationManager.get_instance()

        self.on_click = Event()

        super().__init__(master, **kwargs)

    def _build_widget(self, master=None, **kwargs):
        master_tk = self._get_master_tk()
        self._config_styles()

        if self._text:
            display_text = self._text.get_text() if hasattr(self._text, 'get_text') else self._text
        else:
            display_text = ""

        default_kwargs = {
            "text": display_text,
            "bg": self._styles.normal.bg,
            "fg": self._styles.normal.fg,
            "font": self._styles.normal.font,
            "relief": tk.FLAT,
            "borderwidth": 0,
            "highlightthickness": 0,
            "justify": tk.LEFT,
            "anchor": "w"
        }
        default_kwargs.update(self._kwargs)

        for key in self._kwargs:
            self._external_styles.add(key)

        self._tk_label = tk.Label(master_tk, **default_kwargs)
        self._internal_bind_ids.append((self._tk_label, '<Button-1>', self._tk_label.bind('<Button-1>', self._on_click_internal, add='+')))

        if self._responsive_wrap:
            self._internal_bind_ids.append((self._tk_label, '<Configure>', self._tk_label.bind('<Configure>', self._on_self_resize, add='+')))

        self._register_listeners()
        
        return self._tk_label

    def _on_destroy(self):
        self._unregister_listeners()
        self._unbind_internal_events()
        super()._on_destroy()

    def _unbind_internal_events(self):
        for widget, sequence, funcid in self._internal_bind_ids:
            try:
                widget.unbind(sequence, funcid)
            except:
                pass
        self._internal_bind_ids.clear()

    def _config_styles(self):
        current_style = self.styles.get_style()

        class NormalStyle:
            def __init__(self):
                self.bg = current_style.component.frame.bg.color
                self.fg = current_style.component.label.fg.color
                self.font = current_style.font.normal

        class WarningStyle:
            def __init__(self):
                self.bg = current_style.component.frame.bg.color
                self.fg = current_style.component.label.warning.color if hasattr(current_style.component.label, 'warning') else current_style.component.label.fg.color
                self.font = current_style.font.normal

        class ErrorStyle:
            def __init__(self):
                self.bg = current_style.component.frame.bg.color
                self.fg = current_style.component.label.error.color if hasattr(current_style.component.label, 'error') else '#FF0000'
                self.font = current_style.font.normal

        class SuccessStyle:
            def __init__(self):
                self.bg = current_style.component.frame.bg.color
                self.fg = current_style.component.label.success.color if hasattr(current_style.component.label, 'success') else current_style.component.label.fg.color
                self.font = current_style.font.normal

        class Styles:
            def __init__(self):
                self.normal = NormalStyle()
                self.warning = WarningStyle()
                self.error = ErrorStyle()
                self.success = SuccessStyle()

        self._styles = Styles()

    def _register_listeners(self):
        self.styles.on_theme_changed.add_listener(self._on_theme_changed)
        self.localization.on_language_changed.add_listener(self._on_language_changed)

    def _unregister_listeners(self):
        self.styles.on_theme_changed.remove_listener(self._on_theme_changed)
        self.localization.on_language_changed.remove_listener(self._on_language_changed)

    def _on_theme_changed(self, theme):
        self._config_styles()
        self.refresh_theme()

    def _on_language_changed(self, language):
        self.refresh_text()

    def _on_click_internal(self, event):
        self.on_click.broadcast(event)

    def _on_self_resize(self, event):
        available_width = self._tk_label.winfo_width()
        if available_width > 0:
            self._tk_label.config(wraplength=available_width)

    def refresh_theme(self):
        self._config_styles()
        style_map = {
            LabelColorType.Normal: self._styles.normal,
            LabelColorType.Warning: self._styles.warning,
            LabelColorType.Error: self._styles.error,
            LabelColorType.Success: self._styles.success,
        }
        current_style = style_map.get(self._color_type, self._styles.normal)
        self._tk_label.config(
            bg=current_style.bg,
            fg=current_style.fg,
            font=current_style.font
        )

    def refresh_text(self):
        if self._text:
            display_text = self._text.get_text() if hasattr(self._text, 'get_text') else self._text
            self._tk_label.config(text=display_text)

    def refresh(self):
        self.refresh_theme()
        self.refresh_text()

    def set_text(self, text):
        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")
        self._text = text
        if text:
            display_text = text.get_text() if hasattr(text, 'get_text') else text
            self._tk_label.config(text=display_text)

    def set_color_type(self, color_type):
        if not isinstance(color_type, LabelColorType):
            raise TypeError("color_type 参数必须是 LabelColorType 枚举类型")
        self._color_type = color_type
        self.refresh_theme()

    def set_foreground(self, color):
        self._tk_label.config(fg=color)

    def set_background(self, color):
        self._tk_label.config(bg=color)