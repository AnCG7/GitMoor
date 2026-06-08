import tkinter as tk

from enum import Enum

from ..core.view import View

from ..core.manager.ui_style_manager import UIStyleManager, StyleObject

from ..core.manager.event_manager import Event

from ..core.manager.localization_manager import LocalizedText

from .listbox import ListBox

from .scrollbar import Scrollbar, Orientation



class ScrollbarMode(Enum):

    Auto = "auto"

    Always = "always"

    Never = "never"



class ScrollListbox(View):

    def __init__(self, master=None, scrollbar_mode=ScrollbarMode.Auto, **kwargs):

        self._kwargs = kwargs

        self._disabled = False

        self._scrollbar_mode = scrollbar_mode

        self._scrollbar_visible = None

        self._mouse_inside = False

        self._block_tab = False

        self._tk_frame = None

        self._styles = None


        self._internal_bind_ids = []

        self.styles = UIStyleManager.get_instance()

        self.on_select = Event()

        self.on_configure = Event()

        self.on_tab_block = Event()

        self.on_focus_in = Event()

        self.on_focus_out = Event()


        super().__init__(master, **kwargs)


    def _build_widget(self, master=None, **kwargs):

        master_tk = self._get_master_tk()


        self._config_styles()


        default_kwargs = {

            "bg": self._styles.normal.bg,

            "highlightthickness": 1,

            "highlightbackground": self._styles.normal.border,

            "highlightcolor": self._styles.focus.border,

            "relief": tk.FLAT,

            "borderwidth": 0,

            "takefocus": True

        }


        frame_kwargs = {k: kwargs.get(k, default_kwargs[k]) for k in default_kwargs}

        self._tk_frame = tk.Frame(master_tk, **frame_kwargs)


        self._create_widgets()

        self._bind_events()

        self._register_listeners()


        return self._tk_frame


    def _config_styles(self):

        current_style = self.styles.get_style()

        listbox_style = current_style.component.listbox


        self_styles_dict = {

            'normal': {

                'bg': listbox_style.normal.bg.color,

                'border': listbox_style.normal.border.color

            },

            'focus': {

                'border': listbox_style.focus.border.color

            },

            'disable': {

                'border': listbox_style.disable.border.color

            }

        }

        self._styles = StyleObject(self_styles_dict)


    def _create_widgets(self):

        self.listbox = ListBox(self._tk_frame)

        self.scrollbar = Scrollbar(self._tk_frame, orientation=Orientation.Vertical)


        self._hack_internal_components()


        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


        self.listbox.on_select.add_listener(lambda index, item: self.on_select.broadcast(index, item))


    def _hack_internal_components(self):

        self.listbox.config(takefocus=0)

        self.scrollbar.config(takefocus=0)

        self.listbox.config(highlightthickness=0, borderwidth=0)


    def _bind_events(self):

        self._internal_bind_ids.append((self._tk_frame, '<FocusIn>', self._tk_frame.bind('<FocusIn>', self._on_focus_in_internal, add='+')))

        self._internal_bind_ids.append((self._tk_frame, '<FocusOut>', self._tk_frame.bind('<FocusOut>', self._on_focus_out_internal, add='+')))

        self._internal_bind_ids.append((self._tk_frame, '<KeyPress>', self._tk_frame.bind('<KeyPress>', self._on_key_press_internal, add='+')))

        self._internal_bind_ids.append((self._tk_frame, '<ButtonPress-1>', self._tk_frame.bind('<ButtonPress-1>', self._on_press_internal, add='+')))

        self._internal_bind_ids.append((self._tk_frame, '<Button-1>', self._tk_frame.bind('<Button-1>', self._on_click_internal, add='+')))

        self._internal_bind_ids.append((self._tk_frame, '<Enter>', self._tk_frame.bind('<Enter>', self._on_mouse_enter, add='+')))

        self._internal_bind_ids.append((self._tk_frame, '<Leave>', self._tk_frame.bind('<Leave>', self._on_mouse_leave, add='+')))

        self._internal_bind_ids.append((self._tk_frame, '<MouseWheel>', self._tk_frame.bind('<MouseWheel>', self._on_mouse_wheel, add='+')))

        self._internal_bind_ids.append((self._tk_frame, '<Tab>', self._tk_frame.bind('<Tab>', self._on_tab_internal, add='+')))

        self._internal_bind_ids.append((self._tk_frame, '<Shift-Tab>', self._tk_frame.bind('<Shift-Tab>', self._on_shift_tab_internal, add='+')))


        self._add_parent_to_bindtags(self.listbox._tk_frame)

        self._add_parent_to_bindtags(self.listbox.canvas)

        self._add_parent_to_bindtags(self.scrollbar._tk_canvas)


        self.listbox.on_scroll.add_listener(self._update_scrollbar_state)

        self.scrollbar.on_scroll.add_listener(self._sync_listbox_view)


    def _add_parent_to_bindtags(self, widget):

        try:

            current_tags = widget.bindtags()

            if self._tk_frame not in current_tags:

                new_tags = list(current_tags)

                new_tags.insert(1, self._tk_frame)

                widget.bindtags(tuple(new_tags))

        except Exception:

            pass


    def _on_focus_in_internal(self, event):

        if not self._disabled:

            self._tk_frame.config(highlightcolor=self._styles.focus.border)

            self.listbox._on_focus_in_internal(event)

            self.on_focus_in.broadcast(event)


    def _on_focus_out_internal(self, event):

        if not self._disabled:

            self._tk_frame.config(highlightbackground=self._styles.normal.border)

            self.listbox._on_focus_out_internal(event)

            self.on_focus_out.broadcast(event)


    def _on_key_press_internal(self, event):

        self.listbox._on_key_press_internal(event)


    def _on_press_internal(self, event):

        if not self._disabled:

            self.focus_set()


    def _on_click_internal(self, event):

        pass


    def _on_tab_internal(self, event):

        self.on_tab_block.broadcast('tab')

        if self._block_tab:

            return 'break'


    def _on_shift_tab_internal(self, event):

        self.on_tab_block.broadcast('shift_tab')

        if self._block_tab:

            return 'break'


    def _on_mouse_enter(self, event):

        self._mouse_inside = True


    def _on_mouse_leave(self, event):

        self._mouse_inside = False


    def _on_mouse_wheel(self, event):

        if self._disabled or not self._mouse_inside:

            return


        if not hasattr(self, 'listbox') or not hasattr(self.listbox, 'canvas'):

            return


        if self.listbox.size() == 0:

            return


        yview = self.listbox.canvas.yview()

        if len(yview) != 2:

            return


        content_exceeds = not (yview[0] <= 0.001 and yview[1] >= 0.999)

        if not content_exceeds:

            return


        self.focus_set()

        self.listbox.scroll_by(-1 if event.delta > 0 else 1)

        return 'break'


    def set_scrollbar_mode(self, mode: ScrollbarMode):

        if not isinstance(mode, ScrollbarMode):

            raise TypeError("mode 参数必须是 ScrollbarMode 枚举类型")

        self._scrollbar_mode = mode

        self._update_scrollbar_state()


    def _update_scrollbar_state(self, *args):

        if not hasattr(self, 'listbox') or not hasattr(self.listbox, 'canvas'):

            return


        if self.listbox.size() == 0:

            yview = (0.0, 1.0)

        else:

            yview = self.listbox.canvas.yview()


        if len(yview) != 2:

            return


        content_exceeds = not (yview[0] <= 0.001 and yview[1] >= 0.999)


        needs_show = False

        if self._scrollbar_mode == ScrollbarMode.Always:

            needs_show = True

        elif self._scrollbar_mode == ScrollbarMode.Never:

            needs_show = False

        elif self._scrollbar_mode == ScrollbarMode.Auto:

            needs_show = content_exceeds


        if needs_show and self._scrollbar_visible is not True:

            self.listbox.pack_forget()

            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            self._scrollbar_visible = True


        elif not needs_show and self._scrollbar_visible is not False:

            if self._scrollbar_visible is True:

                self.scrollbar.pack_forget()

            else:

                self.listbox.pack_forget()

                self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            self._scrollbar_visible = False

        self.scrollbar.set_position(yview[0], yview[1])


    def _sync_listbox_view(self, fraction):

        self.listbox.set_scroll_position(fraction)


    def _register_listeners(self):

        self.styles.on_theme_changed.add_listener(self._on_theme_changed_internal)


    def _unregister_listeners(self):

        self.styles.on_theme_changed.remove_listener(self._on_theme_changed_internal)


    def _unbind_internal_events(self):

        for widget, sequence, funcid in self._internal_bind_ids:

            try:

                widget.unbind(sequence, funcid)

            except:

                pass
        self._internal_bind_ids.clear()


    def _on_theme_changed_internal(self, theme):

        self._config_styles()

        self.refresh()


    def refresh(self):

        self._config_styles()

        self._tk_frame.config(

            bg=self._styles.normal.bg,

            highlightbackground=self._styles.normal.border,

            highlightcolor=self._styles.focus.border
        )

        self.listbox.refresh()

        self.scrollbar.refresh()


    def _on_destroy(self):

        self._unregister_listeners()

        self._unbind_internal_events()

        self.listbox.destroy()

        self.scrollbar.destroy()

        super()._on_destroy()


    def insert(self, index, text):

        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")

        self.listbox.insert(index, text)


    def delete(self, index):

        self.listbox.delete(index)

        if self.listbox.size() == 0:

            self._update_scrollbar_state()


    def get(self, index):

        return self.listbox.get(index)


    def curselection(self):

        return self.listbox.curselection()


    def selection_clear(self):

        self.listbox.selection_clear()


    def select(self, index, scroll_to=True):

        self.listbox.select(index, scroll_to=scroll_to)


    def select_without_notify(self, index, scroll_to=True):

        self.listbox.select_without_notify(index, scroll_to=scroll_to)


    def size(self):

        return self.listbox.size()


    def scroll_to_top(self):

        self.listbox.scroll_to_top()


    def scroll_to_index(self, index):

        self.listbox.scroll_to_index(index)


    def delete_all(self):

        self.listbox.delete_all()

        self._update_scrollbar_state()


    def set_disabled(self, disabled):

        self._disabled = disabled

        self.listbox.set_disabled(disabled)
        self.scrollbar.set_disabled(disabled)


    def set_block_tab(self, block):

        self._block_tab = block


    def is_disabled(self):

        return self._disabled


    def get_item_height(self):

        return self.listbox.get_item_height()


    def focus_set(self):

        self._tk_frame.focus_set()



