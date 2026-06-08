import tkinter as tk
import math
import time
from ...core.view import View
from ...core.manager.ui_style_manager import UIStyleManager


class LoadingRectView(View):
    DOT_SIZE = 10
    GAP = 12
    NUM_DOTS = 3
    PERIOD = 1.5
    PHASE_GAP = 0.2
    MIN_BRIGHT = 0.10
    MAX_BRIGHT = 1.0
    FRAME_INTERVAL = 16
    
    def __init__(self, master=None, **kwargs):
        self._kwargs = kwargs
        self._tk_frame = None
        self._canvas = None
        self._rects = []
        self._styles = None
        self._after_id = None
        self._start_time = None
        
        self._styles = UIStyleManager.get_instance()
        
        super().__init__(master, **kwargs)
    
    def _build_widget(self, master=None, **kwargs):
        master_tk = self._get_master_tk()
        
        style = self._styles.get_style().component.loading
        
        self._tk_frame = tk.Frame(master_tk, bg=style.bg.color, **self._kwargs)
        
        total_w = self.NUM_DOTS * self.DOT_SIZE + (self.NUM_DOTS - 1) * self.GAP
        canvas_w = total_w + 40
        canvas_h = self.DOT_SIZE + 40
        
        self._canvas = tk.Canvas(
            self._tk_frame,
            width=canvas_w,
            height=canvas_h,
            bg=style.bg.color,
            highlightthickness=0
        )
        self._canvas.pack(expand=True)
        
        self._fg_color = style.fg.color
        self._bg_color = style.bg.color
        
        start_x = (canvas_w - total_w) // 2
        cy = canvas_h // 2
        
        for i in range(self.NUM_DOTS):
            x = start_x + i * (self.DOT_SIZE + self.GAP)
            y = cy - self.DOT_SIZE // 2
            rect = self._canvas.create_rectangle(
                x, y, x + self.DOT_SIZE, y + self.DOT_SIZE,
                fill=style.bg.color,
                outline="",
                width=0
            )
            self._rects.append(rect)
        
        self._start_time = time.perf_counter()
        
        self._register_listeners()
        
        return self._tk_frame
    
    def _register_listeners(self):
        self._styles.on_theme_changed.add_listener(self._on_theme_changed_internal)
    
    def _unregister_listeners(self):
        self._styles.on_theme_changed.remove_listener(self._on_theme_changed_internal)
    
    def _on_theme_changed_internal(self, theme):
        self.refresh_theme()
    
    def refresh_theme(self):
        style = self._styles.get_style().component.loading
        
        self._tk_frame.config(bg=style.bg.color)
        self._canvas.config(bg=style.bg.color)
        self._fg_color = style.fg.color
        self._bg_color = style.bg.color
    
    def _on_appeared(self):
        self._animate()
    
    def _on_disappeared(self):
        if self._after_id:
            self._tk_frame.after_cancel(self._after_id)
            self._after_id = None
    
    def _on_destroy(self):
        self._on_disappeared()
        self._unregister_listeners()
        super()._on_destroy()
    
    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hex(self, rgb):
        return f'#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}'
    
    def _brightness_to_color(self, brightness):
        bg_r, bg_g, bg_b = self._hex_to_rgb(self._bg_color)
        fg_r, fg_g, fg_b = self._hex_to_rgb(self._fg_color)
        
        r = bg_r + (fg_r - bg_r) * brightness
        g = bg_g + (fg_g - bg_g) * brightness
        b = bg_b + (fg_b - bg_b) * brightness
        
        return self._rgb_to_hex((r, g, b))
    
    def _animate(self):
        if not self._tk_frame.winfo_exists():
            return
        
        now = time.perf_counter() - self._start_time
        
        for i in range(self.NUM_DOTS):
            elapsed = now - i * self.PHASE_GAP
            phase = (elapsed % self.PERIOD) / self.PERIOD
            
            raw = (math.sin(phase * 2 * math.pi - math.pi / 2) + 1.0) / 2.0
            brightness = self.MIN_BRIGHT + (self.MAX_BRIGHT - self.MIN_BRIGHT) * raw
            
            color = self._brightness_to_color(brightness)
            self._canvas.itemconfig(self._rects[i], fill=color)
        
        self._after_id = self._tk_frame.after(self.FRAME_INTERVAL, self._animate)
