import tkinter as tk
from enum import Enum, auto
from ..core.view import View
from ..core.manager.ui_style_manager import UIStyleManager, StyleObject
from ..core.manager.event_manager import Event
from ..core.manager.localization_manager import LocalizedText, LocalizationManager
from ..core.utils.utils import Utils
from ..core.utils.asset_loader import AssetLoader
from .entry import Entry, EntryMode
from .scroll_listbox import ScrollListbox


class ComponentState(Enum):
    Normal = auto()
    Hover = auto()
    Press = auto()
    Focus = auto()
    Disable = auto()

    @classmethod
    def from_string(cls, state_str):
        state_map = {
            'normal': cls.Normal,
            'hover': cls.Hover,
            'press': cls.Press,
            'focus': cls.Focus,
            'disabled': cls.Disable
        }
        return state_map.get(state_str.lower(), cls.Normal)

    def to_string(self):
        state_map = {
            self.Normal: 'normal',
            self.Hover: 'hover',
            self.Press: 'press',
            self.Focus: 'focus',
            self.Disable: 'disabled'
        }
        return state_map[self]


class Combobox(View):
    MAX_VISIBLE_ITEMS = 8

    def __init__(self, master=None, max_visible_items=None, **kwargs):
        self.styles = UIStyleManager.get_instance()
        self.lm = LocalizationManager.get_instance()
        
        default_kwargs = {
            "bg": self.styles.get_style().component.frame.bg.color,
            "takefocus": True
        }
        default_kwargs.update(kwargs)

        self._max_visible_items = max_visible_items or self.MAX_VISIBLE_ITEMS
        self._kwargs = default_kwargs

        self._tk_frame = None
        self.entry = None
        self.arrow_button = None
        self._listbox_container = None
        self.listbox = None

        self.options = []
        self.current_value = ""
        self._current_index = -1
        self._listbox_visible = False
        self._current_state = 'normal'
        self._disabled = False
        self._updating_state = False

        self._mouse_pressed = False
        self._mouse_moved = False
        self._click_start_x = 0
        self._click_start_y = 0

        self._arrow_images = {}
        self._arrow_image = None

        # 事件定义
        self.on_map = Event()
        self.on_unmap = Event()
        self.on_configure = Event()
        self.on_click = Event()
        self.on_enter = Event()
        self.on_leave = Event()
        self.on_press = Event()
        self.on_release = Event()
        self.on_key_press = Event()
        self.on_focus_in = Event()
        self.on_focus_out = Event()
        self.on_double_click = Event()
        self.on_triple_click = Event()
        self.on_motion = Event()
        self.on_select = Event()
        self.on_open = Event()
        self.on_close = Event()

        # 绑定ID
        self._internal_bind_ids = []
        self._click_outside_id = None
        self._configure_id = None
        self._escape_id = None

        self._config_styles()
        self._preload_images()
        self._arrow_image = self._arrow_images.get('normal', None)

        super().__init__(master, **kwargs)

    def _build_widget(self, master=None, **kwargs):
        master_tk = self._get_master_tk()
        
        frame_kwargs = self._kwargs.copy()
        frame_kwargs.pop('state', None)
        self._tk_frame = tk.Frame(master_tk, **frame_kwargs)
        self._tk_frame.grid_columnconfigure(0, weight=1)

        self._tk_frame.config(
            highlightthickness=1,
            highlightbackground=self._styles.normal.border,
            highlightcolor=self._styles.normal.border,
            bg=self._styles.normal.bg,
            takefocus=1
        )

        self.entry = Entry(
            self._tk_frame,
            bg=self._styles.normal.bg,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            takefocus=0
        )
        self.entry.set_mode(EntryMode.Readonly)
        self.entry.set_state_config_override(EntryMode.Readonly, {'takefocus': 0, 'cursor': 'hand2'})
        self.entry._tk_entry.config(width=1)
        self.entry._tk_frame.grid(row=0, column=0, sticky='ew')

        self.arrow_button = tk.Label(
            self._tk_frame,
            image=self._arrow_image,
            bg=self._styles.normal.bg,
            relief=tk.FLAT,
            borderwidth=0,
            takefocus=0,
            cursor='arrow',
            width=16,
            height=16,
            anchor='center'
        )
        self.arrow_button.grid(row=0, column=1, sticky='ns', padx=2, pady=2)
        self.arrow_button.image = self._arrow_image

        self.top_level = self._tk_frame.winfo_toplevel()
        self._listbox_container = tk.Frame(self.top_level)
        self._listbox_container.config(
            bg=self._styles.normal.bg,
            highlightthickness=0,
            highlightbackground=self._styles.normal.border,
            relief=tk.FLAT
        )

        self.listbox = ScrollListbox(self._listbox_container)
        self.listbox.pack(fill=tk.BOTH, expand=True)

        self._internal_bind_ids.append((self._tk_frame, '<Map>', self._tk_frame.bind('<Map>', self._on_map_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<Unmap>', self._tk_frame.bind('<Unmap>', self._on_unmap_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<Configure>', self._tk_frame.bind('<Configure>', self._on_configure_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<Enter>', self._tk_frame.bind('<Enter>', self._on_enter_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<Leave>', self._tk_frame.bind('<Leave>', self._on_leave_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<ButtonPress-1>', self._tk_frame.bind('<ButtonPress-1>', self._on_press_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<ButtonRelease-1>', self._tk_frame.bind('<ButtonRelease-1>', self._on_release_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<KeyPress>', self._tk_frame.bind('<KeyPress>', self._on_key_press_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<FocusIn>', self._tk_frame.bind('<FocusIn>', self._on_focus_in_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<FocusOut>', self._tk_frame.bind('<FocusOut>', self._on_focus_out_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<Double-Button-1>', self._tk_frame.bind('<Double-Button-1>', self._on_double_click_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<Triple-Button-1>', self._tk_frame.bind('<Triple-Button-1>', self._on_triple_click_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<Motion>', self._tk_frame.bind('<Motion>', self._on_motion_internal, add='+')))

        self._setup_events()
        self._register_listeners()
        
        return self._tk_frame

    def _setup_events(self):
        self._internal_bind_ids.append((self.arrow_button, '<Enter>', self.arrow_button.bind('<Enter>', self._on_arrow_enter_internal, add='+')))
        self._internal_bind_ids.append((self.arrow_button, '<Leave>', self.arrow_button.bind('<Leave>', self._on_arrow_leave_internal, add='+')))
        self._internal_bind_ids.append((self.arrow_button, '<ButtonPress-1>', self.arrow_button.bind('<ButtonPress-1>', self._on_arrow_press_internal, add='+')))
        self._internal_bind_ids.append((self.arrow_button, '<ButtonRelease-1>', self.arrow_button.bind('<ButtonRelease-1>', self._on_arrow_release_internal, add='+')))

        self.listbox.on_select.add_listener(self._on_listbox_select_internal)
        self.listbox.on_tab_block.add_listener(self._on_listbox_tab_block_internal)

        self.entry.on_enter.add_listener(self._on_enter_internal)
        self.entry.on_leave.add_listener(self._on_leave_internal)
        self.entry.on_focus_in.add_listener(self._on_focus_in_internal)
        self.entry.on_focus_out.add_listener(self._on_focus_out_internal)

        self.entry.on_press.add_listener(self._on_entry_press_internal)
        self.entry.on_release.add_listener(self._on_entry_release_internal)
        self.entry.on_motion.add_listener(self._on_entry_motion_internal)

        self.entry.on_double_click.add_listener(self._on_entry_double_click_internal)
        self.entry.on_triple_click.add_listener(self._on_entry_triple_click_internal)

    def _register_listeners(self):
        self.styles.on_theme_changed.add_listener(self._on_theme_changed_internal)
        self.lm.on_language_changed.add_listener(self._on_language_changed_internal)

    def _unregister_listeners(self):
        try:
            self.styles.on_theme_changed.remove_listener(self._on_theme_changed_internal)
        except:
            pass
        try:
            self.lm.on_language_changed.remove_listener(self._on_language_changed_internal)
        except:
            pass
        try:
            if self._click_outside_id:
                self.top_level.unbind_all("<Button-1>", self._click_outside_id)
                self._click_outside_id = None
            if hasattr(self, '_configure_id') and self._configure_id:
                self.top_level.unbind("<Configure>", self._configure_id)
                self._configure_id = None
            if self._escape_id:
                self.top_level.unbind_all("<Key-Escape>", self._escape_id)
                self._escape_id = None
        except:
            pass

    def _on_theme_changed_internal(self, theme):
        self._config_styles()
        self._load_images()
        self.refresh()
    
    def _on_language_changed_internal(self, language):
        if 0 <= self._current_index < len(self.options):
            self.set_text(self.options[self._current_index])

    def _preload_images(self):
        arrow_path = AssetLoader.get_theme_image_path("combobox_arrow.png")
        if arrow_path:
            normal_style = self._styles.normal
            img = tk.PhotoImage(file=arrow_path)
            Utils.recolor_image(img, normal_style.bg, normal_style.arrow)
            self._arrow_images['normal'] = img

            hover_style = self._styles.hover
            img = tk.PhotoImage(file=arrow_path)
            Utils.recolor_image(img, hover_style.bg, hover_style.arrow)
            self._arrow_images['hover'] = img

            self._arrow_images['focus'] = self._arrow_images['hover']

            press_style = self._styles.press
            img = tk.PhotoImage(file=arrow_path)
            Utils.recolor_image(img, press_style.bg, press_style.arrow)
            self._arrow_images['press'] = img

            disabled_style = self._styles.disabled
            img = tk.PhotoImage(file=arrow_path)
            Utils.recolor_image(img, disabled_style.bg, disabled_style.arrow)
            self._arrow_images['disabled'] = img

    def _load_images(self):
        self._preload_images()
        self._arrow_image = self._arrow_images.get(self._current_state, None)

    def _update_state(self, state):
        if self._updating_state:
            return
        
        if isinstance(state, ComponentState):
            state_str = state.to_string()
        else:
            state_str = state
            state = ComponentState.from_string(state)

        if self._current_state == 'focus' and state_str == 'focus':
            return
        
        self._updating_state = True
        try:
            self._current_state = state_str
            self._apply_state()
        finally:
            self._updating_state = False

    def _apply_state(self):
        style = getattr(self._styles, self._current_state)
        cursor = 'no' if self._current_state == 'disabled' else 'hand2'
        self._tk_frame.config(
            highlightbackground=style.border,
            highlightcolor=style.border,
            bg=style.bg,
            cursor=cursor
        )
        self.entry._styles.normal.bg = style.bg
        self.entry.refresh()
        
        self._arrow_image = self._arrow_images.get(self._current_state, None)
        
        if self._arrow_image:
            self.arrow_button.config(bg=style.bg, image=self._arrow_image, cursor=cursor)
            self.arrow_button.image = self._arrow_image
        else:
            self.arrow_button.config(bg=style.bg, cursor=cursor)

    def _on_enter_internal(self, event=None):
        if self._disabled:
            return
        if self._listbox_visible:
            return
        if self._current_state != 'focus':
            self._update_state('hover')

    def _on_leave_internal(self, event=None):
        if self._disabled:
            return
        if self._listbox_visible:
            return
        if self._current_state != 'focus':
            self._update_state('normal')

    def _on_press_internal(self, event=None):
        if self._disabled:
            return
        self._update_state('press')

    def _on_release_internal(self, event=None):
        if self._disabled:
            return

        self.toggle_listbox()
        
        if self.entry._tk_entry.focus_get() == self.entry._tk_entry:
            self._update_state('focus')
        else:
            self._update_state('hover')

    def _on_focus_in_internal(self, event=None):
        if self._disabled:
            return
        if self._current_state != 'press':
            self._update_state('focus')

    def _on_focus_out_internal(self, event=None):
        if self._disabled:
            return
        if self._current_state == 'focus':
            self._update_state('normal')


    def _on_entry_press_internal(self, event=None):
        if self._disabled:
            return
        self._mouse_pressed = True
        self._mouse_moved = False
        if event:
            self._click_start_x = event.x
            self._click_start_y = event.y

    def _on_entry_motion_internal(self, event):
        if self._mouse_pressed and not self._mouse_moved:
            if abs(event.x - self._click_start_x) > 2 or abs(event.y - self._click_start_y) > 2:
                self._mouse_moved = True

    def _on_entry_release_internal(self, event=None):
        if self._disabled:
            return
        if self._mouse_pressed:
            has_selection = False
            try:
                selected_text = self.entry._tk_entry.selection_get()
                has_selection = len(selected_text) > 0
            except:
                pass

            if not has_selection:
                self.toggle_listbox()
            self._mouse_pressed = False
            self._mouse_moved = False

    def _on_entry_double_click_internal(self, event=None):
        if self._disabled:
            return

    def _on_entry_triple_click_internal(self, event=None):
        if self._disabled:
            return

    def _on_key_press_internal(self, event):
        if self._disabled:
            return
        if event.keysym in ('Return', 'space'):
            self.toggle_listbox()
        elif event.keysym == 'Escape':
            if self._listbox_visible:
                self.hide_listbox()


    def _on_arrow_enter_internal(self, event):
        if self._disabled:
            return
        if self._current_state != 'focus':
            self._update_state('hover')

    def _on_arrow_leave_internal(self, event):
        if self._disabled:
            return
        if self._current_state != 'focus':
            self._update_state('normal')

    def _on_arrow_press_internal(self, event):
        if self._disabled:
            return
        self._update_state('press')

    def _on_arrow_release_internal(self, event):
        if self._disabled:
            return

        self.toggle_listbox()

        if self.entry._tk_entry.focus_get() == self.entry._tk_entry:
            self._update_state('focus')
        else:
            self._update_state('hover')

    def _on_listbox_select_internal(self, index, value):
        if self._disabled:
            return

        self._current_index = index
        self.set_text(value)
        self.hide_listbox()
        self.on_select.broadcast(index, value)

    def _on_listbox_focus_out_internal(self, event):
        if self._listbox_visible:
            self.listbox.focus_set()

    def _on_listbox_tab_block_internal(self, tab_type):
        pass

    def _on_escape_internal(self, event):
        if self._listbox_visible:
            self.hide_listbox()
            return 'break'

    def _on_click_outside_internal(self, event):
        if not self._listbox_visible:
            return

        clicked_widget = event.widget

        def is_descendant(widget, ancestor):
            while widget:
                if widget == ancestor:
                    return True
                widget = widget.master
            return False

        if is_descendant(clicked_widget, self._tk_frame):
            return
        if is_descendant(clicked_widget, self._listbox_container):
            return

        self.hide_listbox()

    def toggle_listbox(self):
        if self._disabled:
            return
        if self._listbox_visible:
            self.hide_listbox()
        else:
            self.show_listbox()

    def _update_listbox_position(self):
        if not self._listbox_visible:
            return

        self.top_level.update_idletasks()

        combobox_x = self._tk_frame.winfo_rootx() - self.top_level.winfo_rootx()
        combobox_y = self._tk_frame.winfo_rooty() - self.top_level.winfo_rooty()
        combobox_height = self._tk_frame.winfo_height()
        listbox_width = self._tk_frame.winfo_width()

        item_height = self.listbox.get_item_height()
        visible_count = min(self._max_visible_items, len(self.options))
        listbox_height = visible_count * item_height + 10

        window_width = self.top_level.winfo_width()
        window_height = self.top_level.winfo_height()

        space_below = window_height - (combobox_y + combobox_height)
        space_above = combobox_y

        if space_below >= listbox_height:
            listbox_y = combobox_y + combobox_height
        elif space_above >= listbox_height:
            listbox_y = combobox_y - listbox_height
        else:
            listbox_y = combobox_y + combobox_height

        self._listbox_container.place(
            x=combobox_x,
            y=listbox_y,
            width=listbox_width,
            height=listbox_height
        )

    def show_listbox(self):
        if self._disabled:
            return
        self._listbox_visible = True
        self._update_listbox_position()

        if 0 <= self._current_index < self.listbox.size():
            self.listbox.selection_clear()
            self.listbox.select_without_notify(self._current_index, scroll_to=True)

        self._listbox_container.lift()
        self.listbox.focus_set()
        self.listbox.set_block_tab(True)

        self.top_level.update_idletasks()
        self.listbox._update_scrollbar_state()

        self._click_outside_id = self.top_level.bind_all("<Button-1>", self._on_click_outside_internal, add='+')
        self._configure_id = self.top_level.bind("<Configure>", self._on_window_configure, add='+')
        self._escape_id = self.top_level.bind_all("<Key-Escape>", self._on_escape_internal, add='+')
        self.listbox.on_focus_out.add_listener(self._on_listbox_focus_out_internal)
        self.on_open.broadcast()

    def _on_window_configure(self, event):
        self._update_listbox_position()

    def hide_listbox(self):
        if self._disabled:
            return
        if not self._listbox_visible:
            return

        self._listbox_container.place_forget()
        self._listbox_visible = False
        self.listbox.set_block_tab(False)

        try:
            if self._click_outside_id:
                self.top_level.unbind_all("<Button-1>", self._click_outside_id)
                self._click_outside_id = None
            if hasattr(self, '_configure_id') and self._configure_id:
                self.top_level.unbind("<Configure>", self._configure_id)
                self._configure_id = None
            if self._escape_id:
                self.top_level.unbind_all("<Key-Escape>", self._escape_id)
                self._escape_id = None
        except:
            pass
        self.listbox.on_focus_out.remove_listener(self._on_listbox_focus_out_internal)
        self._tk_frame.focus_set()
        self.on_close.broadcast()

    def set_options(self, options):
        for option in options:
            if option is not None and not isinstance(option, LocalizedText):
                raise TypeError("options 中的每一项必须是 LocalizedText 类型")
        self.options = options
        self._current_index = -1
        self.current_value = ""
        self.entry.set_text(LocalizedText(""))
        self.listbox.delete_all()
        for option in options:
            self.listbox.insert(tk.END, option)
        # 默认选中第一个选项
        if options:
            self.set_selected_index(0, scroll_to=False)

    def get_options(self):
        return self.options

    def set_text(self, value):
        if value is not None and not isinstance(value, LocalizedText):
            raise TypeError("value 参数必须是 LocalizedText 类型")
        self.current_value = value
        self.entry.set_text(value)

    def get_value(self):
        return self.current_value

    def get_selected_index(self):
        return self._current_index

    def set_selected_index(self, index, scroll_to=True):
        if 0 <= index < len(self.options):
            self._current_index = index
            self._refresh_selected_index(self._current_index)

    def _refresh_selected_index(self, index, scroll_to=True):
        self.set_text(self.options[index])
        if(self._listbox_visible):
            self.listbox.selection_clear()
            self.listbox.select_without_notify(index, scroll_to=scroll_to)
        

    def set_state(self, state):
        if isinstance(state, ComponentState):
            self._update_state(state)
        else:
            raise ValueError("state 必须是 ComponentState 枚举值")

    def set_disabled(self, disabled):
        self._disabled = disabled
        if disabled:
            self._current_state = 'disabled'
            self.entry.set_disabled(True)
            self._tk_frame.config(takefocus=0)
        else:
            self._current_state = 'normal'
            self.entry.set_disabled(False)
            self._tk_frame.config(takefocus=1)
        self._apply_state()

    def is_disabled(self):
        return self._disabled

    def refresh(self):
        self._tk_frame.config(
            bg=self.styles.get_style().component.frame.bg.color
        )
        self._apply_state()
        self.entry.refresh()
        self.listbox.refresh()

    def _on_map_internal(self, event):
        self.on_map.broadcast()
    
    def _on_unmap_internal(self, event):
        self.on_unmap.broadcast()
    
    def _on_configure_internal(self, event):
        self.on_configure.broadcast(event)
    
    def _on_double_click_internal(self, event):
        self.on_double_click.broadcast(event)
    
    def _on_triple_click_internal(self, event):
        self.on_triple_click.broadcast(event)
    
    def _on_motion_internal(self, event):
        self.on_motion.broadcast(event)

    def _on_destroy(self):
        self._unregister_listeners()
        self._unbind_internal_events()
        self.hide_listbox()
        if self._arrow_image:
            self._arrow_image = None
        self.listbox.destroy()
        self.entry.destroy()
        if self._listbox_container:
            self._listbox_container.destroy()
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
        styles_dict = {
            'normal': {
                'border': current_style.component.combobox.normal.border.color,
                'bg': current_style.component.combobox.normal.bg.color,
                'fg': current_style.component.combobox.normal.fg.color,
                'arrow': current_style.component.combobox.normal.arrow.color
            },
            'hover': {
                'border': current_style.component.combobox.hover.border.color,
                'bg': current_style.component.combobox.hover.bg.color,
                'fg': current_style.component.combobox.hover.fg.color,
                'arrow': current_style.component.combobox.hover.arrow.color
            },
            'press': {
                'border': current_style.component.combobox.press.border.color,
                'bg': current_style.component.combobox.press.bg.color,
                'fg': current_style.component.combobox.press.fg.color,
                'arrow': current_style.component.combobox.press.arrow.color
            },
            'focus': {
                'border': current_style.component.combobox.focus.border.color,
                'bg': current_style.component.combobox.focus.bg.color,
                'fg': current_style.component.combobox.focus.fg.color,
                'arrow': current_style.component.combobox.focus.arrow.color
            },
            'disabled': {
                'border': current_style.component.combobox.disable.border.color,
                'bg': current_style.component.combobox.disable.bg.color,
                'fg': current_style.component.combobox.disable.fg.color,
                'arrow': current_style.component.combobox.disable.arrow.color
            }
        }
        self._styles = StyleObject(styles_dict)