import tkinter as tk
from ..core.view import View
from ..core.manager.ui_style_manager import UIStyleManager
from .entry import Entry
from .normal_button import NormalButton, ButtonStyleType
from ..core.manager.localization_manager import LocalizedText
from ..core.manager.event_manager import Event

class BrowseEntry(View):
    def __init__(self, master=None, text=None, **kwargs):
        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")
        self._text = text
        self._kwargs = kwargs
        self._disabled = False
        self._tk_frame = None
        self._entry = None
        self._button = None

        self.styles = UIStyleManager.get_instance()

        self.on_entry_text_changed = Event()
        self.on_browse_clicked = Event()
        self.on_focus_out = Event()

        super().__init__(master, **kwargs)

    def _build_widget(self, master=None, **kwargs):
        master_tk = self._get_master_tk()
        
        bg_color = self.styles.get_style().component.frame.bg.color
        
        self._tk_frame = tk.Frame(master_tk, bg=bg_color)
        self._tk_frame.grid_columnconfigure(0, weight=1)

        self._entry = Entry(self._tk_frame, **self._kwargs)
        if self._text is not None:
            self._entry.set_text(self._text)
        self._entry.on_entry_text_changed.add_listener(self._on_entry_text_changed_internal)
        self._entry.on_focus_out.add_listener(self._on_focus_out_internal)
        self._entry.grid(row=0, column=0, sticky=tk.EW)

        self._button = NormalButton(self._tk_frame, text=LocalizedText("browse"), width=7, style_type=ButtonStyleType.Primary)
        self._button.on_click.add_listener(lambda: self.on_browse_clicked.broadcast())
        self._button.grid(row=0, column=1, padx=(8, 0), sticky=tk.E)
        
        self._register_listeners()
        
        return self._tk_frame

    def _on_entry_text_changed_internal(self, text):
        self.on_entry_text_changed.broadcast(text)

    def _on_focus_out_internal(self):
        self.on_focus_out.broadcast()

    def _register_listeners(self):
        self.styles.on_theme_changed.add_listener(self._on_theme_changed_internal)

    def _unregister_listeners(self):
        self.styles.on_theme_changed.remove_listener(self._on_theme_changed_internal)

    def _on_theme_changed_internal(self, theme):
        bg_color = self.styles.get_style().component.frame.bg.color
        self._tk_frame.config(bg=bg_color)

    def _on_destroy(self):
        self._unregister_listeners()
        self._entry.destroy()
        self._button.destroy()
        super()._on_destroy()

    def set_text(self, text):
        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")
        self._entry.set_text(text)

    def set_disabled(self, disabled):
        self._disabled = disabled
        self._entry.set_disabled(disabled)
        self._button.set_disabled(disabled)

    def is_disabled(self):
        return self._disabled
