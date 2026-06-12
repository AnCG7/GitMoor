import tkinter as tk
import tkinter.font as tkfont
import math
from ..core.view import View
from ..core.manager.ui_style_manager import UIStyleManager
from ..core.manager.event_manager import Event
from ..core.manager.localization_manager import LocalizationManager, LocalizedText
from ..core.utils.platform_input_bind import PlatformInputBind


class ListBoxItem(View):
    def __init__(self, master=None, text=None, index=-1, **kwargs):
        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")
        self._text = text
        self._index = index
        self._kwargs = kwargs
        self._tk_label = None
        self._styles = None
        self._button_style = None
        self._selected = False
        self._hovered = False
        self._pressed = False
        self._disabled = False
        self._internal_bind_ids = []

        self.styles = UIStyleManager.get_instance()

        kwargs['takefocus'] = kwargs.get('takefocus', False)

        self.on_click = Event()
        self.on_enter = Event()
        self.on_leave = Event()
        self.on_press = Event()
        self.on_release = Event()
        self.on_scroll = Event()

        super().__init__(master, **kwargs)

    def _build_widget(self, master=None, **kwargs):
        master_tk = self._get_master_tk()
            
        self._button_style = self._config_styles()

        display_text = self._text.get_text() if hasattr(self._text, 'get_text') else ""
        anchor = self._kwargs.pop('anchor', 'w')
        justify = self._kwargs.pop('justify', 'left')
        padx = self._kwargs.pop('padx', 4)
        pady = self._kwargs.pop('pady', 4)

        self._tk_label = tk.Label(
            master_tk,
            text=display_text,
            bg=self._button_style["bg"],
            fg=self._button_style["fg"],
            font=self.styles.get_style().font.normal,
            anchor=anchor,
            justify=justify,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            padx=padx,
            pady=pady,
            takefocus=False,
            cursor="hand2"
        )

        self._internal_bind_ids.append((self._tk_label, '<ButtonPress-1>', self._tk_label.bind('<ButtonPress-1>', self._on_button_press, add='+')))
        self._internal_bind_ids.append((self._tk_label, '<ButtonRelease-1>', self._tk_label.bind('<ButtonRelease-1>', self._on_button_release, add='+')))
        self._internal_bind_ids.append((self._tk_label, '<Enter>', self._tk_label.bind('<Enter>', self._on_enter_internal, add='+')))
        self._internal_bind_ids.append((self._tk_label, '<Leave>', self._tk_label.bind('<Leave>', self._on_leave_internal, add='+')))
        self._internal_bind_ids.extend(PlatformInputBind.bind_mousewheel(self._tk_label, self._on_mouse_wheel))

        self._apply_style()
        
        return self._tk_label

    def _unbind_internal_events(self):
        for widget, sequence, funcid in self._internal_bind_ids:
            try:
                widget.unbind(sequence, funcid)
            except:
                pass
        self._internal_bind_ids.clear()

    def _on_destroy(self):
        self._unbind_internal_events()
        super()._on_destroy()

    def _config_styles(self):
        current_style = self.styles.get_style()
        item_style = current_style.component.listbox.item

        styles = {
            "normal": {"bg": item_style.normal.bg.color, "fg": item_style.normal.fg.color},
            "hover": {"bg": item_style.hover.bg.color, "fg": item_style.hover.fg.color},
            "press": {"bg": item_style.press.bg.color, "fg": item_style.press.fg.color},
            "selected": {"bg": item_style.selected.bg.color, "fg": item_style.selected.fg.color},
            "selected_hover": {"bg": item_style.selected_hover.bg.color, "fg": item_style.selected_hover.fg.color},
            "selected_press": {"bg": item_style.selected_press.bg.color, "fg": item_style.selected_press.fg.color},
            "disable": {"bg": item_style.disable.bg.color, "fg": item_style.disable.fg.color}
        }

        styles["bg"] = styles["normal"]["bg"]
        styles["fg"] = styles["normal"]["fg"]

        return styles

    def _apply_style(self):
        if self._disabled:
            state_key = "disable"
        elif self._selected:
            if self._pressed:
                state_key = "selected_press"
            elif self._hovered:
                state_key = "selected_hover"
            else:
                state_key = "selected"
        else:
            if self._pressed:
                state_key = "press"
            elif self._hovered:
                state_key = "hover"
            else:
                state_key = "normal"

        target_style = self._button_style.get(state_key, self._button_style["normal"])
        cursor = "no" if self._disabled else "hand2"
        self._tk_label.config(bg=target_style["bg"], fg=target_style["fg"], cursor=cursor)

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
            self.on_release.broadcast(event)

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

    def set_selected(self, selected):
        self._selected = selected
        self._apply_style()

    def is_selected(self):
        return self._selected

    def set_text(self, text):
        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")
        self._text = text
        if text:
            self._tk_label.config(text=text.get_text())
        else:
            self._tk_label.config(text="")

    def get_text(self):
        return self._text

    def set_disabled(self, disabled):
        self._disabled = disabled
        self._apply_style()

    def is_disabled(self):
        return self._disabled

    def refresh_theme(self):
        self._button_style = self._config_styles()
        self._apply_style()


class ListBox(View):
    def __init__(self, master=None, **kwargs):
        self.styles = UIStyleManager.get_instance()
        self.localization = LocalizationManager.get_instance()
        self._disabled = False
        self._item_pady = 4
        self._kwargs = kwargs

        self._items = []
        self._item_pool = []
        self._pool_windows = []
        self._selected_index = -1
        self._hover_index = -1
        self._tk_frame = None
        self.canvas = None
        self._internal_bind_ids = []

        self.on_select = Event()
        self.on_configure = Event()
        self.on_focus_in = Event()
        self.on_focus_out = Event()
        self.on_scroll = Event()
        
        super().__init__(master, **kwargs)

    def _build_widget(self, master=None, **kwargs):
        master_tk = self._get_master_tk()
        
        self._config_styles()

        default_kwargs = {
            "bg": self._styles.normal.bg,
            "relief": tk.FLAT,
            "borderwidth": 0,
            "takefocus": self._kwargs.get('takefocus', True)
        }

        self._tk_frame = tk.Frame(master_tk, **default_kwargs)
        self._tk_frame.config(
            bg=self._styles.normal.bg,
            highlightthickness=1,
            highlightbackground=self._styles.normal.border,
            highlightcolor=self._styles.focus.border,
            relief=tk.FLAT,
            borderwidth=0
        )

        self.canvas = tk.Canvas(
            self._tk_frame,
            bg=self._styles.normal.bg,
            highlightthickness=0,
            yscrollincrement=self.get_item_height()
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._bind_events()
        self._register_listeners()
        
        return self._tk_frame

    def _bind_events(self):
        self._internal_bind_ids.append((self._tk_frame, '<Configure>', self._tk_frame.bind('<Configure>', self._on_configure_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<FocusIn>', self._tk_frame.bind('<FocusIn>', self._on_focus_in_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<FocusOut>', self._tk_frame.bind('<FocusOut>', self._on_focus_out_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<KeyPress>', self._tk_frame.bind('<KeyPress>', self._on_key_press_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<Enter>', self._tk_frame.bind('<Enter>', self._on_enter_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<Leave>', self._tk_frame.bind('<Leave>', self._on_leave_internal, add='+')))

        self._internal_bind_ids.append((self.canvas, '<Configure>', self.canvas.bind('<Configure>', self._on_canvas_configure, add='+')))
        self._internal_bind_ids.extend(PlatformInputBind.bind_mousewheel(self.canvas, self._on_mouse_wheel))

    def _update_viewport(self, *args):
        if not self.canvas.winfo_exists():
            return

        canvas_h = self.canvas.winfo_height()
        canvas_w = self.canvas.winfo_width()

        if canvas_h <= 1:
            canvas_h = 200

        total_h = len(self._items) * self.get_item_height()
        self.canvas.config(scrollregion=(0, 0, canvas_w, max(canvas_h, total_h)))

        top_y = self.canvas.canvasy(0)
        if top_y < 0:
            top_y = 0

        start_index = int(top_y // self.get_item_height())
        visible_count = math.ceil(canvas_h / self.get_item_height()) + 2

        while len(self._item_pool) < visible_count:
            btn = self._create_item_button(-1, LocalizedText(""))
            win_id = self.canvas.create_window(0, -1000, window=btn._tk_label, anchor='nw')
            self._item_pool.append(btn)
            self._pool_windows.append(win_id)

        for i in range(len(self._item_pool)):
            btn = self._item_pool[i]
            win_id = self._pool_windows[i]
            data_idx = start_index + i

            if data_idx < len(self._items):
                btn._index = data_idx
                btn.set_text(self._items[data_idx])

                btn.set_selected(data_idx == self._selected_index)
                btn._hovered = (data_idx == self._hover_index)
                btn._apply_style()

                y_pos = data_idx * self.get_item_height()
                self.canvas.coords(win_id, 0, y_pos)
                self.canvas.itemconfig(win_id, width=canvas_w)
                self.canvas.itemconfig(win_id, state='normal')
            else:
                self.canvas.itemconfig(win_id, state='hidden')
                btn._index = -1

    def _create_item_button(self, index, text):
        btn = ListBoxItem(
            self.canvas,
            text=text,
            index=index,
            anchor='w',
            justify='left',
            padx=4,
            pady=self._item_pady
        )
        btn.on_click.add_listener(lambda b=btn: self._on_item_btn_click(b))
        btn.on_press.add_listener(lambda b=btn: self._on_item_btn_press(b))
        btn.on_scroll.add_listener(lambda delta: self.scroll_by(delta))
        btn.on_enter.add_listener(lambda b=btn: self._on_item_enter(b))
        return btn

    def _on_item_btn_press(self, btn):
        if not self._disabled:
            self._tk_frame.focus_set()

    def _on_item_enter(self, btn):
        if not self._disabled and btn._index >= 0:
            self._update_hover(btn._index)

    def _on_configure_internal(self, event):
        self._hover_index = -1
        self.on_configure.broadcast(event)

    def _on_canvas_configure(self, event):
        self._hover_index = -1
        self._update_viewport()
        self._trigger_scroll_event()

    def _on_mouse_wheel(self, event, delta):
        if self._disabled:
            return
        self.scroll_by(-1 * delta)

    def scroll_by(self, delta):
        total_h = len(self._items) * self.get_item_height()
        if total_h <= self.canvas.winfo_height():
            return

        self.canvas.yview_scroll(delta, 'units')
        self._update_viewport()
        self._trigger_scroll_event()

    def set_scroll_position(self, fraction):
        self.canvas.yview_moveto(fraction)
        self._update_viewport()
        self._trigger_scroll_event()

    def _trigger_scroll_event(self):
        scroll_pos = self.canvas.yview()[0]
        self.on_scroll.broadcast(scroll_pos)

    def _register_listeners(self):
        self.styles.on_theme_changed.add_listener(self._on_theme_changed_internal)
        self.localization.on_language_changed.add_listener(self._on_language_changed_internal)

    def _unregister_listeners(self):
        self.styles.on_theme_changed.remove_listener(self._on_theme_changed_internal)
        self.localization.on_language_changed.remove_listener(self._on_language_changed_internal)

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
        listbox_style = current_style.component.listbox

        class ListBoxStyles:
            def __init__(self):
                self.normal = type('Style', (), {
                    'bg': listbox_style.normal.bg.color,
                    'fg': listbox_style.normal.fg.color,
                    'border': listbox_style.normal.border.color
                })()
                self.focus = type('Style', (), {
                    'bg': listbox_style.focus.bg.color,
                    'fg': listbox_style.focus.fg.color,
                    'border': listbox_style.focus.border.color
                })()
                self.disable = type('Style', (), {
                    'bg': listbox_style.disable.bg.color,
                    'fg': listbox_style.disable.fg.color,
                    'border': listbox_style.disable.border.color
                })()

        self._styles = ListBoxStyles()

    def _on_theme_changed_internal(self, theme):
        self._config_styles()
        self.refresh()

    def _on_language_changed_internal(self, language):
        self._update_viewport()

    def _on_focus_in_internal(self, event):
        if not self._disabled:
            self._tk_frame.config(highlightcolor=self._styles.focus.border)
            if len(self._items) > 0 and self._hover_index < 0:
                if self._selected_index >= 0:
                    self._update_hover(self._selected_index)
                else:
                    self._update_hover(0)
            self.on_focus_in.broadcast()

    def _on_focus_out_internal(self, event):
        if not self._disabled:
            self._tk_frame.config(highlightbackground=self._styles.normal.border)
            self.on_focus_out.broadcast()

    def _on_enter_internal(self, event):
        pass

    def _on_leave_internal(self, event):
        pass

    def _on_key_press_internal(self, event):
        if self._disabled:
            return
        if event.keysym == 'Up':
            self._move_selection(-1)
        elif event.keysym == 'Down':
            self._move_selection(1)
        elif event.keysym in ('Return', 'space'):
            self._activate_selection()
        elif event.keysym == 'Home':
            self._move_to_first()
        elif event.keysym == 'End':
            self._move_to_last()

    def _update_hover(self, index):
        self._hover_index = index
        self._refresh_pool_states()

    def _refresh_pool_states(self):
        for btn in self._item_pool:
            if 0 <= btn._index < len(self._items):
                btn._hovered = (btn._index == self._hover_index)
                btn._selected = (btn._index == self._selected_index)
                btn._apply_style()

    def insert(self, index, text):
        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")
        if index == tk.END or index > len(self._items):
            index = len(self._items)
        self._items.insert(index, text)

        self._selected_index = -1
        self._hover_index = -1

        self._update_viewport()
        self._trigger_scroll_event()
        
        if self.canvas.winfo_exists():
            self.canvas.update_idletasks()
            self._update_viewport()

    def delete(self, index):
        if 0 <= index < len(self._items):
            self._items.pop(index)

            self._selected_index = -1
            self._hover_index = -1

            self._update_viewport()
            self._trigger_scroll_event()

    def delete_all(self):
        self._items.clear()
        self._selected_index = -1
        self._hover_index = -1
        self._update_viewport()
        self._trigger_scroll_event()

    def refresh(self):
        self._config_styles()
        self._tk_frame.config(
            bg=self._styles.normal.bg,
            highlightbackground=self._styles.normal.border,
            highlightcolor=self._styles.focus.border
        )
        self.canvas.config(bg=self._styles.normal.bg)

        self.canvas.config(yscrollincrement=self.get_item_height())

        for btn in self._item_pool:
            btn.refresh_theme()

        self._update_viewport()

    def _on_item_btn_click(self, btn):
        self._on_item_click(btn._index)

    def _on_item_click(self, index):
        if not self._disabled:
            self._update_hover(index)
            self._select_item(index)

    def _select_item(self, index):
        if 0 <= index < len(self._items):
            self._selected_index = index
            self._refresh_pool_states()
            self.on_select.broadcast(index, self._items[index])

    def _select_item_without_notify(self, index):
        if 0 <= index < len(self._items):
            self._selected_index = index
            self._refresh_pool_states()

    def _activate_selection(self):
        if self._hover_index >= 0:
            self._on_item_click(self._hover_index)

    def _move_to_first(self):
        if self._items:
            self._update_hover(0)
            self._ensure_visible(0)

    def _move_to_last(self):
        if self._items:
            self._update_hover(len(self._items) - 1)
            self._ensure_visible(len(self._items) - 1)

    def _move_selection(self, delta):
        if len(self._items) == 0:
            return
        new_index = self._hover_index
        if new_index < 0:
            new_index = 0 if delta > 0 else len(self._items) - 1
        else:
            new_index += delta

        new_index = max(0, min(len(self._items) - 1, new_index))
        self._update_hover(new_index)
        self._ensure_visible(new_index)

    def _ensure_visible(self, index):
        if index < 0 or index >= len(self._items):
            return

        top_y = self.canvas.canvasy(0)
        canvas_h = self.canvas.winfo_height()
        bottom_y = top_y + canvas_h

        item_top = index * self.get_item_height()
        item_bottom = item_top + self.get_item_height()
        total_h = len(self._items) * self.get_item_height()

        needs_update = False
        if item_top < top_y:
            fraction = item_top / total_h
            self.canvas.yview_moveto(fraction)
            needs_update = True
        elif item_bottom > bottom_y:
            fraction = (item_bottom - canvas_h) / total_h
            self.canvas.yview_moveto(fraction)
            needs_update = True

        if needs_update:
            self._update_viewport()
            self._trigger_scroll_event()

    def get(self, index):
        return self._items[index]

    def curselection(self):
        return (self._selected_index,) if self._selected_index >= 0 else ()

    def selection_clear(self):
        self._selected_index = -1
        self._refresh_pool_states()

    def select(self, index, scroll_to=True):
        if index < 0 or index >= len(self._items):
            return
        self._hover_index = -1
        self._select_item(index)
        if scroll_to:
            self._ensure_visible(index)

    def select_without_notify(self, index, scroll_to=True):
        if index < 0 or index >= len(self._items):
            return
        self._hover_index = -1
        self._select_item_without_notify(index)
        if scroll_to:
            self._ensure_visible(index)

    def size(self):
        return len(self._items)

    def scroll_to_top(self):
        self.canvas.yview_moveto(0)
        self._update_viewport()
        self._trigger_scroll_event()

    def scroll_to_index(self, index):
        if 0 <= index < len(self._items):
            self._ensure_visible(index)

    def set_disabled(self, disabled):
        self._disabled = disabled
        for btn in self._item_pool:
            btn.set_disabled(disabled)

        if disabled:
            # 禁用时不允许获取焦点
            self._tk_frame.config(takefocus=False)
            # 如果当前有焦点，让出焦点到下一个组件
            if self._tk_frame.focus_get() == self._tk_frame:
                try:
                    self._tk_frame.tk_focusNext().focus_set()
                except Exception:
                    pass
        else:
            # 恢复允许获取焦点
            self._tk_frame.config(takefocus=True)

    def is_disabled(self):
        return self._disabled

    def get_item_height(self):
        font = self.styles.get_style().font.normal
        font_obj = tkfont.Font(font=font)
        return font_obj.metrics("linespace") + self._item_pady * 2

    def focus_set(self):
        self._tk_frame.focus_set()
