import tkinter as tk
from ..core.view import View
from ..core.manager.localization_manager import LocalizationManager, LocalizedText
from ..core.manager.ui_style_manager import UIStyleManager, StyleObject
from ..core.manager.event_manager import Event
from ..core.utils.utils import Utils
from ..core.utils.asset_loader import AssetLoader


class CheckButton(View):
    def __init__(self, master=None, text=None, **kwargs):
        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")
        self._text = text
        self._kwargs = kwargs
        self._tk_frame = None
        self._indicator_label = None
        self._text_label = None
        self._styles = None
        self._indicator_size = 16
        self._border_width = 1
        self._variable = kwargs.pop('variable', None)
        self._onvalue = kwargs.pop('onvalue', 1)
        self._offvalue = kwargs.pop('offvalue', 0)
        self._selected = False
        self._hovered = False
        self._focused = False
        self._pressed = False
        self._disabled = False
        self._empty_pixel = tk.PhotoImage(width=1, height=1)
        self._internal_bind_ids = []

        self.styles = UIStyleManager.get_instance()
        self.localization = LocalizationManager.get_instance()

        self.on_select = Event()
        self.on_configure = Event()
        self.on_variable_change = Event()

        super().__init__(master, **kwargs)

    def _build_widget(self, master=None, **kwargs):
        master_tk = self._get_master_tk()
        self._config_styles()

        display_text = self._text.get_text() if hasattr(self._text, 'get_text') else self._text if self._text else ""

        default_kwargs = {
            "bg": self._styles.normal.bg,
            "relief": tk.FLAT,
            "highlightthickness": 0,
            "takefocus": not self._disabled
        }
        default_kwargs.update(self._kwargs)

        self._tk_frame = tk.Frame(master_tk, **default_kwargs)

        self._indicator_label = tk.Label(
            self._tk_frame,
            width=self._indicator_size,
            height=self._indicator_size,
            bd=0,
            highlightthickness=self._border_width,
            relief=tk.FLAT,
            compound="center",
            image=self._empty_pixel,
            cursor="hand2"
        )
        self._indicator_label.pack(side=tk.LEFT, padx=(0, 5))

        self._text_label = tk.Label(
            self._tk_frame,
            text=display_text,
            bg=self._styles.normal.bg,
            fg=self._styles.normal.fg,
            cursor="hand2"
        )
        self._text_label.pack(side=tk.LEFT)

        self._bind_events()
        self._register_listeners()
        self._draw_indicator()

        if self._variable:
            try:
                val = self._variable.get()
                self._selected = (val == self._onvalue)
            except:
                pass
            self._variable.trace_add('write', self._on_variable_changed)
            self._draw_indicator()

        return self._tk_frame

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

    def _bind_events(self):
        self._internal_bind_ids.append((self._tk_frame, '<Configure>', self._tk_frame.bind('<Configure>', self._on_configure_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<ButtonPress-1>', self._tk_frame.bind('<ButtonPress-1>', self._on_press_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<ButtonRelease-1>', self._tk_frame.bind('<ButtonRelease-1>', self._on_click_release, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<FocusIn>', self._tk_frame.bind('<FocusIn>', self._on_focus_in, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<FocusOut>', self._tk_frame.bind('<FocusOut>', self._on_focus_out, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<Key-space>', self._tk_frame.bind('<Key-space>', self._on_key_toggle, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<Key-Return>', self._tk_frame.bind('<Key-Return>', self._on_key_toggle, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<Enter>', self._tk_frame.bind('<Enter>', self._on_enter, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<Leave>', self._tk_frame.bind('<Leave>', self._on_leave, add='+')))

        for widget in [self._indicator_label, self._text_label]:
            self._internal_bind_ids.append((widget, '<ButtonPress-1>', widget.bind('<ButtonPress-1>', self._on_press_internal, add='+')))
            self._internal_bind_ids.append((widget, '<ButtonRelease-1>', widget.bind('<ButtonRelease-1>', self._on_click_release, add='+')))
            self._internal_bind_ids.append((widget, '<Enter>', widget.bind('<Enter>', self._on_enter, add='+')))
            self._internal_bind_ids.append((widget, '<Leave>', widget.bind('<Leave>', self._on_leave, add='+')))

    def _register_listeners(self):
        self.styles.on_theme_changed.add_listener(self._on_theme_changed_internal)
        self.localization.on_language_changed.add_listener(self._on_language_changed_internal)

    def _unregister_listeners(self):
        self.styles.on_theme_changed.remove_listener(self._on_theme_changed_internal)
        self.localization.on_language_changed.remove_listener(self._on_language_changed_internal)

    def _on_theme_changed_internal(self, theme):
        self._config_styles()
        self.refresh_theme()

    def _on_language_changed_internal(self, language):
        self.refresh_text()

    def _on_configure_internal(self, event):
        self.on_configure.broadcast(event)

    def _on_enter(self, event):
        if not self._disabled:
            self._hovered = True
            self._draw_indicator()
        return "break"

    def _on_leave(self, event):
        if not self._disabled:
            self._hovered = False
            self._pressed = False
            self._draw_indicator()
        return "break"

    def _on_press_internal(self, event):
        if not self._disabled:
            self._tk_frame.focus_set()
        return "break"

    def _on_click_release(self, event):
        if not self._disabled:
            self._toggle()
        return "break"

    def _on_focus_in(self, event):
        if not self._disabled:
            self._focused = True
            self._draw_indicator()

    def _on_focus_out(self, event):
        self._focused = False
        self._draw_indicator()

    def _on_key_toggle(self, event):
        if not self._disabled:
            self._toggle()
        return "break"

    def _on_variable_changed(self, *args):
        if self._variable:
            try:
                val = self._variable.get()
                new_selected = (val == self._onvalue)
                if new_selected != self._selected:
                    self._selected = new_selected
                    self._draw_indicator()
                    self.on_variable_change.broadcast(self._selected)
            except:
                pass

    def _toggle(self):
        self._selected = not self._selected
        if self._variable:
            try:
                self._variable.set(self._onvalue if self._selected else self._offvalue)
            except:
                pass
        self._draw_indicator()
        self.on_select.broadcast()

    def _get_current_style(self):
        if self._disabled:
            return self._styles.disable
        if self._selected:
            return self._styles.selected_focus if (self._focused or self._hovered) else self._styles.selected
        return self._styles.focus if (self._focused or self._hovered) else self._styles.normal

    def _draw_indicator(self):
        style = self._get_current_style()

        cursor = "hand2" if not self._disabled else "no"
        self._tk_frame.config(cursor=cursor)
        self._indicator_label.config(cursor=cursor)
        self._text_label.config(cursor=cursor)

        self._indicator_label.config(
            bg=style.indicator_bg,
            highlightbackground=style.indicator_border,
            highlightcolor=style.indicator_border
        )

        if self._selected:
            checkmark_path = AssetLoader.get_theme_image_path("checkbutton_checkmark.png")
            check_image = tk.PhotoImage(file=checkmark_path)
            recolored_image = Utils.recolor_image(check_image, style.indicator_bg, style.indicator_fg)
            self._indicator_label.config(image=recolored_image)
            self._indicator_label.image = recolored_image
        else:
            self._indicator_label.config(image=self._empty_pixel)

        self._text_label.config(fg=style.fg, bg=style.bg)
        self._tk_frame.config(bg=style.bg)

    def _config_styles(self):
        current_style = self.styles.get_style()
        styles_dict = {
            'indicator': {'size': self._indicator_size},
            'normal': {
                'bg': current_style.component.checkbutton.normal.bg.color,
                'fg': current_style.component.checkbutton.normal.fg.color,
                'border': current_style.component.checkbutton.normal.border.color,
                'indicator_bg': current_style.component.checkbutton.normal.indicator_bg.color,
                'indicator_fg': current_style.component.checkbutton.normal.indicator_fg.color,
                'indicator_border': current_style.component.checkbutton.normal.indicator_border.color,
                'font': current_style.font.normal
            },
            'hover': {
                'bg': current_style.component.checkbutton.hover.bg.color,
                'fg': current_style.component.checkbutton.hover.fg.color,
                'border': current_style.component.checkbutton.hover.border.color,
                'indicator_bg': current_style.component.checkbutton.hover.indicator_bg.color,
                'indicator_fg': current_style.component.checkbutton.hover.indicator_fg.color,
                'indicator_border': current_style.component.checkbutton.hover.indicator_border.color
            },
            'press': {
                'bg': current_style.component.checkbutton.press.bg.color,
                'fg': current_style.component.checkbutton.press.fg.color,
                'border': current_style.component.checkbutton.press.border.color,
                'indicator_bg': current_style.component.checkbutton.press.indicator_bg.color,
                'indicator_fg': current_style.component.checkbutton.press.indicator_fg.color,
                'indicator_border': current_style.component.checkbutton.press.indicator_border.color
            },
            'focus': {
                'bg': current_style.component.checkbutton.focus.bg.color,
                'fg': current_style.component.checkbutton.focus.fg.color,
                'border': current_style.component.checkbutton.focus.border.color,
                'indicator_bg': current_style.component.checkbutton.focus.indicator_bg.color,
                'indicator_fg': current_style.component.checkbutton.focus.indicator_fg.color,
                'indicator_border': current_style.component.checkbutton.focus.indicator_border.color
            },
            'selected': {
                'bg': current_style.component.checkbutton.selected.bg.color,
                'fg': current_style.component.checkbutton.selected.fg.color,
                'border': current_style.component.checkbutton.selected.border.color,
                'indicator_bg': current_style.component.checkbutton.selected.indicator_bg.color,
                'indicator_fg': current_style.component.checkbutton.selected.indicator_fg.color,
                'indicator_border': current_style.component.checkbutton.selected.indicator_border.color
            },
            'selected_focus': {
                'bg': current_style.component.checkbutton.selected_focus.bg.color,
                'fg': current_style.component.checkbutton.selected_focus.fg.color,
                'border': current_style.component.checkbutton.selected_focus.border.color,
                'indicator_bg': current_style.component.checkbutton.selected_focus.indicator_bg.color,
                'indicator_fg': current_style.component.checkbutton.selected_focus.indicator_fg.color,
                'indicator_border': current_style.component.checkbutton.selected_focus.indicator_border.color
            },
            'disable': {
                'bg': current_style.component.checkbutton.disable.bg.color,
                'fg': current_style.component.checkbutton.disable.fg.color,
                'border': current_style.component.checkbutton.disable.border.color,
                'indicator_bg': current_style.component.checkbutton.disable.indicator_bg.color,
                'indicator_fg': current_style.component.checkbutton.disable.indicator_fg.color,
                'indicator_border': current_style.component.checkbutton.disable.indicator_border.color
            }
        }
        self._styles = StyleObject(styles_dict)

    def refresh_theme(self):
        self._config_styles()
        style = self._get_current_style()
        self._tk_frame.config(bg=style.bg)
        self._draw_indicator()

    def refresh_text(self):
        if self._text:
            display_text = self._text.get_text() if hasattr(self._text, 'get_text') else self._text
            self._text_label.config(text=display_text)

    def refresh(self):
        self.refresh_theme()
        self.refresh_text()

    def set_disabled(self, disabled):
        self._disabled = disabled
        self._tk_frame.config(takefocus=not disabled)
        self._draw_indicator()

    def is_disabled(self):
        return self._disabled

    def select(self):
        if not self._selected:
            self._toggle()

    def deselect(self):
        if self._selected:
            self._toggle()

    def toggle(self):
        self._toggle()

    def invoke(self):
        self._toggle()

    def set_text(self, text):
        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")
        self._text = text
        self.refresh_text()
