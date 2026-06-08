import json
import os
from .event_manager import Event


class LocalizationManager:
    _instance = None
    
    def __new__(cls, language="zh-Hans", localization_path="localization"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, language="zh-Hans", localization_path="localization"):
        if self._initialized:
            return
        self._initialized = True
        
        self.localization_path = localization_path
        self.supported_languages = self.get_languages()
        self.default_language = "zh-Hans"
        
        self.language = language
        self.strings = self.load_strings()
        self.on_language_changed = Event()
    
    def set_localization_path(self, path):
        if path != self.localization_path:
            self.localization_path = path
            self.supported_languages = self.get_languages()
            self.strings = self.load_strings()
            self.on_language_changed.broadcast(self.language)
    
    @classmethod
    def get_instance(cls, language="zh-Hans", localization_path="localization"):
        if cls._instance is None:
            cls._instance = cls(language, localization_path)
        return cls._instance
    
    def load_strings(self):
        strings_path = os.path.join(self.localization_path, f"{self.language}.json")
        if os.path.exists(strings_path):
            with open(strings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            default_path = os.path.join(self.localization_path, "zh-Hans.json")
            if os.path.exists(default_path):
                with open(default_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
    
    def set_language(self, language):
        if language != self.language:
            self.language = language
            self.strings = self.load_strings()
            self.on_language_changed.broadcast(language)
    
    def get(self, key, default=""):
        return self.strings.get(key, default)
    
    def get_languages(self):
        languages = []
        if os.path.exists(self.localization_path):
            for item in os.listdir(self.localization_path):
                if item.endswith(".json"):
                    language_code = item.replace(".json", "")
                    languages.append(language_code)
        return languages


class LocalizedText:
    class TextType:
        LOCALIZED = 1
        STRING = 2
    
    def __init__(self, text, text_type=TextType.LOCALIZED):
        self.text = text
        self.text_type = text_type
        self._localized_text = None
        
        self.lm = LocalizationManager.get_instance()
        self._update_text()
    
    def _update_text(self):
        if self.text_type == self.TextType.LOCALIZED:
            self._localized_text = self.lm.get(self.text, self.text)
        else:
            self._localized_text = self.text
    
    def get_text(self):
        self._update_text()
        return self._localized_text
    
    def set_text(self, text, text_type=None):
        self.text = text
        if text_type is not None:
            self.text_type = text_type
        self._update_text()
    
    def __str__(self):
        return self.get_text()
    
    def __repr__(self):
        return f"LocalizedText(text='{self.text}', text_type={self.text_type})"
    
    @classmethod
    def format(cls, text):
        return cls(text)