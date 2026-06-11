import tkinter as tk
from enum import Enum
from .button import Button
from ..core.manager.localization_manager import LocalizationManager, LocalizedText
from ..core.manager.ui_style_manager import UIStyleManager, StyleObject
from ..core.manager.event_manager import Event
from ..core.utils.platform_input_bind import PlatformInputBind


class ButtonStyleType(Enum):
    Primary = "primary"
    Secondary = "secondary"


class ButtonSize(Enum):
    Small = "small"
    Normal = "normal"
    Large = "large"


class NormalButton(Button):
    def __init__(self, master=None, text=None, style_type=ButtonStyleType.Primary,
                 size=ButtonSize.Normal, **kwargs):
        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")
        if not isinstance(style_type, ButtonStyleType):
            raise TypeError("style_type 参数必须是 ButtonStyleType 枚举类型")
        if not isinstance(size, ButtonSize):
            raise TypeError("size 参数必须是 ButtonSize 枚举类型")

        self._text = text
        self._style_type = style_type
        self._size = size
        self._kwargs = kwargs
        self._tk_button = None
        self._styles = None
        self._disabled = False
        self._hovered = False
        self._pressed = False
        self._focused = False

        self.styles = UIStyleManager.get_instance()
        self.localization = LocalizationManager.get_instance()
        size_value = self._size.value
        preset = self.styles.get_size_preset(size_value)
        if 'padx' not in kwargs:
            kwargs['padx'] = preset['padx']
        if 'pady' not in kwargs:
            kwargs['pady'] = preset['pady']

        self.on_click = Event()
        self.on_enter = Event()
        self.on_leave = Event()
        self.on_configure = Event()
        self.on_scroll = Event()
        self.on_press = Event()

        self._internal_bind_ids = []

        super().__init__(master, text=text, **kwargs)

    def _build_widget(self, master=None, **kwargs):
        master_tk = self._get_master_tk()

        display_text = self._text.get_text() if hasattr(self._text, 'get_text') else self._text if self._text else ""

        width = self._kwargs.pop('width', None)
        font = self._kwargs.pop('font', None)
        padx = self._kwargs.pop('padx', None)
        pady = self._kwargs.pop('pady', None)

        self._button_style = self._config_styles()

        size_value = self._size.value if hasattr(self._size, 'value') else self._size
        preset = self.styles.get_size_preset(size_value)

        default_kwargs = {
            "text": display_text,
            "bg": self._button_style["bg"],
            "fg": self._button_style["fg"],
            "font": font if font else self.styles.get_style().font.normal,
            "relief": tk.FLAT,
            "borderwidth": 0,
            "highlightthickness": 0,
            "takefocus": not self._disabled,
            "cursor": "hand2",
            "padx": padx if padx is not None else preset['padx'],
            "pady": pady if pady is not None else preset['pady']
        }
        default_kwargs.update(self._kwargs)

        self._tk_button = tk.Label(master_tk, **default_kwargs)

        if width is not None:
            self._tk_button.config(width=width)

        self._internal_bind_ids.append((self._tk_button, '<ButtonPress-1>', self._tk_button.bind('<ButtonPress-1>', self._on_button_press, add='+')))
        self._internal_bind_ids.append((self._tk_button, '<ButtonRelease-1>', self._tk_button.bind('<ButtonRelease-1>', self._on_button_release, add='+')))
        self._internal_bind_ids.append((self._tk_button, '<Enter>', self._tk_button.bind('<Enter>', self._on_enter_internal, add='+')))
        self._internal_bind_ids.append((self._tk_button, '<Leave>', self._tk_button.bind('<Leave>', self._on_leave_internal, add='+')))
        self._internal_bind_ids.append((self._tk_button, '<Configure>', self._tk_button.bind('<Configure>', self._on_configure_internal, add='+')))
        self._internal_bind_ids.append((self._tk_button, '<FocusIn>', self._tk_button.bind('<FocusIn>', self._on_focus_in, add='+')))
        self._internal_bind_ids.append((self._tk_button, '<FocusOut>', self._tk_button.bind('<FocusOut>', self._on_focus_out, add='+')))
        self._internal_bind_ids.extend(PlatformInputBind.bind_mousewheel(self._tk_button, self._on_mouse_wheel))
        self._internal_bind_ids.append((self._tk_button, '<KeyPress-space>', self._tk_button.bind('<KeyPress-space>', self._on_key_press, add='+')))
        self._internal_bind_ids.append((self._tk_button, '<KeyRelease-space>', self._tk_button.bind('<KeyRelease-space>', self._on_key_release, add='+')))
        self._internal_bind_ids.append((self._tk_button, '<KeyPress-Return>', self._tk_button.bind('<KeyPress-Return>', self._on_key_press, add='+')))
        self._internal_bind_ids.append((self._tk_button, '<KeyRelease-Return>', self._tk_button.bind('<KeyRelease-Return>', self._on_key_release, add='+')))

        self._register_listeners()
        self._apply_style()

        return self._tk_button

    def _unbind_internal_events(self):
        for widget, sequence, funcid in self._internal_bind_ids:
            try:
                widget.unbind(sequence, funcid)
            except:
                pass
        self._internal_bind_ids.clear()

    def _on_destroy(self):
        self._unregister_listeners()
        self._unbind_internal_events()
        super()._on_destroy()

    def _config_styles(self):
        current_style = self.styles.get_style()

        if self._style_type == ButtonStyleType.Primary:
            return {
                "bg": current_style.component.button.primary.normal.bg.color,
                "fg": current_style.component.button.primary.normal.fg.color,
                "activebackground": current_style.component.button.primary.press.bg.color,
                "activeforeground": current_style.component.button.primary.press.fg.color,
                "hover_bg": current_style.component.button.primary.hover.bg.color,
                "hover_fg": current_style.component.button.primary.hover.fg.color,
                "focus_bg": current_style.component.button.primary.focus.bg.color,
                "focus_fg": current_style.component.button.primary.focus.fg.color,
                "disable_bg": current_style.component.button.primary.disable.bg.color,
                "disable_fg": current_style.component.button.primary.disable.fg.color,
                "border": current_style.component.button.primary.normal.border.color,
                "hover_border": current_style.component.button.primary.hover.border.color,
                "press_border": current_style.component.button.primary.press.border.color,
                "focus_border": current_style.component.button.primary.focus.border.color,
                "disable_border": current_style.component.button.primary.disable.border.color
            }
        else:
            return {
                "bg": current_style.component.button.secondary.normal.bg.color,
                "fg": current_style.component.button.secondary.normal.fg.color,
                "activebackground": current_style.component.button.secondary.press.bg.color,
                "activeforeground": current_style.component.button.secondary.press.fg.color,
                "hover_bg": current_style.component.button.secondary.hover.bg.color,
                "hover_fg": current_style.component.button.secondary.hover.fg.color,
                "focus_bg": current_style.component.button.secondary.focus.bg.color,
                "focus_fg": current_style.component.button.secondary.focus.fg.color,
                "disable_bg": current_style.component.button.secondary.disable.bg.color,
                "disable_fg": current_style.component.button.secondary.disable.fg.color,
                "border": current_style.component.button.secondary.normal.border.color,
                "hover_border": current_style.component.button.secondary.hover.border.color,
                "press_border": current_style.component.button.secondary.press.border.color,
                "focus_border": current_style.component.button.secondary.focus.border.color,
                "disable_border": current_style.component.button.secondary.disable.border.color
            }

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

    def _on_mouse_wheel(self, event, delta):
        self.on_scroll.broadcast(-1 * delta)
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
            border = self._button_style.get("disable_border", self._button_style.get("border", "#000000"))
            cursor = "no"
        elif self._pressed:
            bg = self._button_style.get("activebackground", self._button_style["bg"])
            fg = self._button_style.get("activeforeground", self._button_style["fg"])
            border = self._button_style.get("press_border", self._button_style.get("border", "#000000"))
            cursor = "hand2"
        elif self._focused:
            bg = self._button_style.get("focus_bg", self._button_style["bg"])
            fg = self._button_style.get("focus_fg", self._button_style["fg"])
            border = self._button_style.get("focus_border", self._button_style.get("border", "#000000"))
            cursor = "hand2"
        elif self._hovered:
            bg = self._button_style.get("hover_bg", self._button_style["bg"])
            fg = self._button_style.get("hover_fg", self._button_style["fg"])
            border = self._button_style.get("hover_border", self._button_style.get("border", "#000000"))
            cursor = "hand2"
        else:
            bg = self._button_style["bg"]
            fg = self._button_style["fg"]
            border = self._button_style.get("border", "#000000")
            cursor = "hand2"

        self._tk_button.config(bg=bg, fg=fg, cursor=cursor)
        self._tk_button.config(relief=tk.FLAT, borderwidth=1, highlightthickness=1,
                               highlightbackground=border, highlightcolor=border)

    def refresh_theme(self):
        self._button_style = self._config_styles()
        self._apply_style()

    def refresh_text(self):
        if self._text:
            display_text = self._text.get_text() if hasattr(self._text, 'get_text') else self._text
            self._tk_button.config(text=display_text)

    def refresh(self):
        self.refresh_theme()
        self.refresh_text()

    def set_text(self, text):
        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")
        self._text = text
        self.refresh_text()

    def set_width(self, width):
        self._tk_button.config(width=width)

    def set_font(self, font):
        self._tk_button.config(font=font)

    def set_style_type(self, style_type):
        if not isinstance(style_type, ButtonStyleType):
            raise TypeError("style_type 参数必须是 ButtonStyleType 枚举类型")
        self._style_type = style_type
        self.refresh_theme()

    def set_size(self, size):
        if not isinstance(size, ButtonSize):
            raise TypeError("size 参数必须是 ButtonSize 枚举类型")
        self._size = size
        preset = self.styles.get_size_preset(size.value)
        self._tk_button.config(padx=preset['padx'], pady=preset['pady'])

    def set_disabled(self, disabled):
        self._disabled = disabled
        self._tk_button.config(takefocus=not disabled)
        self._apply_style()

    def is_disabled(self):
        return self._disabled
