import os
import sys
import tkinter as tk

class AssetLoader:
    _instance = None

    def __new__(cls, base_path=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, base_path=None):
        if self._initialized:
            return
        self._initialized = True

        # 基础路径
        if base_path:
            self.base_path = base_path
        elif getattr(sys, 'frozen', False):
            # PyInstaller 打包后，veiltk/assets/ 在 EXE 同级目录
            self.base_path = os.path.join(os.path.dirname(sys.executable), "veiltk")
        else:
            # 开发环境：__file__ = veiltk/src/core/utils/asset_loader.py，向上 4 层到 veiltk/
            self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

        # 默认资源目录
        self.assets_dir = os.path.join(self.base_path, "assets")
        self.images_dir = os.path.join(self.assets_dir, "images")
        self.theme_dir = os.path.join(self.images_dir, "theme")

    @classmethod
    def get_instance(cls, base_path=None):
        if cls._instance is None:
            cls._instance = cls(base_path)
        return cls._instance

    @classmethod
    def set_base_path(cls, base_path):
        """设置基础路径"""
        inst = cls.get_instance()
        if base_path != inst.base_path:
            inst.base_path = base_path
            inst.assets_dir = os.path.join(inst.base_path, "assets")
            inst.images_dir = os.path.join(inst.assets_dir, "images")
            inst.theme_dir = os.path.join(inst.images_dir, "theme")

    @classmethod
    def get_asset_path(cls, *path_parts):
        """获取资源路径

        Args:
            *path_parts: 路径部分，如 "images", "theme", "checkbutton_checkmark.png"

        Returns:
            str: 完整的资源路径
        """
        return os.path.join(cls.get_instance().base_path, *path_parts)

    @classmethod
    def get_image_path(cls, *path_parts):
        """获取图片路径

        Args:
            *path_parts: 路径部分，如 "theme", "checkbutton_checkmark.png"

        Returns:
            str: 完整的图片路径
        """
        return os.path.join(cls.get_instance().images_dir, *path_parts)

    @classmethod
    def get_theme_image_path(cls, filename):
        """获取主题图片路径

        Args:
            filename: 图片文件名

        Returns:
            str: 完整的主题图片路径
        """
        return os.path.join(cls.get_instance().theme_dir, filename)

    @classmethod
    def load_image(cls, path, **kwargs):
        """加载图片

        Args:
            path: 图片路径
            **kwargs: 传递给 tk.PhotoImage 的参数

        Returns:
            tk.PhotoImage: 图片对象
        """
        try:
            return tk.PhotoImage(file=path, **kwargs)
        except Exception as e:
            print(f"加载图片失败: {e}")
            return None

    @classmethod
    def load_theme_image(cls, filename, **kwargs):
        """加载主题图片

        Args:
            filename: 图片文件名
            **kwargs: 传递给 tk.PhotoImage 的参数

        Returns:
            tk.PhotoImage: 图片对象
        """
        image_path = cls.get_theme_image_path(filename)
        return cls.load_image(image_path, **kwargs)

    @classmethod
    def load_json(cls, path):
        """加载 JSON 文件

        Args:
            path: JSON 文件路径

        Returns:
            dict: JSON 数据
        """
        try:
            import json
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载 JSON 文件失败: {e}")
            return {}

    @classmethod
    def load_text(cls, path):
        """加载文本文件

        Args:
            path: 文本文件路径

        Returns:
            str: 文本内容
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"加载文本文件失败: {e}")
            return ""
