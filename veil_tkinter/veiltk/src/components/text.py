import tkinter as tk
import enum
from ..core.view import View
from ..core.manager.ui_style_manager import UIStyleManager, StyleObject
from ..core.manager.event_manager import Event
from ..core.manager.localization_manager import LocalizedText, LocalizationManager
from ..core.utils.platform_input_bind import PlatformInputBind
from .scrollbar import Scrollbar, Orientation, ScrollbarState
from .scroll_listbox import ScrollbarMode


class TextMode(enum.Enum):
    Normal = "normal"
    Readonly = "readonly"
    Display = "display"
    Disable = "disable"
    Label = "label"


class TextInteractionState(enum.Enum):
    Idle = "none"
    Hover = "hover"
    Active = "active"
    Focus = "focus"


class TextWrapMode(enum.Enum):
    None_ = "none"
    Char = "char"
    Word = "word"

    def to_tk(self):
        _WRAP_MAP = {
            TextWrapMode.None_: tk.NONE,
            TextWrapMode.Char: tk.CHAR,
            TextWrapMode.Word: tk.WORD,
        }
        return _WRAP_MAP[self]


class Text(View):
    def __init__(self, master=None, text=None, wrap_mode=TextWrapMode.Char, scrollbar_mode=ScrollbarMode.Auto, **kwargs):
        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")

        if not isinstance(wrap_mode, TextWrapMode):
            raise TypeError("wrap_mode 参数必须是 TextWrapMode 枚举类型")

        if not isinstance(scrollbar_mode, ScrollbarMode):
            raise TypeError("scrollbar_mode 参数必须是 ScrollbarMode 枚举类型")

        if 'wrap' in kwargs:
            print(f"警告: 不支持通过 kwargs 设置 wrap，请使用 wrap_mode 参数或 set_wrap_mode() 方法，已忽略传入的 wrap 值")
            kwargs.pop('wrap')

        self._text = text
        self._wrap_mode = wrap_mode
        self._scrollbar_mode = scrollbar_mode
        self._kwargs = kwargs
        self._tk_frame = None
        self._tk_frame_b = None
        self._tk_text = None
        self._scrollbar = None
        self._styles = None
        self._text_mode = TextMode.Normal
        self._interaction_state = TextInteractionState.Idle
        self._scrollbar_visible = None
        self._mouse_inside = False
        self._block_tab = False
        self._internal_bind_ids = []
        self._show_frame_decoration = True
        self._selectable = True
        self._layout_in_progress = False
        self._last_text_width = None
        self._last_text_height = None
        self._scrollbar_stable = False
        self._mapped = False
        self._is_global_click_bound = False
        self._global_click_id = None

        # Events
        self.on_focus_in = Event()
        self.on_focus_out = Event()
        self.on_text_changed = Event()
        self._on_click_event = Event()
        self._on_double_click_event = Event()
        self._on_triple_click_event = Event()
        self._on_enter_event = Event()
        self._on_leave_event = Event()
        self._on_press_event = Event()
        self._on_release_event = Event()
        self._on_motion_event = Event()
        self._on_key_press_event = Event()
        self._on_configure_event = Event()
        self._on_scroll_event = Event()
        self._on_tab_block_event = Event()

        self.styles = UIStyleManager.get_instance()
        self.localization = LocalizationManager.get_instance()

        super().__init__(master, **kwargs)

    def _build_widget(self, master=None, **kwargs):
        master_tk = self._get_master_tk()

        self._config_styles()

        size_preset = self.styles.get_size_preset('normal')
        self._padx = 4
        self._pady = size_preset['pady']

        # 检测用户是否通过构造参数指定了像素尺寸（父级掌控布局）
        has_fixed_size = 'height' in self._kwargs or 'width' in self._kwargs

        default_kwargs = {
            "bg": self._styles.normal.bg,
            "relief": tk.FLAT,
            "borderwidth": 0,
            "highlightthickness": 1,
            "highlightbackground": self._styles.normal.border,
            "highlightcolor": self._styles.focus.border,
            "takefocus": True,
        }
        default_kwargs.update(self._kwargs)
        self._tk_frame = tk.Frame(master_tk, **default_kwargs)

        # 如果用户指定了像素尺寸，切断内部reqheight/reqwidth传播，确保父级掌控布局
        if has_fixed_size:
            self._tk_frame.pack_propagate(False)

        self._tk_frame_b = tk.Frame(
            self._tk_frame,
            bg=self._styles.normal.bg,
            padx=self._padx,
            pady=self._pady,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
        )

        self._create_widgets()
        self._bind_events()
        self._register_listeners()
        self._update_styles()
        self._update_global_click_binding()

        return self._tk_frame

    def _create_widgets(self):
        bg_color = self._styles.normal.bg
        fg_color = self._styles.normal.fg
        normal_font = self._styles.normal.font
        wrap_tk = self._wrap_mode.to_tk()

        self._tk_text = tk.Text(
            self._tk_frame_b,
            wrap=wrap_tk,
            width=40,
            height=1,
            bg=bg_color,
            fg=fg_color,
            font=normal_font,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            padx=0,
            pady=2,
            cursor='xterm',
            takefocus=1,
            undo=True,
            maxundo=50,
            tabs=(32,),
        )

        if self._text:
            display_text = self._text.get_text()
            self._tk_text.insert('1.0', display_text)
            self._tk_text.edit_modified(False)

        self._tk_text.config(yscrollcommand=self._sync_scrollbar)

        self._scrollbar = Scrollbar(self._tk_frame, orientation=Orientation.Vertical)
        self._scrollbar.on_scroll.add_listener(self._on_scrollbar_scroll)
        self._scrollbar.on_click.add_listener(self._on_scrollbar_click)

        self._hack_internal_components()

        self._tk_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._tk_frame_b.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _hack_internal_components(self):
        self._tk_text.config(takefocus=0)
        self._scrollbar.config(takefocus=0)
        self._tk_text.config(highlightthickness=0, borderwidth=0)

    def _bind_events(self):
        bind_targets = [self._tk_frame_b, self._tk_text]
        for target in bind_targets:
            self._internal_bind_ids.append((target, '<Button-1>', target.bind('<Button-1>', self._on_press_internal, add='+')))
            self._internal_bind_ids.append((target, '<Double-Button-1>', target.bind('<Double-Button-1>', self._on_double_click_internal, add='+')))
            self._internal_bind_ids.append((target, '<Triple-Button-1>', target.bind('<Triple-Button-1>', self._on_triple_click_internal, add='+')))
            self._internal_bind_ids.append((target, '<Enter>', target.bind('<Enter>', self._on_enter_internal, add='+')))
            self._internal_bind_ids.append((target, '<Leave>', target.bind('<Leave>', self._on_leave_internal, add='+')))
            self._internal_bind_ids.append((target, '<ButtonRelease-1>', target.bind('<ButtonRelease-1>', self._on_release_internal, add='+')))
            self._internal_bind_ids.append((target, '<Motion>', target.bind('<Motion>', self._on_motion_internal, add='+')))
            self._internal_bind_ids.append((target, '<B1-Motion>', target.bind('<B1-Motion>', self._on_motion_internal, add='+')))

        # 焦点管理
        self._internal_bind_ids.append((self._tk_frame, '<FocusIn>', self._tk_frame.bind('<FocusIn>', self._on_focus_in_internal, add='+')))
        self._internal_bind_ids.append((self._tk_frame, '<FocusOut>', self._tk_frame.bind('<FocusOut>', self._on_focus_out_internal, add='+')))

        # Tab 导航
        self._internal_bind_ids.append((self._tk_text, '<Tab>', self._tk_text.bind('<Tab>', self._on_tab_internal, add='+')))
        self._internal_bind_ids.extend(PlatformInputBind.bind_shift_tab(self._tk_text, self._on_shift_tab_internal))
        self._internal_bind_ids.append((self._tk_text, '<Control-Tab>', self._tk_text.bind('<Control-Tab>', self._on_ctrl_tab_internal, add='+')))
        self._internal_bind_ids.extend(PlatformInputBind.bind_ctrl_shift_tab(self._tk_text, self._on_ctrl_shift_tab_internal))

        # 核心拦截与底层事件监听
        self._internal_bind_ids.append((self._tk_text, '<KeyPress>', self._tk_text.bind('<KeyPress>', self._on_key_press_internal, add='+')))
        self._internal_bind_ids.append((self._tk_text, '<Configure>', self._tk_text.bind('<Configure>', self._on_configure_internal, add='+')))
        self._internal_bind_ids.append((self._tk_text, '<<Modified>>', self._tk_text.bind('<<Modified>>', self._on_text_modified_internal, add='+')))

        # 快捷键拦截与放行
        self._internal_bind_ids.append((self._tk_text, '<<Copy>>', self._tk_text.bind('<<Copy>>', self._on_platform_copy, add='+')))
        self._internal_bind_ids.append((self._tk_text, '<<SelectAll>>', self._tk_text.bind('<<SelectAll>>', self._on_platform_select_all, add='+')))

        # 彻底封死只读/显示模式下的底层写操作虚拟事件
        for write_event in ('<<Paste>>', '<<Cut>>', '<<Clear>>', '<<Undo>>', '<<Redo>>', '<<PasteSelection>>'):
            self._internal_bind_ids.append((self._tk_text, write_event, self._tk_text.bind(write_event, self._block_modify_events, add='+')))

        self._internal_bind_ids.extend(PlatformInputBind.bind_mousewheel(self._tk_frame_b, self._on_mouse_wheel))
        self._add_parent_to_bindtags(self._tk_text, self._tk_frame_b)

        self._internal_bind_ids.append((self._scrollbar._tk_canvas, '<Enter>', self._scrollbar._tk_canvas.bind('<Enter>', self._on_scrollbar_enter, add='+')))
        self._internal_bind_ids.append((self._scrollbar._tk_canvas, '<Leave>', self._scrollbar._tk_canvas.bind('<Leave>', self._on_scrollbar_leave, add='+')))

    def _block_modify_events(self, event):
        """当处于非可编辑模式时，彻底截断任何虚拟修改事件"""
        if self._text_mode in (TextMode.Readonly, TextMode.Display, TextMode.Disable) or (self._text_mode == TextMode.Label and not self._selectable):
            return 'break'

    def _add_parent_to_bindtags(self, widget, parent):
        try:
            current_tags = widget.bindtags()
            if parent not in current_tags:
                new_tags = list(current_tags)
                new_tags.insert(1, parent)
                widget.bindtags(tuple(new_tags))
        except Exception:
            pass

    def _config_styles(self):
        current_state = self.styles.get_style()
        styles_dict = {
            'normal': {
                'bg': current_state.component.text.normal.bg.color,
                'fg': current_state.component.label.fg.color,
                'font': current_state.font.normal,
                'border': current_state.component.text.normal.border.color
            },
            'hover': {
                'bg': current_state.component.text.hover.bg.color,
                'fg': current_state.component.text.hover.fg.color,
                'border': current_state.component.text.hover.border.color
            },
            'active': {
                'bg': current_state.component.text.hover.bg.color,
                'fg': current_state.component.text.hover.fg.color,
                'border': current_state.component.text.hover.border.color
            },
            'focus': {
                'bg': current_state.component.button.secondary.hover.bg.color,
                'fg': current_state.component.label.fg.color,
                'border': current_state.component.text.focus.border.color
            },
            'disable': {
                'bg': current_state.component.text.disable.bg.color,
                'fg': current_state.component.text.disable.fg.color,
                'border': current_state.component.text.disable.border.color
            },
            'selected_font': {
                'bg': current_state.component.text.selected_font.bg.color,
                'fg': current_state.component.text.selected_font.fg.color
            }
        }
        self._styles = StyleObject(styles_dict)

    def _update_styles(self):
        style_key = (self._text_mode, self._interaction_state)
        if getattr(self, '_last_style_key', None) == style_key:
            return
        self._last_style_key = style_key

        # 动态控制内层 _tk_text 的 takefocus：Label 模式内容未超出时设为 0，杜绝 Tab/点击意外聚焦
        if self._text_mode == TextMode.Label and not self._content_exceeds_view():
            takefocus_val = 0
        else:
            takefocus_val = 0
        cursor = 'xterm'
        tk_state = 'normal'

        if self._text_mode == TextMode.Disable:
            cursor, tk_state = 'no', 'disabled'
            style = self._styles.disable
        elif self._text_mode == TextMode.Display:
            # Display 模式可选择时必须为 normal 状态，否则 Tkinter 无法渲染选区
            if self._selectable and not self._is_content_empty():
                cursor, tk_state = 'xterm', 'normal'
            else:
                cursor, tk_state = 'arrow', 'disabled'
            style = self._styles.normal
        elif self._text_mode == TextMode.Label:
            if self._selectable and not self._is_content_empty():
                cursor, tk_state = 'xterm', 'normal'  # 保持 normal 以托管丝滑选择
            else:
                cursor, tk_state = 'arrow', 'disabled'
            style = self._styles.normal
        elif self._text_mode == TextMode.Readonly:
            if self._is_content_empty():
                cursor = 'arrow'
            else:
                cursor, tk_state = 'xterm', 'normal'  # 核心改动：保持 normal 状态以托管原生优雅选区
            if self._interaction_state == TextInteractionState.Focus:
                style = self._styles.focus
            elif self._interaction_state == TextInteractionState.Hover:
                style = self._styles.hover
            elif self._interaction_state == TextInteractionState.Active:
                style = self._styles.active
            else:
                style = self._styles.normal
        else:  # Normal
            cursor, tk_state = 'xterm', 'normal'
            if self._interaction_state == TextInteractionState.Focus:
                style = self._styles.focus
            elif self._interaction_state == TextInteractionState.Hover:
                style = self._styles.hover
            elif self._interaction_state == TextInteractionState.Active:
                style = self._styles.active
            else:
                style = self._styles.normal

        if self._text_mode == TextMode.Disable:
            frame_takefocus = 0
        elif self._text_mode == TextMode.Label:
            frame_takefocus = 1 if self._content_exceeds_view() else 0
        elif self._text_mode == TextMode.Display:
            frame_takefocus = 1 if self._content_exceeds_view() else 0
        else:
            frame_takefocus = 1

        struct_key = (self._text_mode, self._show_frame_decoration)
        struct_changed = getattr(self, '_last_struct_key', None) != struct_key
        if struct_changed:
            self._last_struct_key = struct_key
            if self._show_frame_decoration:
                self._tk_frame.config(highlightbackground=style.border, highlightcolor=self._styles.focus.border, highlightthickness=1)
                self._tk_frame_b.config(padx=self._padx, pady=self._pady)
            else:
                self._tk_frame.config(highlightbackground=style.bg, highlightcolor=style.bg, highlightthickness=0)
                self._tk_frame_b.config(padx=0, pady=0)

        if self._show_frame_decoration:
            self._tk_frame.config(bg=style.bg, takefocus=frame_takefocus, highlightbackground=style.border, highlightcolor=self._styles.focus.border)
        else:
            self._tk_frame.config(bg=style.bg, takefocus=frame_takefocus, highlightbackground=style.bg, highlightcolor=style.bg)
        self._tk_frame_b.config(bg=style.bg, cursor=cursor)

        # 只读模式下可以通过控制 insertwidth=0 或隐去光标颜色，隐藏闪烁插入标，保证扁平设计纯净度
        show_caret = (self._text_mode == TextMode.Normal)
        self._tk_text.config(
            state='normal',
            bg=style.bg,
            fg=style.fg,
            cursor=cursor,
            takefocus=takefocus_val,
            insertbackground=style.fg if show_caret else style.bg,
            insertwidth=2 if show_caret else 0,
            selectbackground=style.bg if self._is_content_empty() else self._styles.selected_font.bg,
            selectforeground=self._styles.selected_font.fg,
        )

        if self._scrollbar is not None:
            self._scrollbar.set_disabled(self._text_mode == TextMode.Disable)

        if struct_changed:
            self._update_scrollbar_state()
            if self._scrollbar_visible:
                self._force_scrollbar_position()

        if tk_state == 'disabled':
            self._tk_text.config(state='disabled')

    def _sync_scrollbar(self, *args):
        if not hasattr(self, '_scrollbar') or self._scrollbar is None:
            return
        if len(args) == 2:
            try:
                start = float(args[0])
                end = float(args[1])
                if self._scrollbar_visible or self._scrollbar_mode == ScrollbarMode.Always:
                    self._scrollbar.set_position(start, end)
            except (ValueError, tk.TclError):
                pass

    def _on_scrollbar_scroll(self, fraction):
        try:
            self._tk_text.yview_moveto(fraction)
        except tk.TclError:
            pass

    def _on_scrollbar_click(self, event):
        self.focus_set()

    def _force_scrollbar_position(self):
        try:
            if self._scrollbar is not None and self._scrollbar_visible:
                yv = self._tk_text.yview()
                if len(yv) == 2:
                    self._scrollbar.set_position(float(yv[0]), float(yv[1]))
        except (tk.TclError, ValueError):
            pass

    def _on_mouse_wheel(self, event, delta):
        if not self._mouse_inside:
            return
        if self._text_mode == TextMode.Disable:
            return 'break'
        try:
            yview = self._tk_text.yview()
            if len(yview) != 2:
                return
            content_exceeds = not (yview[0] <= 0.001 and yview[1] >= 0.999)
            if not content_exceeds:
                return
            if self._text_mode not in (TextMode.Display, TextMode.Label):
                self.focus_set()
            self._tk_text.yview_scroll(-1 * delta, 'units')
            self._on_scroll_event.broadcast(event)
            return 'break'
        except tk.TclError:
            pass

    def _update_scrollbar_state(self, *args, show_only=False):
        if not hasattr(self, '_scrollbar') or self._scrollbar is None:
            return
        if not self._mapped:
            return

        try:
            yview = self._tk_text.yview()
            if len(yview) != 2:
                return
            content_exceeds = not (yview[0] <= 0.001 and yview[1] >= 0.999)
        except tk.TclError:
            content_exceeds = False

        needs_show = False
        if self._scrollbar_mode == ScrollbarMode.Always:
            needs_show = True
        elif self._scrollbar_mode == ScrollbarMode.Never:
            needs_show = False
        elif self._scrollbar_mode == ScrollbarMode.Auto:
            needs_show = content_exceeds

        if needs_show and self._scrollbar_visible is not True:
            self._layout_in_progress = True
            self._tk_frame_b.pack_forget()
            self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self._tk_frame_b.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self._scrollbar_visible = True
            self._scrollbar_stable = True
            self._tk_frame.after_idle(self._clear_layout_flag)
        elif not needs_show and self._scrollbar_visible is not False and not show_only:
            # 只有非 show_only 调用（即内容变化/手动设置）才允许隐藏
            self._layout_in_progress = True
            if self._scrollbar_visible is True:
                self._scrollbar.pack_forget()
            else:
                self._tk_frame_b.pack_forget()
                self._tk_frame_b.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self._scrollbar_visible = False
            self._scrollbar_stable = False
            self._tk_frame.after_idle(self._clear_layout_flag)

        if self._scrollbar_visible and self._has_focus():
            if self._text_mode in (TextMode.Normal, TextMode.Readonly, TextMode.Display, TextMode.Label):
                if self._scrollbar is not None:
                    self._scrollbar.set_state(ScrollbarState.Focus)
        elif not self._scrollbar_visible and self._scrollbar is not None:
            self._scrollbar.set_state(ScrollbarState.Normal)

        if self._scrollbar_visible:
            self._force_scrollbar_position()

    def _clear_layout_flag(self):
        self._layout_in_progress = False

    def _is_content_empty(self) -> bool:
        """判断文本内容是否为空（排除 Tkinter 末尾隐形换行符）"""
        try:
            return self._tk_text.get('1.0', 'end-1c') == ''
        except tk.TclError:
            return True

    def _update_select_color(self):
        """根据内容是否为空，直接更新选区背景色（绕过 _update_styles 缓存）"""
        try:
            if self._is_content_empty():
                self._tk_text.config(selectbackground=self._styles.normal.bg)
            else:
                self._tk_text.config(selectbackground=self._styles.selected_font.bg)
        except tk.TclError:
            pass

    def _on_text_modified_internal(self, event):
        try:
            if self._tk_text.edit_modified():
                self._tk_text.edit_modified(False)
                content = self._tk_text.get('1.0', 'end-1c')
                self.on_text_changed.broadcast(content)
                self._update_scrollbar_state()
                self._update_select_color()
        except tk.TclError:
            pass

    def _content_exceeds_view(self):
        """判断内容是否超出可视区域（不依赖 scrollbar 是否可见）"""
        try:
            yview = self._tk_text.yview()
            if len(yview) == 2:
                return not (yview[0] <= 0.001 and yview[1] >= 0.999)
        except tk.TclError:
            pass
        return False

    def _on_focus_in_internal(self, event):
        if self._text_mode == TextMode.Disable:
            self._tk_frame.after_idle(self._deflect_focus)
            return "break"
        if self._text_mode == TextMode.Display:
            # 可选时需要保留内核焦点以渲染选区，不可选 + 内容未超出时才转移
            if not self._selectable and not self._content_exceeds_view():
                self._tk_frame.after_idle(self._deflect_focus)
                return "break"
        if self._text_mode == TextMode.Label:
            # 无内容时一律拒绝焦点
            if self._is_content_empty():
                self._tk_frame.after_idle(self._deflect_focus)
                return "break"
            # 不可选 + 内容未超出时转移焦点
            if not self._selectable and not self._content_exceeds_view():
                self._tk_frame.after_idle(self._deflect_focus)
                return "break"
        previous = self._interaction_state
        self._interaction_state = TextInteractionState.Focus
        # Label 模式：有焦点且可选时显示边框装饰
        if self._text_mode == TextMode.Label and self._selectable:
            self._show_frame_decoration = True
            if hasattr(self, '_last_style_key'):
                del self._last_style_key
            if hasattr(self, '_last_struct_key'):
                del self._last_struct_key
        if self._interaction_state != previous:
            self._update_styles()
        if self._tk_frame.focus_get() != self._tk_text:
            self._tk_text.focus_set()
        if self._text_mode in (TextMode.Normal, TextMode.Readonly, TextMode.Display, TextMode.Label):
            if self._content_exceeds_view() and self._scrollbar is not None:
                self._scrollbar.set_state(ScrollbarState.Focus)
        self.on_focus_in.broadcast()

    def _on_focus_out_internal(self, event):
        self._tk_frame.after_idle(self._check_focus_loss)

    def _check_focus_loss(self):
        if self._has_focus():
            return
        # Label 模式：失去焦点时关闭边框装饰
        if self._text_mode == TextMode.Label and self._show_frame_decoration:
            self._show_frame_decoration = False
            if hasattr(self, '_last_style_key'):
                del self._last_style_key
            if hasattr(self, '_last_struct_key'):
                del self._last_struct_key
        if self._text_mode != TextMode.Disable:
            previous = self._interaction_state
            self._interaction_state = TextInteractionState.Idle
            if self._interaction_state != previous:
                self._update_styles()
        if self._scrollbar is not None:
            self._scrollbar.set_state(ScrollbarState.Normal)
        self._clear_selection()
        self.on_focus_out.broadcast()

    def _has_focus(self):
        try:
            focused = self._tk_frame.focus_get()
            return focused in (self._tk_frame, self._tk_text, self._tk_frame_b)
        except Exception:
            return False

    def _clear_selection(self):
        if not hasattr(self, '_tk_text') or self._tk_text is None:
            return
        try:
            prev_state = self._tk_text.cget('state')
            if prev_state == 'disabled':
                self._tk_text.config(state='normal')
            self._tk_text.tag_remove('sel', '1.0', tk.END)
            if prev_state == 'disabled':
                self._tk_text.config(state='disabled')
        except tk.TclError:
            pass

    def _navigate_focus(self, forward=True, start_from_frame=False):
        """安全地将焦点转移到组件外的下一个/上一个可聚焦控件。
        
        Args:
            forward: True=下一个, False=上一个
            start_from_frame: True=从 _tk_frame 开始, False=从 _tk_text 开始
        """
        _INTERNAL = (self._tk_frame, self._tk_text, self._tk_frame_b)
        try:
            curr = self._tk_frame if start_from_frame else self._tk_text
            terminal = self._tk_frame if start_from_frame else self._tk_text
            visited = set()  # 哨兵：检测焦点链上的环形回路，防止死循环
            # 安全上限：基于顶层窗口的子 widget 数量动态计算
            try:
                toplevel = curr.winfo_toplevel()
                widget_count = len(toplevel.winfo_children())
                max_steps = max(widget_count * 3, 20)
            except Exception:
                max_steps = 50  # 兜底值
            while len(visited) < max_steps:
                nxt = curr.tk_focusNext() if forward else curr.tk_focusPrev()
                if not nxt or nxt == terminal or nxt in visited:
                    break
                visited.add(nxt)
                if nxt not in _INTERNAL:
                    try:
                        if nxt.winfo_exists():
                            nxt.focus_set()
                    except Exception:
                        pass
                    break
                curr = nxt
        except Exception:
            pass

    def _deflect_focus(self):
        self._navigate_focus(forward=True, start_from_frame=True)

    def _on_tab_internal(self, event):
        self._on_tab_block_event.broadcast('tab')
        if self._block_tab:
            return 'break'

        if self._text_mode in (TextMode.Readonly, TextMode.Display, TextMode.Label):
            self._navigate_focus(forward=True)
            return 'break'

        try:
            self._tk_text.insert(tk.INSERT, '\t')
        except tk.TclError:
            pass
        return 'break'

    def _on_shift_tab_internal(self, event):
        self._on_tab_block_event.broadcast('shift_tab')
        if self._block_tab:
            return 'break'

        if self._text_mode in (TextMode.Readonly, TextMode.Display, TextMode.Label):
            self._navigate_focus(forward=False)
            return 'break'

    def _on_ctrl_tab_internal(self, event):
        if self._text_mode == TextMode.Disable:
            return 'break'
        self._navigate_focus(forward=True)
        return 'break'

    def _on_ctrl_shift_tab_internal(self, event):
        if self._text_mode == TextMode.Disable:
            return 'break'
        self._navigate_focus(forward=False)
        return 'break'

    def set_block_tab(self, block):
        self._block_tab = block

    def _on_enter_internal(self, event):
        self._mouse_inside = True
        if self._text_mode == TextMode.Disable:
            return
        if self._text_mode in (TextMode.Display, TextMode.Label) and not self._selectable:
            return
        previous = self._interaction_state
        if self._has_focus():
            self._interaction_state = TextInteractionState.Focus
        else:
            self._interaction_state = TextInteractionState.Hover
        if self._interaction_state != previous:
            self._update_styles()
        self._on_enter_event.broadcast(event)

    def _on_scrollbar_enter(self, event):
        self._mouse_inside = True

    def _on_scrollbar_leave(self, event):
        self._mouse_inside = False

    def _on_leave_internal(self, event):
        self._mouse_inside = False
        if self._text_mode in (TextMode.Disable, TextMode.Display, TextMode.Label) and not self._selectable:
            return
        if not self._has_focus():
            self._interaction_state = TextInteractionState.Idle
            self._update_styles()
        self._on_leave_event.broadcast(event)

    def _text_rel_xy(self, event):
        return (event.x_root - self._tk_text.winfo_rootx(),
                event.y_root - self._tk_text.winfo_rooty())

    def _on_press_internal(self, event):
        if self._text_mode == TextMode.Disable:
            return 'break'
        if self._text_mode == TextMode.Display:
            # 可选择时放行原生选择流，不可选择时截断
            if not self._selectable:
                return 'break'
        if self._text_mode == TextMode.Label:
            # 无内容时完全截断点击
            if self._is_content_empty():
                return 'break'
            # 内容未超出 + 不可选 → 彻底截断；可选时放行以允许鼠标拖选区
            if not self._content_exceeds_view() and not self._selectable:
                return 'break'
            if not self._selectable:
                return 'break'

        # 只读模式及Label可选现在完全托管给原生选择流，无需手动进行 tag_add 计算
        if not self._has_focus():
            if self._text_mode not in (TextMode.Readonly, TextMode.Label):
                self._interaction_state = TextInteractionState.Active
            self._update_styles()
        self._on_press_event.broadcast(event)

        if event.widget == self._tk_frame_b:
            text_x, text_y = self._text_rel_xy(event)
            text_w = self._tk_text.winfo_width()
            text_h = self._tk_text.winfo_height()

            # Label 模式内容未超出时，不主动 focus_set()，但放行原生选区拖拽
            if self._text_mode == TextMode.Label and not self._content_exceeds_view():
                if not self._selectable:
                    return 'break'
                # selectable=True 时继续执行，但不调用 focus_set()
            else:
                self.focus_set()

            # 如果点击在 _tk_text 之外的 padding 区域，只清除选区，不设置 insert 光标
            if not (0 <= text_x < text_w and 0 <= text_y < text_h):
                self._clear_selection()
                # Label 模式内容未超出时，点击空白取消选中、关闭装饰、转移焦点
                if self._text_mode == TextMode.Label and not self._content_exceeds_view():
                    self._show_frame_decoration = False
                    if hasattr(self, '_last_style_key'):
                        del self._last_style_key
                    if hasattr(self, '_last_struct_key'):
                        del self._last_struct_key
                    self._interaction_state = TextInteractionState.Idle
                    self._update_styles()
                    self._deflect_focus()
                return

            if self._text_mode in (TextMode.Normal, TextMode.Readonly, TextMode.Display) or (self._text_mode == TextMode.Label and self._selectable):
                try:
                    idx = self._tk_text.index(f'@{text_x},{text_y}')
                    self._tk_text.mark_set('insert', idx)
                    self._tk_text.tag_remove('sel', '1.0', tk.END)
                except tk.TclError:
                    pass

    def _on_release_internal(self, event):
        if self._text_mode == TextMode.Disable:
            return 'break'
        if self._text_mode == TextMode.Display and not self._selectable:
            return 'break'
        if self._text_mode == TextMode.Label:
            if not self._content_exceeds_view() and not self._selectable:
                return 'break'
            if not self._selectable:
                return 'break'

        if self._has_focus():
            self._interaction_state = TextInteractionState.Focus
        else:
            self._interaction_state = TextInteractionState.Hover
        self._update_styles()
        self._on_release_event.broadcast(event)

    def _on_motion_internal(self, event):
        if self._text_mode == TextMode.Disable:
            return 'break'
        if not self._selectable:
            # 任何模式下不可选时都阻止拖拽选区
            return 'break'
        if self._text_mode == TextMode.Display and not self._selectable:
            return 'break'
        if self._text_mode == TextMode.Label:
            if not self._content_exceeds_view() and not self._selectable:
                return 'break'
            if not self._selectable:
                return 'break'
        # 移除了所有冗余的多 Bug 选区计算，原生选择机制自动完美处理拖拽、缩小和自动边缘滚动
        self._on_motion_event.broadcast(event)

    def _on_platform_copy(self, event):
        if not self._selectable:
            return 'break'
        if self._text_mode == TextMode.Disable:
            return 'break'
        # 放行所有可选模式下的复制
        return

    def _on_platform_select_all(self, event):
        if not self._selectable:
            return 'break'
        if self._text_mode in (TextMode.Readonly, TextMode.Normal, TextMode.Label, TextMode.Display):
            try:
                self._tk_text.tag_add('sel', '1.0', 'end')
            except tk.TclError:
                pass
            return 'break'
        return 'break'

    def _on_key_press_internal(self, event):
        # 1. Disable 模式彻底封死
        if self._text_mode == TextMode.Disable:
            return "break"

        # 单独的修饰键按压在所有受限模式下都无害放行
        if event.keysym in PlatformInputBind.MODIFIER_KEYS:
            return

        # 2. Display（不可选）和 Label（不可选）模式：只放行滚动导航键
        if (self._text_mode == TextMode.Display and not self._selectable) or (self._text_mode == TextMode.Label and not self._selectable):
            if self._content_exceeds_view() and event.keysym in PlatformInputBind.SCROLL_KEYS:
                # 手动执行滚动，因为 Display/Label 模式下 tk_text 为 disabled 状态无法原生导航
                self._handle_keyboard_scroll(event)
                return "break"
            return "break"

        # 3. 精细控制只读与标签/显示可选交互
        if self._text_mode == TextMode.Readonly or ((self._text_mode == TextMode.Label or self._text_mode == TextMode.Display) and self._selectable):
            # 放行复制与全选组合键：keysym 是 c/a 且 char 为控制字符，表示 Ctrl/Command+C/A
            if event.keysym.lower() in ('c', 'a') and event.char and ord(event.char) < 32:
                return

            # 滚动导航键：直接执行视图滚动，避免隐形光标导致的"按多下才滚动"问题
            if event.keysym in PlatformInputBind.SCROLL_KEYS:
                if self._content_exceeds_view():
                    self._handle_keyboard_scroll(event)
                return "break"

            # 放行 Left/Right 用于光标水平移动（选区相关场景可能需要）
            if event.keysym in PlatformInputBind.NAVIGATE_KEYS:
                return

            # 拦截任何输入、修改、删除或空隙操作（如 Backspace, Delete, Enter 等）
            return "break"

        self._on_key_press_event.broadcast(event.char, event.keysym)

    def _handle_keyboard_scroll(self, event):
        """在 disabled 状态下手动处理键盘滚动"""
        try:
            keysym = event.keysym
            if keysym == 'Up':
                self._tk_text.yview_scroll(-1, 'units')
            elif keysym == 'Down':
                self._tk_text.yview_scroll(1, 'units')
            elif keysym in ('Page_Up', 'Prior'):
                self._tk_text.yview_scroll(-1, 'pages')
            elif keysym in ('Page_Down', 'Next'):
                self._tk_text.yview_scroll(1, 'pages')
            elif keysym == 'Home':
                self._tk_text.yview_moveto(0.0)
            elif keysym == 'End':
                self._tk_text.yview_moveto(1.0)
            self._on_scroll_event.broadcast(event)
        except tk.TclError:
            pass

    def _on_configure_internal(self, event):
        # 如果是自己 pack/pack_forget 导致的布局变化，只记录尺寸但不触发检查
        w, h = event.width, event.height
        if self._layout_in_progress:
            self._last_text_width = w
            self._last_text_height = h
            return
        # 布局尚未稳定：等待 _tk_text 获得真实高度（> 1px）后标记为已稳定
        if not self._mapped:
            self._last_text_width = w
            self._last_text_height = h
            if h > 1:
                self._mapped = True
                if self._scrollbar_visible is None:
                    self._scrollbar_visible = False
                self._update_scrollbar_state()
            return
        # 只在实际尺寸变化时才检查 scrollbar 状态
        if w == self._last_text_width and h == self._last_text_height:
            return
        self._last_text_width = w
        self._last_text_height = h
        # Configure 驱动的检查只允许「显示」scrollbar，不允许「隐藏」
        # 隐藏只在内容变化时触发，避免布局震荡
        self._update_scrollbar_state(show_only=True)
        self._on_configure_event.broadcast(None)

    def _on_double_click_internal(self, event):
        if self._text_mode == TextMode.Disable:
            return 'break'
        if not self._selectable:
            return 'break'
        if self._text_mode == TextMode.Display and not self._selectable:
            return 'break'
        if self._text_mode == TextMode.Label:
            if not self._content_exceeds_view() and not self._selectable:
                return 'break'
            if not self._selectable:
                return 'break'
        # 托管给原生处理：双击自动精准选词，后续拖动按词优雅流式扩展
        self._on_double_click_event.broadcast(event)

    def _on_triple_click_internal(self, event):
        if self._text_mode == TextMode.Disable:
            return 'break'
        if not self._selectable:
            return 'break'
        if self._text_mode == TextMode.Display and not self._selectable:
            return 'break'
        if self._text_mode == TextMode.Label:
            if not self._content_exceeds_view() and not self._selectable:
                return 'break'
            if not self._selectable:
                return 'break'
        # 托管给原生处理：三击精准选择整行，后续拖动按行流式扩展
        self._on_triple_click_event.broadcast(event)

    def _register_listeners(self):
        self.styles.on_theme_changed.add_listener(self._on_theme_changed_internal)
        self.localization.on_language_changed.add_listener(self._on_language_changed_internal)

    def _unregister_listeners(self):
        self.styles.on_theme_changed.remove_listener(self._on_theme_changed_internal)
        self.localization.on_language_changed.remove_listener(self._on_language_changed_internal)

    def _on_theme_changed_internal(self, theme):
        self._config_styles()
        self.refresh()

    def _on_language_changed_internal(self, language):
        if self._text is not None:
            self.set_text(self._text)

    def _unbind_internal_events(self):
        for widget, sequence, funcid in self._internal_bind_ids:
            try:
                widget.unbind(sequence, funcid)
            except:
                pass
        self._internal_bind_ids.clear()

    def _bind_global_click(self):
        """绑定全局点击事件：当点击组件外部时清除选区（参考 entry.py）"""
        if not self._is_global_click_bound:
            self._global_click_id = self._tk_frame.bind_all('<Button-1>', self._on_global_click, add='+')
            self._is_global_click_bound = True

    def _unbind_global_click(self):
        """解绑全局点击事件"""
        if self._is_global_click_bound:
            try:
                if self._global_click_id:
                    self._tk_frame.unbind_all('<Button-1>', funcid=self._global_click_id)
                    self._global_click_id = None
            except:
                pass
            self._is_global_click_bound = False

    def _update_global_click_binding(self):
        """根据当前模式和可选择状态决定是否绑定全局点击事件
        只有当组件可能产生选区时才需要监听全局点击"""
        if self._text_mode == TextMode.Disable or not self._selectable:
            self._unbind_global_click()
        else:
            self._bind_global_click()

    def _on_global_click(self, event):
        """全局点击回调：点击组件外部时清除选区"""
        try:
            if not self._tk_frame.winfo_exists():
                return
            # 不处理自身组件内的点击
            if event.widget in (self._tk_frame, self._tk_text, self._tk_frame_b):
                return
            # 检查是否有选区，有则清除
            try:
                sel_ranges = self._tk_text.tag_ranges('sel')
                if sel_ranges:
                    self._clear_selection()
            except Exception:
                pass
        except tk.TclError:
            pass

    def _on_destroy(self):
        self._unregister_listeners()
        self._unbind_internal_events()
        self._unbind_global_click()
        if self._scrollbar:
            self._scrollbar.destroy()
        super()._on_destroy()

    def set_mode(self, mode):
        if not isinstance(mode, TextMode):
            raise TypeError("mode 参数必须 be TextMode 枚举类型")
        if mode == self._text_mode:
            return

        self._text_mode = mode

        # 每种模式有自己明确的默认属性
        if mode == TextMode.Normal:
            self._show_frame_decoration = True
            self._selectable = True
        elif mode == TextMode.Readonly:
            self._show_frame_decoration = True
            self._selectable = True
        elif mode == TextMode.Display:
            self._show_frame_decoration = True
            self._selectable = False
        elif mode == TextMode.Label:
            self._show_frame_decoration = False
            self._selectable = False
        # Disable 不改变这两个属性，保持当前值

        if mode in (TextMode.Display, TextMode.Disable) or (mode == TextMode.Label and not self._selectable):
            self._clear_selection()

        if mode in (TextMode.Disable, TextMode.Label):
            if self._has_focus():
                self._deflect_focus()

        self._update_global_click_binding()
        self.refresh()

    def set_disabled(self, disabled):
        self.set_mode(TextMode.Disable if disabled else TextMode.Normal)

    def set_selectable_copyable(self, selectable):
        self._selectable = bool(selectable)
        if not selectable:
            self._clear_selection()
        # Label 模式：selectable 关闭时关闭边框装饰，selectable 打开且有焦点时开启
        if self._text_mode == TextMode.Label:
            if selectable and self._has_focus():
                self._show_frame_decoration = True
            else:
                self._show_frame_decoration = False
        self._update_global_click_binding()
        if self._text_mode in (TextMode.Label, TextMode.Display):
            self.refresh()

    def get_mode(self):
        return self._text_mode

    def set_scrollbar_mode(self, mode):
        if not isinstance(mode, ScrollbarMode):
            raise TypeError("mode 参数必须是 ScrollbarMode 枚举类型")
        self._scrollbar_mode = mode
        self._update_scrollbar_state()

    def set_wrap_mode(self, mode):
        if not isinstance(mode, TextWrapMode):
            raise TypeError("mode 参数必须是 TextWrapMode 枚举类型")
        self._wrap_mode = mode
        self._tk_text.config(wrap=mode.to_tk())

    def is_disabled(self):
        return self._text_mode == TextMode.Disable

    def set_frame_decoration(self, enabled):
        self._show_frame_decoration = bool(enabled)
        self.refresh()

    def refresh(self):
        self._interaction_state = TextInteractionState.Focus if self._has_focus() else TextInteractionState.Idle
        if hasattr(self, '_last_style_key'):
            del self._last_style_key
        if hasattr(self, '_last_struct_key'):
            del self._last_struct_key
        self._update_styles()
        self._update_scrollbar_state()

    def focus_set(self):
        if self._text_mode == TextMode.Disable:
            return
        if self._text_mode == TextMode.Label:
            if not self._content_exceeds_view():
                return
        self._tk_frame.focus_set()

    def tag_configure(self, tagName, **kwargs):
        self._tk_text.tag_configure(tagName, **kwargs)

    def tag_add(self, tagName, index1, index2=None):
        curr_state = self._tk_text.cget('state')
        if curr_state == 'disabled':
            self._tk_text.config(state='normal')
            self._tk_text.tag_add(tagName, index1, index2)
            self._tk_text.config(state='disabled')
        else:
            self._tk_text.tag_add(tagName, index1, index2)

    def tag_remove(self, tagName, index1, index2=None):
        curr_state = self._tk_text.cget('state')
        if curr_state == 'disabled':
            self._tk_text.config(state='normal')
            self._tk_text.tag_remove(tagName, index1, index2)
            self._tk_text.config(state='disabled')
        else:
            self._tk_text.tag_remove(tagName, index1, index2)

    def tag_delete(self, tagName):
        curr_state = self._tk_text.cget('state')
        if curr_state == 'disabled':
            self._tk_text.config(state='normal')
            self._tk_text.tag_delete(tagName)
            self._tk_text.config(state='disabled')
        else:
            self._tk_text.tag_delete(tagName)

    def tag_raise(self, tagName, aboveThis=None):
        self._tk_text.tag_raise(tagName, aboveThis)

    def tag_lower(self, tagName, belowThis=None):
        self._tk_text.tag_lower(tagName, belowThis)

    def tag_names(self, index=None):
        return self._tk_text.tag_names(index)

    def tag_ranges(self, tagName):
        return self._tk_text.tag_ranges(tagName)

    def get(self, index1, index2=None):
        return self._tk_text.get(index1, index2)

    def insert(self, index, text):
        curr_state = self._tk_text.cget('state')
        if curr_state == 'disabled':
            self._tk_text.config(state='normal')
            self._tk_text.insert(index, text)
            self._tk_text.config(state='disabled')
        else:
            self._tk_text.insert(index, text)

    def delete(self, index1, index2=None):
        curr_state = self._tk_text.cget('state')
        if curr_state == 'disabled':
            self._tk_text.config(state='normal')
            self._tk_text.delete(index1, index2)
            self._tk_text.config(state='disabled')
        else:
            self._tk_text.delete(index1, index2)

    def set_text(self, text):
        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")

        self._text = text
        display_text = text.get_text() if text else ""

        current_state = self._tk_text.cget('state')
        if current_state == 'disabled':
            self._tk_text.config(state='normal')
        self._tk_text.delete('1.0', tk.END)
        self._tk_text.insert('1.0', display_text)
        self._tk_text.edit_modified(False)
        if current_state == 'disabled':
            self._tk_text.config(state='disabled')

    def see(self, index):
        return self._tk_text.see(index)

    def index(self, index):
        return self._tk_text.index(index)

    def get_line_count(self):
        try:
            result = self._tk_text.count('1.0', 'end', 'displaylines')
            if isinstance(result, tuple):
                return result[0] if result else 1
            return result if result else 1
        except tk.TclError:
            return 1

    def get_content_text(self):
        try:
            return self._tk_text.get('1.0', 'end-1c')
        except tk.TclError:
            return ""

    def get_height_for_lines(self, lines):
        """测量指定行数所需的像素高度（不改变组件状态，仅返回测量值）"""
        if not self._tk_text:
            return 0
        import tkinter.font as tkfont
        font_obj = tkfont.Font(font=self._tk_text.cget('font'))
        line_height_px = font_obj.metrics('linespace')
        # tk.Text 的 pady 会在上下各加一份
        text_pady = int(self._tk_text.cget('pady'))
        frame_pady = self._pady
        # 总像素高度 = 行高 * 行数 + text内部pady*2 + frame_b的pady*2
        return line_height_px * int(lines) + text_pady * 2 + frame_pady * 2

