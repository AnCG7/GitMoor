"""
路径解析工具 - 兼容开发环境和 PyInstaller 打包环境。

打包后的目录结构（--onedir + --contents-directory=_runtime）：
  GitMoor/
    ├── GitMoor.exe
    ├── app_setting.json       ← 用户可修改
    ├── assets/                ← 用户可修改
    ├── veiltk/assets/         ← 用户可修改
    └── _runtime/              ← Python 运行时（sys._MEIPASS 指向这里）

资源文件放在 EXE 同级目录，而不是 _runtime/ 内部，
这样用户可以直接修改第一层的资源文件。

  - sys._MEIPASS 指向 _runtime/ 目录（只含 Python 内部文件）
  - sys.executable 指向 EXE 所在目录（资源文件在此）
"""
import os
import sys


def get_base_path():
    """获取应用资源根目录。

    开发环境：返回项目根目录（main.py 所在目录）。
    PyInstaller 打包：返回 EXE 所在目录，
    因为 assets/、app_setting.json 等资源文件都在 EXE 同级的第一层。
    """
    if getattr(sys, 'frozen', False):
        # 资源文件在 EXE 同级目录，而不是 _runtime/ 中
        return os.path.dirname(sys.executable)
    else:
        # path_helper.py 位于 src/utils/，向上 3 层到项目根目录
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_user_data_path():
    """获取用户数据可写目录。

    开发环境：返回项目根目录。
    PyInstaller 打包：返回 EXE 所在目录，用于存放运行时生成的用户数据。
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
