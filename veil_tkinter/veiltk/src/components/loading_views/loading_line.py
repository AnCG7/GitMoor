import tkinter as tk
from ...core.view import View
from ...core.manager.ui_style_manager import UIStyleManager


class LoadingLineView(View):
    def __init__(self, master=None, **kwargs):
        self._kwargs = kwargs
        self._tk_frame = None
        self._canvas = None
        self._line_bar = None
        self._styles = None
        self._anim_x = 0
        self._track_width = 0
        self._track_height = 2
        self._bar_width = 0
        self._after_id = None
        self._internal_bind_ids = []
        
        super().__init__(master, **kwargs)
    
    def _build_widget(self, master=None, **kwargs):
        master_tk = self._get_master_tk()
        
        self._styles = UIStyleManager.get_instance()
        style = self._styles.get_style().component.loading
        
        # 创建根 Frame
        self._tk_frame = tk.Frame(master_tk, bg=style.bg.color, **self._kwargs)
        
        # 创建 Canvas 轨道（初始大小为0，由父级控制）
        self._canvas = tk.Canvas(
            self._tk_frame,
            width=150,
            height=4,
            bg=style.trough.color,
            highlightthickness=0
        )
        self._canvas.pack(fill='both', expand=True)
        
        # 创建滑块矩形（初始位置）
        self._line_bar = self._canvas.create_rectangle(
            0, 0, 0, 0,
            fill=style.fg.color,
            outline=""
        )
        
        # 初始化动画坐标
        self._anim_x = 0
        
        # 注册主题监听器
        self._register_listeners()
        
        # 监听 Canvas 大小变化
        self._internal_bind_ids.append((self._canvas, '<Configure>', self._canvas.bind('<Configure>', self._on_canvas_resize, add='+')))
        
        return self._tk_frame
    
    def _on_canvas_resize(self, event):
        # 更新轨道尺寸
        self._track_width = event.width
        self._track_height = event.height
        
        # 滑块宽度为轨道宽度的 30%（保持比例），最小为 1px
        self._bar_width = max(1, int(self._track_width * 0.3))
        
        # 如果滑块当前位置超过新轨道宽度，重置到安全位置
        if self._anim_x > self._track_width:
            self._anim_x = min(self._anim_x, self._track_width - self._bar_width)
        
        # 更新滑块坐标
        self._canvas.coords(
            self._line_bar,
            self._anim_x, 0,
            self._anim_x + self._bar_width, self._track_height
        )
    
    def _register_listeners(self):
        self._styles.on_theme_changed.add_listener(self._on_theme_changed_internal)
    
    def _unregister_listeners(self):
        self._styles.on_theme_changed.remove_listener(self._on_theme_changed_internal)
    
    def _on_theme_changed_internal(self, theme):
        self.refresh_theme()
    
    def refresh_theme(self):
        style = self._styles.get_style().component.loading
        
        self._tk_frame.config(bg=style.bg.color)
        self._canvas.config(bg=style.trough.color)
        self._canvas.itemconfig(self._line_bar, fill=style.fg.color)
    
    def _on_appeared(self):
        self._animate()
    
    def _on_disappeared(self):
        if self._after_id:
            self._tk_frame.after_cancel(self._after_id)
            self._after_id = None
    
    def _on_destroy(self):
        self._on_disappeared()
        self._unbind_internal_events()
        self._unregister_listeners()
        super()._on_destroy()

    def _unbind_internal_events(self):
        for widget, sequence, funcid in self._internal_bind_ids:
            try:
                widget.unbind(sequence, funcid)
            except:
                pass
        self._internal_bind_ids.clear()
    
    def _animate(self):
        if not self._tk_frame.winfo_exists():
            return
        
        # 原始轨道宽度（用于计算速度比例）
        ORIGINAL_TRACK_WIDTH = 150
        
        # 如果轨道宽度为0，跳过动画
        if self._track_width <= 0:
            self._after_id = self._tk_frame.after(16, self._animate)
            return
        
        # 计算速度比例，保持动画速度与原始一致
        speed_ratio = self._track_width / ORIGINAL_TRACK_WIDTH
        step = 4 * speed_ratio
        
        self._anim_x += step
        
        if self._anim_x > self._track_width:
            self._anim_x = -self._bar_width
        
        self._canvas.coords(
            self._line_bar,
            self._anim_x, 0,
            self._anim_x + self._bar_width, self._track_height
        )
        
        self._after_id = self._tk_frame.after(16, self._animate)
