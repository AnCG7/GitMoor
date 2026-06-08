import tkinter as tk
import webbrowser
from ..core.view import View
from ..core.manager.localization_manager import LocalizationManager, LocalizedText
from ..core.manager.ui_style_manager import UIStyleManager
from ..core.manager.event_manager import Event

class LinkButton(View):
    def __init__(self, master=None, text=None, url=None, **kwargs):
        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")
        self._text = text
        self._url = url
        self._kwargs = kwargs
        self._tk_label = None
        self._disabled = False
        self._hovered = False
        self._styles = None
        self._button_style = None
        self._internal_bind_ids = []

        self.on_click = Event()
        self.on_enter = Event()
        self.on_leave = Event()
        
        super().__init__(master, **kwargs)

    def _build_widget(self, master=None, **kwargs):
        master_tk = self._get_master_tk()
            
        self.styles = UIStyleManager.get_instance()
        self.localization = LocalizationManager.get_instance()
        self._button_style = self._config_styles()

        display_text = self._text.get_text() if hasattr(self._text, 'get_text') else self._text if self._text else ""

        default_kwargs = {
            "text": display_text,
            "bg": self._button_style["bg"],
            "fg": self._button_style["fg"],
            "font": self.styles.get_style().font.link,
            "relief": tk.FLAT,
            "borderwidth": 0,
            "highlightthickness": 0,
            "cursor": "hand2" if not self._disabled else "no",
            "takefocus": not self._disabled
        }
        default_kwargs.update(self._kwargs)

        self._tk_label = tk.Label(master_tk, **default_kwargs)
        self._internal_bind_ids.append((self._tk_label, '<ButtonPress-1>', self._tk_label.bind('<ButtonPress-1>', self._on_button_press, add='+')))
        self._internal_bind_ids.append((self._tk_label, '<ButtonRelease-1>', self._tk_label.bind('<ButtonRelease-1>', self._on_button_release, add='+')))
        self._internal_bind_ids.append((self._tk_label, '<Enter>', self._tk_label.bind('<Enter>', self._on_enter_internal, add='+')))
        self._internal_bind_ids.append((self._tk_label, '<Leave>', self._tk_label.bind('<Leave>', self._on_leave_internal, add='+')))

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
            except:
                pass
        self._internal_bind_ids.clear()

    def _config_styles(self):
        current_style = self.styles.get_style()
        return {
            "bg": current_style.component.frame.bg.color,
            "fg": current_style.component.link.normal.fg.color,
            "activebackground": current_style.component.frame.bg.color,
            "activeforeground": current_style.component.link.press.fg.color,
            "hover_bg": current_style.component.frame.bg.color,
            "hover_fg": current_style.component.link.hover.fg.color,
            "focus_bg": current_style.component.frame.bg.color,
            "focus_fg": current_style.component.link.focus.fg.color if hasattr(current_style.component.link, 'focus') else current_style.component.link.hover.fg.color,
            "disable_bg": current_style.component.frame.bg.color,
            "disable_fg": current_style.component.link.disable.fg.color
        }

    def _register_listeners(self):
        self.styles.on_theme_changed.add_listener(self._on_theme_changed_internal)
        self.localization.on_language_changed.add_listener(self._on_language_changed_internal)

    def _unregister_listeners(self):
        self.styles.on_theme_changed.remove_listener(self._on_theme_changed_internal)
        self.localization.on_language_changed.remove_listener(self._on_language_changed_internal)

    def _on_theme_changed_internal(self, theme):
        self._button_style = self._config_styles()
        self.refresh()

    def _on_language_changed_internal(self, language):
        self.refresh_text()

    def _apply_style(self):
        if self._disabled:
            bg = self._button_style.get("disable_bg", self._button_style["bg"])
            fg = self._button_style.get("disable_fg", self._button_style["fg"])
        elif self._hovered:
            bg = self._button_style.get("hover_bg", self._button_style["bg"])
            fg = self._button_style.get("hover_fg", self._button_style["fg"])
        else:
            bg = self._button_style["bg"]
            fg = self._button_style["fg"]
        self._tk_label.config(bg=bg, fg=fg)

    def _on_button_press(self, event):
        if not self._disabled:
            self._tk_label.config(fg=self._button_style["activeforeground"])

    def _on_button_release(self, event):
        if not self._disabled:
            if self._hovered:
                self._tk_label.config(fg=self._button_style["hover_fg"])
            else:
                self._tk_label.config(fg=self._button_style["fg"])
            self.on_click.broadcast()
            if self._url:
                webbrowser.open(self._url)

    def _on_enter_internal(self, event):
        if not self._disabled:
            self._hovered = True
            self._tk_label.config(fg=self._button_style["hover_fg"])
            self.on_enter.broadcast()

    def _on_leave_internal(self, event):
        if not self._disabled:
            self._hovered = False
            self._tk_label.config(fg=self._button_style["fg"])
            self.on_leave.broadcast()

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

    def set_url(self, url):
        self._url = url

    def get_url(self):
        return self._url

    def set_disabled(self, disabled):
        self._disabled = disabled
        self._tk_label.config(cursor="no" if disabled else "hand2", takefocus=not disabled)
        self._apply_style()

    def is_disabled(self):
        return self._disabled
