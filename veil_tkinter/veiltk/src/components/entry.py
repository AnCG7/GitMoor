import tkinter as tk
import enum
from ..core.view import View
from ..core.manager.ui_style_manager import UIStyleManager, StyleObject
from ..core.manager.event_manager import Event
from ..core.manager.localization_manager import LocalizedText, LocalizationManager

class EntryMode(enum.Enum):
    Normal = "normal"
    Readonly = "readonly"
    Disable = "disable"
    AllDisable = "all_disable"

class EntryInteractionState(enum.Enum):
    Idle = "none"
    Hover = "hover"
    Active = "active"
    Focus = "focus"

class Entry(View):
    def __init__(self, master=None, text=None, **kwargs):
        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")
        
        self._text = text
        self._kwargs = kwargs
        self._tk_frame = None
        self._tk_entry = None
        self._styles = None
        self._entry_mode = EntryMode.Normal
        self._interaction_state = EntryInteractionState.Idle
        self._is_global_click_bound = False
        self._global_click_id = None
        self._override_state_config = {}
        self._internal_bind_ids = []
        self.lm = LocalizationManager.get_instance()

        self.on_focus_in = Event()
        self.on_focus_out = Event()
        self.on_key_press = Event()
        self.on_configure = Event()
        self.on_click = Event()
        self.on_double_click = Event()
        self.on_triple_click = Event()
        self.on_enter = Event()
        self.on_leave = Event()
        self.on_press = Event()
        self.on_release = Event()
        self.on_motion = Event()
        self.on_entry_text_changed = Event()
        
        super().__init__(master, **kwargs)

    def _build_widget(self, master=None, **kwargs):
        master_tk = self._get_master_tk()
            
        self.styles = UIStyleManager.get_instance()
        self._config_styles()

        size_preset = self.styles.get_size_preset('normal')
        self._padx = 8
        self._pady = size_preset['pady']

        default_kwargs = {
            "bg": self._styles.normal.bg,
            "relief": tk.FLAT,
            "borderwidth": 0,
            "highlightthickness": 1,
            "highlightbackground": self._styles.normal.border,
            "highlightcolor": self._styles.normal.border,
            "padx": self._padx,
            "pady": self._pady
        }
        default_kwargs.update(self._kwargs)

        self._tk_frame = tk.Frame(master_tk, **default_kwargs)

        self._textvariable = tk.StringVar()
        if self._text:
            self._textvariable.set(self._text.get_text())
        self._textvariable.trace_add('write', self._on_text_changed)

        self._tk_entry = tk.Entry(
            self._tk_frame,
            bg=self._styles.normal.bg,
            fg=self._styles.normal.fg,
            font=self._styles.normal.font,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            insertbackground=self._styles.normal.insertbackground,
            textvariable=self._textvariable,
        )
        self._tk_entry.pack(fill=tk.BOTH, expand=True)

        bind_targets = [self._tk_frame, self._tk_entry]
        for target in bind_targets:
            self._internal_bind_ids.append((target, '<Button-1>', target.bind('<Button-1>', self._on_click_internal, add='+')))
            self._internal_bind_ids.append((target, '<Double-Button-1>', target.bind('<Double-Button-1>', self._on_double_click_internal, add='+')))
            self._internal_bind_ids.append((target, '<Triple-Button-1>', target.bind('<Triple-Button-1>', self._on_triple_click_internal, add='+')))
            self._internal_bind_ids.append((target, '<Enter>', target.bind('<Enter>', self._on_enter_internal, add='+')))
            self._internal_bind_ids.append((target, '<Leave>', target.bind('<Leave>', self._on_leave_internal, add='+')))
            self._internal_bind_ids.append((target, '<ButtonPress-1>', target.bind('<ButtonPress-1>', self._on_press_internal, add='+')))
            self._internal_bind_ids.append((target, '<ButtonRelease-1>', target.bind('<ButtonRelease-1>', self._on_release_internal, add='+')))
            self._internal_bind_ids.append((target, '<Motion>', target.bind('<Motion>', self._on_motion_internal, add='+')))
            self._internal_bind_ids.append((target, '<B1-Motion>', target.bind('<B1-Motion>', self._on_motion_internal, add='+')))

        self._internal_bind_ids.append((self._tk_entry, '<FocusIn>', self._tk_entry.bind('<FocusIn>', self._on_focus_in_internal, add='+')))
        self._internal_bind_ids.append((self._tk_entry, '<FocusOut>', self._tk_entry.bind('<FocusOut>', self._on_focus_out_internal, add='+')))
        self._internal_bind_ids.append((self._tk_entry, '<KeyPress>', self._tk_entry.bind('<KeyPress>', self._on_key_press_internal, add='+')))
        self._internal_bind_ids.append((self._tk_entry, '<Configure>', self._tk_entry.bind('<Configure>', self._on_configure_internal, add='+')))

        self._register_listeners()
        self._update_styles()
        self._update_global_click_binding()
        
        return self._tk_frame

    def _on_destroy(self):
        self._unregister_listeners()
        self._unbind_internal_events()
        self._unbind_global_click()
        super()._on_destroy()

    def _unbind_internal_events(self):
        for widget, sequence, funcid in self._internal_bind_ids:
            try:
                widget.unbind(sequence, funcid)
            except:
                pass
        self._internal_bind_ids.clear()

    def _update_styles(self):
        takefocus_val = 1
        cursor = None

        if self._entry_mode in self._override_state_config:
            config = self._override_state_config[self._entry_mode]
            cursor = config.get('cursor')
            if 'takefocus' in config:
                takefocus_val = config['takefocus']

            if self._entry_mode == EntryMode.AllDisable:
                entry_state, style, takefocus_val = 'disabled', self._styles.disable, 0
            elif self._entry_mode == EntryMode.Disable:
                entry_state, style, takefocus_val = 'readonly', self._styles.disable, 0
            elif self._entry_mode == EntryMode.Readonly:
                entry_state = 'readonly'
                if self._interaction_state == EntryInteractionState.Focus: style = self._styles.focus
                elif self._interaction_state == EntryInteractionState.Hover: style = self._styles.hover
                elif self._interaction_state == EntryInteractionState.Active: style = self._styles.active
                else: style = self._styles.normal
            else:
                entry_state = 'normal'
                if self._interaction_state == EntryInteractionState.Focus: style = self._styles.focus
                elif self._interaction_state == EntryInteractionState.Hover: style = self._styles.hover
                elif self._interaction_state == EntryInteractionState.Active: style = self._styles.active
                else: style = self._styles.normal
        elif self._entry_mode == EntryMode.AllDisable:
            cursor, entry_state, style, takefocus_val = 'no', 'disabled', self._styles.disable, 0
        elif self._entry_mode == EntryMode.Disable:
            cursor, entry_state, style, takefocus_val = 'no', 'readonly', self._styles.disable, 0
        elif self._entry_mode == EntryMode.Readonly:
            cursor, entry_state = 'xterm', 'readonly'
            if self._interaction_state == EntryInteractionState.Focus: style = self._styles.focus
            elif self._interaction_state == EntryInteractionState.Hover: style = self._styles.hover
            elif self._interaction_state == EntryInteractionState.Active: style = self._styles.active
            else: style = self._styles.normal
        else:
            cursor, entry_state = 'xterm', 'normal'
            if self._interaction_state == EntryInteractionState.Focus: style = self._styles.focus
            elif self._interaction_state == EntryInteractionState.Hover: style = self._styles.hover
            elif self._interaction_state == EntryInteractionState.Active: style = self._styles.active
            else: style = self._styles.normal

        self._tk_frame.config(
            bg=style.bg,
            highlightbackground=style.border,
            highlightcolor=style.border,
            cursor=cursor,
            takefocus=0
        )

        self._tk_entry.config(
            state=entry_state,
            bg=style.bg,
            fg=style.fg,
            cursor=cursor,
            takefocus=takefocus_val,
            insertbackground=style.fg
        )

        if self._entry_mode == EntryMode.AllDisable:
            self._tk_entry.config(disabledbackground=style.bg, disabledforeground=style.fg)
        if self._entry_mode in [EntryMode.Readonly, EntryMode.Disable]:
            self._tk_entry.config(readonlybackground=style.bg)

        self._tk_entry.config(
            selectbackground=self._styles.selected_font.bg,
            selectforeground=self._styles.selected_font.fg
        )

    def _get_rel_x(self, event):
        if event.widget == self._tk_frame:
            entry_x = self._tk_entry.winfo_x()
            return event.x - entry_x
        return event.x

    def _on_click_internal(self, event):
        if self._entry_mode not in [EntryMode.AllDisable, EntryMode.Disable]:
            rel_x = self._get_rel_x(event)
            target_index = self._tk_entry.index(f"@{rel_x}")
            self._tk_entry.icursor(target_index)
            self._tk_entry.selection_from(target_index)
            self.on_click.broadcast(event)

    def _on_motion_internal(self, event):
        if self._entry_mode not in [EntryMode.AllDisable, EntryMode.Disable]:
            if event.state & 0x0100:
                rel_x = self._get_rel_x(event)
                self._tk_entry.selection_to(f"@{rel_x}")
                self._tk_entry.icursor(f"@{rel_x}")
            self.on_motion.broadcast(event)

    def _on_focus_in_internal(self, event):
        if self._entry_mode in [EntryMode.AllDisable, EntryMode.Disable]:
            return "break"
        self._interaction_state = EntryInteractionState.Focus
        self._update_styles()
        self.on_focus_in.broadcast()

    def _on_focus_out_internal(self, event):
        if self._entry_mode not in [EntryMode.AllDisable, EntryMode.Disable]:
            self._interaction_state = EntryInteractionState.Idle
            self._update_styles()
        self.on_focus_out.broadcast()

    def _on_enter_internal(self, event):
        if self._entry_mode not in [EntryMode.AllDisable, EntryMode.Disable]:
            if self._tk_entry.focus_get() == self._tk_entry:
                self._interaction_state = EntryInteractionState.Focus
            else:
                self._interaction_state = EntryInteractionState.Hover
            self._update_styles()
            self.on_enter.broadcast(event)

    def _on_leave_internal(self, event):
        if self._entry_mode not in [EntryMode.AllDisable, EntryMode.Disable]:
            if self._interaction_state != EntryInteractionState.Focus:
                self._interaction_state = EntryInteractionState.Idle
                self._update_styles()
            self.on_leave.broadcast(event)

    def _on_press_internal(self, event):
        if self._entry_mode not in [EntryMode.AllDisable, EntryMode.Disable]:
            if self._tk_entry.focus_get() != self._tk_entry:
                self._interaction_state = EntryInteractionState.Active
                self._update_styles()
            self.on_press.broadcast(event)

            if event.widget == self._tk_frame:
                self._tk_entry.focus_set()
                entry_x = event.x - self._tk_entry.winfo_x()
                entry_y = event.y - self._tk_entry.winfo_y()
                if 0 <= entry_x < self._tk_entry.winfo_width() and 0 <= entry_y < self._tk_entry.winfo_height():
                    self._tk_entry.event_generate('<ButtonPress-1>', x=entry_x, y=entry_y)

    def _on_release_internal(self, event):
        if self._entry_mode not in [EntryMode.AllDisable, EntryMode.Disable]:
            if self._tk_entry.focus_get() == self._tk_entry:
                self._interaction_state = EntryInteractionState.Focus
            else:
                self._interaction_state = EntryInteractionState.Hover
            self._update_styles()
            self.on_release.broadcast(event)

    def _on_key_press_internal(self, event):
        if self._entry_mode not in [EntryMode.AllDisable, EntryMode.Readonly, EntryMode.Disable]:
            self.on_key_press.broadcast(event.char, event.keysym)

    def _on_text_changed(self, *args):
        self.on_entry_text_changed.broadcast(self._textvariable.get())

    def _on_configure_internal(self, event):
        self.on_configure.broadcast(event)

    def _on_double_click_internal(self, event):
        if self._entry_mode != EntryMode.AllDisable:
            self._tk_entry.selection_range(0, tk.END)
            self._tk_entry.icursor(tk.END)
            self.on_double_click.broadcast(event)
            return "break"

    def _on_triple_click_internal(self, event):
        if self._entry_mode != EntryMode.AllDisable:
            self._tk_entry.selection_range(0, tk.END)
            self.on_triple_click.broadcast(event)
            return "break"

    def _bind_global_click(self):
        if not self._is_global_click_bound:
            self._global_click_id = self._tk_frame.bind_all('<Button-1>', self._on_global_click, add='+')
            self._is_global_click_bound = True

    def _unbind_global_click(self):
        if self._is_global_click_bound:
            try:
                if self._global_click_id:
                    self._tk_frame.unbind_all('<Button-1>', funcid=self._global_click_id)
                    self._global_click_id = None
            except:
                pass
            self._is_global_click_bound = False

    def _update_global_click_binding(self):
        if self._entry_mode == EntryMode.AllDisable:
            self._unbind_global_click()
        else:
            self._bind_global_click()

    def _on_global_click(self, event):
        try:
            if not self._tk_frame.winfo_exists(): return
            if self._entry_mode not in [EntryMode.AllDisable]:
                if event.widget != self._tk_frame and event.widget != self._tk_entry:
                    try:
                        selected_text = self._tk_entry.selection_get()
                        if len(selected_text) > 0:
                            self.selection_clear()
                    except:
                        pass
        except tk.TclError: pass

    def _config_styles(self):
        current_state = self.styles.get_style()
        styles_dict = {
            'normal': {
                'bg': current_state.component.entry.normal.bg.color,
                'fg': current_state.component.label.fg.color,
                'insertbackground': current_state.component.label.fg.color,
                'font': current_state.font.normal,
                'border': current_state.component.entry.normal.border.color
            },
            'hover': {
                'bg': current_state.component.entry.hover.bg.color,
                'fg': current_state.component.entry.hover.fg.color,
                'border': current_state.component.entry.hover.border.color
            },
            'active': {
                'bg': current_state.component.entry.hover.bg.color,
                'fg': current_state.component.entry.hover.fg.color,
                'border': current_state.component.entry.hover.border.color
            },
            'focus': {
                'bg': current_state.component.button.secondary.hover.bg.color,
                'fg': current_state.component.label.fg.color,
                'border': current_state.component.entry.focus.border.color
            },
            'disable': {
                'bg': current_state.component.entry.disable.bg.color,
                'fg': current_state.component.entry.disable.fg.color,
                'border': current_state.component.entry.disable.border.color
            },
            'selected_font': {
                'bg': current_state.component.entry.selected_font.bg.color,
                'fg': current_state.component.entry.selected_font.fg.color
            }
        }
        self._styles = StyleObject(styles_dict)

    def _register_listeners(self):
        self.styles.on_theme_changed.add_listener(self._on_theme_changed_internal)
        self.lm.on_language_changed.add_listener(self._on_language_changed_internal)

    def _unregister_listeners(self):
        self.styles.on_theme_changed.remove_listener(self._on_theme_changed_internal)
        self.lm.on_language_changed.remove_listener(self._on_language_changed_internal)

    def _on_theme_changed_internal(self, theme):
        self._config_styles()
        self.refresh()

    def _on_language_changed_internal(self, language):
        if self._text is not None:
            self._textvariable.set(self._text.get_text())

    def set_mode(self, mode):
        if not isinstance(mode, EntryMode):
            raise ValueError("mode must be EntryMode enum value")
        self._entry_mode = mode
        self._update_global_click_binding()
        self.refresh()

    def set_disabled(self, disabled):
        self._entry_mode = EntryMode.Disable if disabled else EntryMode.Normal
        self._update_global_click_binding()
        self.refresh()

    def is_disabled(self):
        return self._entry_mode in [EntryMode.AllDisable, EntryMode.Disable]

    def refresh(self):
        self._interaction_state = EntryInteractionState.Idle
        self._update_styles()

    def focus_set(self):
        if self._entry_mode not in [EntryMode.AllDisable, EntryMode.Disable]:
            self._tk_entry.focus_set()

    def get(self):
        return self._tk_entry.get()

    def delete(self, first, last=None):
        return self._tk_entry.delete(first, last)

    def insert(self, index, string):
        return self._tk_entry.insert(index, string)

    def selection_clear(self):
        return self._tk_entry.selection_clear()

    def set_text(self, text):
        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")
        
        display_text = text.get_text() if text else ""
        
        current_state = self._tk_entry.cget('state')
        if current_state in ['disabled', 'readonly']:
            self._tk_entry.config(state='normal')
        self._tk_entry.delete(0, tk.END)
        self._tk_entry.insert(0, display_text)
        if current_state in ['disabled', 'readonly']:
            self._tk_entry.config(state=current_state)

    def set_state_config_override(self, state, config):
        if isinstance(state, EntryMode):
            if state not in self._override_state_config:
                self._override_state_config[state] = {}
            self._override_state_config[state].update(config)
            self._update_styles()
        else:
            raise ValueError("state must be EntryMode enum value")

    def set_cursor_override(self, state, cursor):
        if isinstance(state, EntryMode):
            if state not in self._override_state_config:
                self._override_state_config[state] = {}
            self._override_state_config[state]['cursor'] = cursor
            self._update_styles()
        else:
            raise ValueError("state must be EntryMode enum value")