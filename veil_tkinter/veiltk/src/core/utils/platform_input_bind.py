"""
跨平台输入事件绑定助手类。

提供统一的跨平台键盘/鼠标事件绑定方法，屏蔽 Windows/macOS/Linux 之间的差异：
- Tab 变体全量绑定（兼容 Linux ISO_Left_Tab）
- 鼠标滚轮条件绑定 + delta 归一化
"""

from .platform_info import PlatformInfo


class PlatformInputBind:
    """跨平台输入事件绑定助手（无状态静态工具类）"""

    # ─── 跨平台 keysym 常量集合 ──────────────────────────────────────────
    # 用于统一的按键拦截/放行判断，屏蔽各平台 keysym 差异

    SCROLL_KEYS = ('Up', 'Down', 'Page_Up', 'Page_Down', 'Home', 'End', 'Prior', 'Next')
    """滚动/翻页导航键"""

    MODIFIER_KEYS = (
        'Control_L', 'Control_R',
        'Shift_L', 'Shift_R',
        'Alt_L', 'Alt_R',
        'Super_L', 'Super_R',      # macOS Command 键（部分 Tk 版本报告为 Super）
        'Command_L', 'Command_R',  # macOS Command 键（部分 Tk 版本报告为 Command）
    )
    """修饰键（单独按下时不应被拦截）"""

    NAVIGATE_KEYS = ('Left', 'Right')
    """水平光标移动键"""

    # ─── Tab 变体绑定（全量绑定策略） ──────────────────────────────────────

    @staticmethod
    def bind_shift_tab(widget, callback, add='+') -> list:
        """
        绑定 Shift+Tab 事件（全量绑定策略）。

        同时绑定 <Shift-Tab> 和 <ISO_Left_Tab>（Linux 兼容），
        不触发的事件无副作用。

        Args:
            widget: Tkinter 组件
            callback: 回调函数，签名 callback(event)
            add: 绑定模式，默认 '+' 追加

        Returns:
            list: [(widget, event_name, bind_id), ...] 兼容 _internal_bind_ids
        """
        bind_ids = []
        for event_name in ('<Shift-Tab>', '<ISO_Left_Tab>'):
            bid = widget.bind(event_name, callback, add=add)
            bind_ids.append((widget, event_name, bid))
        return bind_ids

    @staticmethod
    def bind_ctrl_shift_tab(widget, callback, add='+') -> list:
        """
        绑定 Ctrl+Shift+Tab 事件（全量绑定策略）。

        同时绑定 <Control-Shift-Tab> 和 <Control-ISO_Left_Tab>（Linux 兼容）。

        Args:
            widget: Tkinter 组件
            callback: 回调函数，签名 callback(event)
            add: 绑定模式，默认 '+' 追加

        Returns:
            list: [(widget, event_name, bind_id), ...] 兼容 _internal_bind_ids
        """
        bind_ids = []
        for event_name in ('<Control-Shift-Tab>', '<Control-ISO_Left_Tab>'):
            bid = widget.bind(event_name, callback, add=add)
            bind_ids.append((widget, event_name, bid))
        return bind_ids

    # ─── 鼠标滚轮绑定（条件绑定策略） ────────────────────────────────────

    @staticmethod
    def bind_mousewheel(widget, callback, add='+') -> list:
        """
        绑定鼠标滚轮事件（条件绑定策略 + delta 归一化）。

        - Windows/macOS: 绑定 <MouseWheel>，delta 归一化为 +1/-1
        - Linux: 绑定 <Button-4>（向上）和 <Button-5>（向下）

        回调签名: callback(event, delta: int)
            delta > 0: 向上滚动
            delta < 0: 向下滚动

        Args:
            widget: Tkinter 组件
            callback: 回调函数，签名 callback(event, delta: int)
            add: 绑定模式，默认 '+' 追加

        Returns:
            list: [(widget, event_name, bind_id), ...] 兼容 _internal_bind_ids
        """
        bind_ids = []

        if PlatformInfo.is_linux():
            # Linux: Button-4 向上, Button-5 向下
            def _on_button4(event, cb=callback):
                return cb(event, 1)

            def _on_button5(event, cb=callback):
                return cb(event, -1)

            bid4 = widget.bind('<Button-4>', _on_button4, add=add)
            bind_ids.append((widget, '<Button-4>', bid4))

            bid5 = widget.bind('<Button-5>', _on_button5, add=add)
            bind_ids.append((widget, '<Button-5>', bid5))
        else:
            # Windows / macOS: MouseWheel 事件，归一化 delta
            def _on_mousewheel(event, cb=callback):
                if PlatformInfo.is_windows():
                    # Windows: event.delta 为 ±120 的倍数
                    delta = 1 if event.delta > 0 else -1
                else:
                    # macOS: event.delta 为 ±1 (或更大的整数)
                    delta = 1 if event.delta > 0 else -1
                return cb(event, delta)

            bid = widget.bind('<MouseWheel>', _on_mousewheel, add=add)
            bind_ids.append((widget, '<MouseWheel>', bid))

        return bind_ids

    @staticmethod
    def unbind_mousewheel(widget) -> None:
        """
        解除鼠标滚轮事件绑定（便捷方法）。

        根据平台解绑对应的事件。
        """
        if PlatformInfo.is_linux():
            widget.unbind('<Button-4>')
            widget.unbind('<Button-5>')
        else:
            widget.unbind('<MouseWheel>')
