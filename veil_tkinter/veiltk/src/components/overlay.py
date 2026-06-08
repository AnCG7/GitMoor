import tkinter as tk
from ..core.view import View


class Overlay(View):
    def __init__(self, master=None, bg_color='#FFFFFF', alpha=1.0, **kwargs):
        self._bg_color = bg_color
        self._alpha = alpha
        self._tk_frame = None
        super().__init__(master, **kwargs)

    def _build_widget(self, master=None, **kwargs):
        master_tk = self._get_master_tk()
        
        self._tk_frame = tk.Frame(master_tk, bg=self._bg_color)
        return self._tk_frame

    def _on_appeared(self):
        if self._tk_frame:
            self._tk_frame.place(x=0, y=0, relwidth=1, relheight=1)

    def _on_disappeared(self):
        if self._tk_frame:
            self._tk_frame.place_forget()

    def set_background_color(self, color):
        self._bg_color = color
        if self._tk_frame:
            self._tk_frame.config(bg=color)

    def set_alpha(self, alpha):
        self._alpha = alpha
        if self._tk_frame and hasattr(self._tk_frame, 'attributes'):
            self._tk_frame.attributes('-alpha', alpha)