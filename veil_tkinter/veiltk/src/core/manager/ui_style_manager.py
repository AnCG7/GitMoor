import json
import os
import tkinter as tk
from .event_manager import Event
from ..utils.utils import Utils
from ..utils.asset_loader import AssetLoader


class UIStyleManager:
    _instance = None

    def __new__(cls, default_theme="light"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, default_theme="light"):
        if self._initialized:
            return
        self._initialized = True

        self.supported_themes = ["light", "dark"]
        self.default_theme = default_theme

        self._DEFAULT_PADX = 5
        self._DEFAULT_PADY = 5

        self._font = Font()

        self._size_presets = {
            'small': {'padx': 8, 'pady': 4},
            'normal': {'padx': 12, 'pady': 6},
            'large': {'padx': 16, 'pady': 8},
        }

        self._theme = self.default_theme
        
        self._raw_styles = {}
        self._processed_styles_cache = {}
        self._precomputed_bg = ""
        
        self._load_styles()
        self._load_components_config()
        self.on_theme_changed = Event()

    def get_size_preset(self, size_key):
        return self._size_presets.get(size_key, self._size_presets['normal'])

    def _load_styles(self):
        styles_dir = AssetLoader.get_asset_path("assets", "styles")
        if self._theme == "dark":
            style_file = os.path.join(styles_dir, "dark.json")
        else:
            style_file = os.path.join(styles_dir, "light.json")

        with open(style_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self._raw_styles = data.get("colors", {})
            
            if self._raw_styles:
                original_bg = self._raw_styles.get("bg_color", "#ffffffff")
                bg_alpha = Utils.hex_to_alpha(original_bg)
                self._precomputed_bg = Utils.blend_color("#000000", original_bg, bg_alpha)
                self._processed_styles_cache["bg_color"] = self._precomputed_bg
            else:
                self._precomputed_bg = "#ffffff"
                self._processed_styles_cache["bg_color"] = "#ffffff"

    def _process_color(self, color_key):
        if color_key in self._processed_styles_cache:
            return self._processed_styles_cache[color_key]
        
        if color_key not in self._raw_styles:
            return ""
        
        color = self._raw_styles[color_key]
        alpha = Utils.hex_to_alpha(color)
        processed_color = Utils.blend_color(self._precomputed_bg, color, alpha)
        
        self._processed_styles_cache[color_key] = processed_color
        return processed_color

    def _load_components_config(self):
        components_file = AssetLoader.get_asset_path("assets", "styles", "components.json")
        with open(components_file, 'r', encoding='utf-8') as f:
            components_config = json.load(f)

        self._style_root = StyleRoot(components_config, self, self._font)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def scale_image(self, img, scale):
        width = img.width()
        height = img.height()
        new_width = int(width * scale)
        new_height = int(height * scale)

        scaled = tk.PhotoImage(width=new_width, height=new_height)

        for y in range(new_height):
            for x in range(new_width):
                orig_x = int(x / scale)
                orig_y = int(y / scale)
                orig_x = min(orig_x, width - 1)
                orig_y = min(orig_y, height - 1)

                color = img.get(orig_x, orig_y)

                if isinstance(color, tuple):
                    if len(color) >= 3:
                        color_str = f'#{color[0]:02x}{color[1]:02x}{color[2]:02x}'
                        scaled.put(color_str, (x, y))
                else:
                    scaled.put(color, (x, y))

        return scaled

    def get_styles(self):
        return self._raw_styles.keys()

    def set_theme(self, theme):
        if theme != self._theme:
            self._theme = theme
            self._raw_styles = {}
            self._processed_styles_cache = {}
            self._precomputed_bg = ""
            self._load_styles()
            self._load_components_config()
            self.on_theme_changed.broadcast(theme)

    def get_theme(self):
        return self._theme


    def set_default_theme(self, default_theme):
        if not hasattr(self, '_theme') or not self._theme:
            self.default_theme = default_theme
            self._theme = self.default_theme
            self._load_styles()
            self._load_components_config()

    def get_style(self, style_name=None):
        if style_name:
            return self._process_color(style_name)
        return self._style_root

    def get_default_pad(self, axis=None):
        if axis == 'x':
            return self._DEFAULT_PADX
        elif axis == 'y':
            return self._DEFAULT_PADY
        return (self._DEFAULT_PADX, self._DEFAULT_PADY)

    def get_font_by_size(self, size_key):
        font_map = {
            'small': self._font.small,
            'normal': self._font.normal,
            'large': self._font.large
        }
        return font_map.get(size_key, self._font.normal)

    def get_pad_by_size(self, size_key, axis=None):
        preset = self.get_size_preset(size_key)
        if axis == 'x':
            return preset['padx']
        elif axis == 'y':
            return preset['pady']
        return (preset['padx'], preset['pady'])

    def apply_style(self, widget, style_dict):
        for style, value in style_dict.items():
            if hasattr(widget, f"{style}_variable"):
                getattr(widget, f"{style}_variable").set(value)
            elif hasattr(widget, f"{style}"):
                setattr(widget, f"{style}", value)


class Style:
    def __init__(self, config, style_manager):
        self.config = config
        self.style_manager = style_manager
        self._init_sub_styles()

    def _init_sub_styles(self):
        if isinstance(self.config, dict):
            for key, value in self.config.items():
                if isinstance(value, (dict, str)):
                    setattr(self, key, Style(value, self.style_manager))

    @property
    def color(self):
        if isinstance(self.config, str):
            return self.style_manager.get_style(self.config)
        return ""

    def get_style_color(self, *path):
        current = self.config
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return ""

        if isinstance(current, str):
            return self.style_manager.get_style(current)
        return ""


class StyleObject:
    def __init__(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    setattr(self, key, StyleObject(value))
                else:
                    setattr(self, key, value)
        else:
            self.value = data

    def __getattr__(self, name):
        return ""


class Font:
    def __init__(self):
        self.small = ("Arial", 4)
        self.normal = ("Arial", 10)
        self.large = ("Arial", 12)
        self.large_bold = ("Arial", 12, "bold")
        self.title = ("Arial", 14, "bold")
        self.link = ("Arial", 10)


class StyleRoot:
    def __init__(self, components_config, style_manager, font):
        self.component = Style(components_config, style_manager)
        self.font = font