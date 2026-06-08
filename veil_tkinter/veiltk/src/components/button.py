import tkinter as tk
from ..core.view import View
from ..core.manager.localization_manager import LocalizationManager, LocalizedText
from ..core.manager.ui_style_manager import UIStyleManager, StyleObject
from ..core.manager.event_manager import Event


class Button(View):
    def __init__(self, master=None, text=None, **kwargs):
        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")
        self._text = text
        self._kwargs = kwargs
        self._tk_label = None
        self._styles = None
        self._button_style = None
        self._disabled = False
        self._hovered = False
        self._pressed = False
        self._focused = False
        self._internal_bind_ids = []

        self.styles = UIStyleManager.get_instance()
        self.localization = LocalizationManager.get_instance()

        self.on_click = Event()
        self.on_enter = Event()
        self.on_leave = Event()
        self.on_configure = Event()
        self.on_scroll = Event()
        self.on_press = Event()
        
        super().__init__(master, **kwargs)

    def _build_widget(self, master=None, **kwargs):
        master_tk = self._get_master_tk()

        display_text = self._text.get_text() if hasattr(self._text, 'get_text') else self._text if self._text else ""

        width = self._kwargs.pop('width', None)
        font = self._kwargs.pop('font', None)

        self._button_style = self._config_styles()

        default_kwargs = {
            "text": display_text,
            "bg": self._button_style["bg"],
            "fg": self._button_style["fg"],
            "font": font if font else self.styles.get_style().font.normal,
            "relief": tk.FLAT,
            "borderwidth": 0,
            "highlightthickness": 0,
            "takefocus": not self._disabled,
            "cursor": "hand2"
        }
        default_kwargs.update(self._kwargs)

        self._tk_label = tk.Label(master_tk, **default_kwargs)

        if width is not None:
            self._tk_label.config(width=width)

        self._internal_bind_ids.append((self._tk_label, '<ButtonPress-1>', self._tk_label.bind('<ButtonPress-1>', self._on_button_press, add='+')))
        self._internal_bind_ids.append((self._tk_label, '<ButtonRelease-1>', self._tk_label.bind('<ButtonRelease-1>', self._on_button_release, add='+')))
        self._internal_bind_ids.append((self._tk_label, '<Enter>', self._tk_label.bind('<Enter>', self._on_enter_internal, add='+')))
        self._internal_bind_ids.append((self._tk_label, '<Leave>', self._tk_label.bind('<Leave>', self._on_leave_internal, add='+')))
        self._internal_bind_ids.append((self._tk_label, '<Configure>', self._tk_label.bind('<Configure>', self._on_configure_internal, add='+')))
        self._internal_bind_ids.append((self._tk_label, '<FocusIn>', self._tk_label.bind('<FocusIn>', self._on_focus_in, add='+')))
        self._internal_bind_ids.append((self._tk_label, '<FocusOut>', self._tk_label.bind('<FocusOut>', self._on_focus_out, add='+')))
        self._internal_bind_ids.append((self._tk_label, '<MouseWheel>', self._tk_label.bind('<MouseWheel>', self._on_mouse_wheel, add='+')))
        self._internal_bind_ids.append((self._tk_label, '<KeyPress-space>', self._tk_label.bind('<KeyPress-space>', self._on_key_press, add='+')))
        self._internal_bind_ids.append((self._tk_label, '<KeyRelease-space>', self._tk_label.bind('<KeyRelease-space>', self._on_key_release, add='+')))
        self._internal_bind_ids.append((self._tk_label, '<KeyPress-Return>', self._tk_label.bind('<KeyPress-Return>', self._on_key_press, add='+')))
        self._internal_bind_ids.append((self._tk_label, '<KeyRelease-Return>', self._tk_label.bind('<KeyRelease-Return>', self._on_key_release, add='+')))

        self._register_listeners()
        self._apply_style()
        
        return self._tk_label

    def _on_destroy(self):
        self._unregister_listeners()
        self._unbind_internal_events()
        super()._on_destroy()

    def _unbind_internal_events(self):
        for widget, sequence, funcid in self._internal_bind_ids:
            try:
                widget.unbind(sequence, funcid)
            except Exception:
                pass
        self._internal_bind_ids.clear()

    def _config_styles(self):
        raise NotImplementedError("子类必须实现 _config_styles 方法")

    def _register_listeners(self):
        self.styles.on_theme_changed.add_listener(self._on_theme_changed_internal)
        self.localization.on_language_changed.add_listener(self._on_language_changed_internal)

    def _unregister_listeners(self):
        self.styles.on_theme_changed.remove_listener(self._on_theme_changed_internal)
        self.localization.on_language_changed.remove_listener(self._on_language_changed_internal)

    def _on_theme_changed_internal(self, theme):
        self.refresh_theme()

    def _on_language_changed_internal(self, language):
        self.refresh_text()

    def _on_button_press(self, event):
        if not self._disabled:
            self._pressed = True
            self._apply_style()
            self.on_press.broadcast(event)

    def _on_button_release(self, event):
        if not self._disabled:
            self._pressed = False
            self._apply_style()
            self.on_click.broadcast()

    def _on_enter_internal(self, event):
        if not self._disabled:
            self._hovered = True
            self._apply_style()
            self.on_enter.broadcast()

    def _on_leave_internal(self, event):
        if not self._disabled:
            self._hovered = False
            self._pressed = False
            self._apply_style()
            self.on_leave.broadcast()

    def _on_mouse_wheel(self, event):
        delta = -1 if event.delta > 0 else 1
        self.on_scroll.broadcast(delta)
        return 'break'

    def _on_key_press(self, event):
        if not self._disabled:
            self._pressed = True
            self._apply_style()
        return 'break'

    def _on_key_release(self, event):
        if not self._disabled:
            self._pressed = False
            self._apply_style()
            self.on_click.broadcast()
        return 'break'

    def _on_configure_internal(self, event):
        self.on_configure.broadcast(event)

    def _on_focus_in(self, event):
        if not self._disabled:
            self._focused = True
            self._apply_style()

    def _on_focus_out(self, event):
        self._focused = False
        self._apply_style()

    def _apply_style(self):
        if self._disabled:
            bg = self._button_style.get("disable_bg", self._button_style["bg"])
            fg = self._button_style.get("disable_fg", self._button_style["fg"])
            cursor = "no"
        elif self._pressed:
            bg = self._button_style.get("activebackground", self._button_style["bg"])
            fg = self._button_style.get("activeforeground", self._button_style["fg"])
            cursor = "hand2"
        elif self._focused:
            bg = self._button_style.get("focus_bg", self._button_style["bg"])
            fg = self._button_style.get("focus_fg", self._button_style["fg"])
            cursor = "hand2"
        elif self._hovered:
            bg = self._button_style.get("hover_bg", self._button_style["bg"])
            fg = self._button_style.get("hover_fg", self._button_style["fg"])
            cursor = "hand2"
        else:
            bg = self._button_style["bg"]
            fg = self._button_style["fg"]
            cursor = "hand2"

        self._tk_label.config(bg=bg, fg=fg, cursor=cursor)

    def refresh_theme(self):
        self._button_style = self._config_styles()
        self._apply_style()

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
        self.refresh_text()

    def set_width(self, width):
        self._tk_label.config(width=width)

    def set_font(self, font):
        self._tk_label.config(font=font)

    def set_disable(self, disable):
        self._disabled = disable
        self._tk_label.config(takefocus=not disable)
        self._apply_style()

    def is_disable(self):
        return self._disabled