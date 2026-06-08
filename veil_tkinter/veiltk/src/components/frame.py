import tkinter as tk
from ..core.view import View
from ..core.manager.ui_style_manager import UIStyleManager
from ..core.manager.event_manager import Event

class Frame(View):
    def __init__(self, master=None, **kwargs):
        self._kwargs = kwargs
        self._tk_frame = None
        self._styles = None
        self._internal_bind_ids = []

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
        
        super().__init__(master, **kwargs)

    def _build_widget(self, master=None, **kwargs):
        master_tk = self._get_master_tk()
            
        self.styles = UIStyleManager.get_instance()
        default_kwargs = {
            "bg": self.styles.get_style().component.frame.bg.color,
            "takefocus": False
        }
        default_kwargs.update(self._kwargs)

        self._tk_frame = tk.Frame(master_tk, **default_kwargs)

        self._internal_bind_ids.append((self._tk_frame, '<Map>', self._tk_frame.bind('<Map>', self._on_map_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<Unmap>', self._tk_frame.bind('<Unmap>', self._on_unmap_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<Configure>', self._tk_frame.bind('<Configure>', self._on_configure_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<Button-1>', self._tk_frame.bind('<Button-1>', self._on_click_internal, add='+')))
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
        
        self._register_listeners()
        
        return self._tk_frame

    def _register_listeners(self):
        self.styles.on_theme_changed.add_listener(self._on_theme_changed_internal)

    def _unregister_listeners(self):
        self.styles.on_theme_changed.remove_listener(self._on_theme_changed_internal)

    def _unbind_internal_events(self):
        for widget, sequence, funcid in self._internal_bind_ids:
            try:
                widget.unbind(sequence, funcid)
            except Exception:
                pass
        self._internal_bind_ids.clear()

    def _on_destroy(self):
        self._unregister_listeners()
        self._unbind_internal_events()
        super()._on_destroy()

    def _on_theme_changed_internal(self, theme):
        self.refresh_theme()

    def refresh_theme(self):
        bg_color = self.styles.get_style().component.frame.bg.color
        self._tk_frame.config(bg=bg_color)



    def _on_map_internal(self, event):
        self.on_map.broadcast()

    def _on_unmap_internal(self, event):
        self.on_unmap.broadcast()

    def _on_configure_internal(self, event):
        self.on_configure.broadcast(event)

    def _on_click_internal(self, event):
        self.on_click.broadcast(event)

    def _on_enter_internal(self, event):
        self.on_enter.broadcast(event)

    def _on_leave_internal(self, event):
        self.on_leave.broadcast(event)

    def _on_press_internal(self, event):
        self.on_press.broadcast(event)

    def _on_release_internal(self, event):
        self.on_release.broadcast(event)

    def _on_key_press_internal(self, event):
        self.on_key_press.broadcast(event)

    def _on_focus_in_internal(self, event):
        self.on_focus_in.broadcast(event)

    def _on_focus_out_internal(self, event):
        self.on_focus_out.broadcast(event)

    def _on_double_click_internal(self, event):
        self.on_double_click.broadcast(event)

    def _on_triple_click_internal(self, event):
        self.on_triple_click.broadcast(event)

    def _on_motion_internal(self, event):
        self.on_motion.broadcast(event)

    def bind(self, sequence=None, func=None, add=None):
        if func:
            self._tk_frame.bind(sequence, func, add)
        else:
            return self._tk_frame.bind(sequence)

