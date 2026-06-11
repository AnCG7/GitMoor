"""
平台检测工具类。

提供跨平台的系统检测方法，用于条件绑定等场景。
"""

import sys


class PlatformInfo:
    """平台检测（无状态静态工具类）"""

    # 平台缓存（类变量，只计算一次）
    _platform: str = sys.platform

    # ─── 平台检测 ─────────────────────────────────────────────────────────

    @staticmethod
    def is_windows() -> bool:
        """当前是否为 Windows 平台"""
        return PlatformInfo._platform == 'win32'

    @staticmethod
    def is_macos() -> bool:
        """当前是否为 macOS 平台"""
        return PlatformInfo._platform == 'darwin'

    @staticmethod
    def is_linux() -> bool:
        """当前是否为 Linux 平台"""
        return PlatformInfo._platform.startswith('linux')
