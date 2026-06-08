import tkinter as tk

from enum import Enum

from ..core.view import View

from ..core.manager.ui_style_manager import UIStyleManager, StyleObject

from ..core.manager.event_manager import Event



class Orientation(Enum):

    Vertical = "vertical"

    Horizontal = "horizontal"



class Scrollbar(View):

    def __init__(self, master=None, orientation=Orientation.Vertical, **kwargs):

        if not isinstance(orientation, Orientation):

            raise TypeError("orientation 参数必须是 Orientation 枚举类型")

        self._orientation = orientation

        self._kwargs = kwargs

        self._tk_canvas = None

        self._styles = None

        self._thumb = None

        self._disabled = False

        self._pressed = False

        self._hovered = False

        self._dragging = False

        self._start = 0.0

        self._end = 1.0

        self._internal_bind_ids = []


        self.on_configure = Event()

        self.on_scroll = Event()

        self.on_click = Event()
        

        super().__init__(master, **kwargs)


    def _build_widget(self, master=None, **kwargs):

        master_tk = self._get_master_tk()
            

        self.styles = UIStyleManager.get_instance()

        self._config_styles()


        if self._orientation == Orientation.Vertical:

            self._kwargs.setdefault("width", 10)

        else:

            self._kwargs.setdefault("height", 10)


        default_kwargs = {

            "highlightthickness": 0,

            "bg": self._styles['normal']['trough'],

            "relief": tk.FLAT,

            "borderwidth": 0

        }

        default_kwargs.update(self._kwargs)


        self._tk_canvas = tk.Canvas(master_tk, **default_kwargs)


        self._thumb = self._tk_canvas.create_rectangle(0, 0, 0, 0, outline="")


        self._internal_bind_ids.append((self._tk_canvas, "<Button-1>", self._tk_canvas.bind("<Button-1>", self._on_button_press, add='+')))

        self._internal_bind_ids.append((self._tk_canvas, "<B1-Motion>", self._tk_canvas.bind("<B1-Motion>", self._on_b1_motion, add='+')))

        self._internal_bind_ids.append((self._tk_canvas, "<ButtonRelease-1>", self._tk_canvas.bind("<ButtonRelease-1>", self._on_button_release, add='+')))

        self._internal_bind_ids.append((self._tk_canvas, "<Enter>", self._tk_canvas.bind("<Enter>", self._on_enter, add='+')))

        self._internal_bind_ids.append((self._tk_canvas, "<Leave>", self._tk_canvas.bind("<Leave>", self._on_leave, add='+')))

        self._internal_bind_ids.append((self._tk_canvas, "<Configure>", self._tk_canvas.bind("<Configure>", self._on_configure_internal, add='+')))

        self._register_listeners()
        self.set_position(0.0, 1.0)
        self._update_cursor()
        

        return self._tk_canvas


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

        styles_dict = {

            'normal': {

                'thumb': current_style.component.scrollbar.normal.thumb.color,

                'trough': current_style.component.scrollbar.normal.trough.color

            },

            'hover': {

                'thumb': current_style.component.scrollbar.hover.thumb.color

            },

            'press': {

                'thumb': current_style.component.scrollbar.press.thumb.color

            },

            'disable': {

                'thumb': current_style.component.scrollbar.disable.thumb.color

            }

        }

        self._styles = styles_dict


    def _register_listeners(self):

        self.styles.on_theme_changed.add_listener(self._on_theme_changed)


    def _unregister_listeners(self):

        self.styles.on_theme_changed.remove_listener(self._on_theme_changed)


    def _on_theme_changed(self, theme):

        self._config_styles()

        self.refresh_theme()


    def _on_configure_internal(self, event):
        self.set_position(self._start, self._end)

        self.on_configure.broadcast(event)


    def _on_button_press(self, event):

        if self._disabled:
            return

        self.on_click.broadcast(event)

        w, h = self._tk_canvas.winfo_width(), self._tk_canvas.winfo_height()

        x1, y1, x2, y2 = self._tk_canvas.coords(self._thumb)


        self._pressed = True


        if event.x >= x1 and event.x <= x2 and event.y >= y1 and event.y <= y2:

            self._dragging = True

            self._drag_offset_x = event.x - x1

            self._drag_offset_y = event.y - y1

        else:

            self._scroll_to(event.x, event.y)

            new_x1, new_y1, new_x2, new_y2 = self._tk_canvas.coords(self._thumb)

            self._dragging = True

            self._drag_offset_x = event.x - new_x1

            self._drag_offset_y = event.y - new_y1


        self._update_thumb_color()


    def _on_b1_motion(self, event):

        if self._disabled or not self._dragging:
            return


        adjusted_x = event.x - self._drag_offset_x

        adjusted_y = event.y - self._drag_offset_y

        self._scroll_to(adjusted_x, adjusted_y)


    def _on_button_release(self, event):

        self._pressed = False

        self._dragging = False

        self._update_thumb_color()


    def _on_enter(self, event):

        if self._disabled:
            return

        self._hovered = True

        self._update_thumb_color()


    def _on_leave(self, event):

        self._hovered = False

        if not self._dragging:

            self._pressed = False

        self._update_thumb_color()


    def _scroll_to(self, x, y):

        self._tk_canvas.update_idletasks()

        w, h = self._tk_canvas.winfo_width(), self._tk_canvas.winfo_height()


        if self._orientation == Orientation.Vertical:

            fraction = y / h

        else:

            fraction = x / w


        fraction = max(0, min(fraction, 1.0))

        self.on_scroll.broadcast(fraction)


    def _update_thumb_color(self):

        if self._disabled:

            color = self._styles['disable']['thumb']

        elif self._pressed:

            color = self._styles['press']['thumb']

        elif self._hovered:

            color = self._styles['hover']['thumb']

        else:

            color = self._styles['normal']['thumb']


        self._tk_canvas.itemconfig(self._thumb, fill=color)

    def _update_cursor(self):

        if self._tk_canvas:
            self._tk_canvas.config(cursor="no" if self._disabled else "")

    def set_position(self, start, end):

        start, end = float(start), float(end)

        self._start = start

        self._end = end


        self._tk_canvas.update_idletasks()

        w, h = self._tk_canvas.winfo_width(), self._tk_canvas.winfo_height()


        margin = 2

        if self._orientation == Orientation.Vertical:

            self._tk_canvas.coords(self._thumb, margin, start * h, w - margin, end * h)

        else:

            self._tk_canvas.coords(self._thumb, start * w, margin, end * w, h - margin)


        self._update_thumb_color()


    def refresh_theme(self):

        self._tk_canvas.config(bg=self._styles['normal']['trough'])

        self._update_thumb_color()


    def refresh(self):

        self.refresh_theme()


    def set_disabled(self, disabled):

        self._disabled = disabled

        self._update_thumb_color()

        self._update_cursor()


    def is_disabled(self):

        return self._disabled