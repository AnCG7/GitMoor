import tkinter as tk
import math
import time
from ...core.view import View
from ...core.manager.ui_style_manager import UIStyleManager


class LoadingChaseView(View):
    DOT_SIZE = 10
    TRACK_WIDTH = 36
    PERIOD = 1.4
    MIN_BRIGHT = 0.18
    MAX_BRIGHT = 0.92
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
        
        canvas_w = self.TRACK_WIDTH + self.DOT_SIZE + 40
        canvas_h = self.DOT_SIZE + 40
        
        self._canvas = tk.Canvas(
            self._tk_frame,
            width=canvas_w,
            height=canvas_h,
            bg=style.bg.color,
            highlightthickness=0
        )
        self._canvas.pack(expand=True)
        
        self._cx = canvas_w / 2.0
        self._cy = canvas_h / 2.0
        self._half_track = self.TRACK_WIDTH / 2.0
        
        self._fg_color = style.fg.color
        self._bg_color = style.bg.color
        
        # 预创建两个方块
        for _ in range(2):
            rect = self._canvas.create_rectangle(
                0, 0, self.DOT_SIZE, self.DOT_SIZE,
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
        
        full_phase = now / self.PERIOD
        cycle = int(full_phase) % 2
        phase = full_phase % 1.0
        
        wave = math.sin(phase * 2 * math.pi)
        
        for i in range(2):
            if i == 0:
                x_offset = wave * self._half_track
            else:
                x_offset = -wave * self._half_track
            
            is_bright_turn = (i == 0 and cycle == 0) or (i == 1 and cycle == 1)
            
            if is_bright_turn:
                bright_raw = (math.cos(phase * 2 * math.pi - math.pi) + 1.0) / 2.0
            else:
                bright_raw = 0.0
            
            brightness = self.MIN_BRIGHT + (self.MAX_BRIGHT - self.MIN_BRIGHT) * bright_raw
            
            x = self._cx + x_offset - self.DOT_SIZE / 2.0
            y = self._cy - self.DOT_SIZE / 2.0
            self._canvas.coords(
                self._rects[i],
                x, y, x + self.DOT_SIZE, y + self.DOT_SIZE
            )
            
            color = self._brightness_to_color(brightness)
            self._canvas.itemconfig(self._rects[i], fill=color)
        
        self._after_id = self._tk_frame.after(self.FRAME_INTERVAL, self._animate)
