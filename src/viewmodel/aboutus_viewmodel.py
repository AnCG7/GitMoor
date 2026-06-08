import veiltk as vk
from src.viewmodel.base_viewmodel import BaseViewModel


class AboutViewModel(BaseViewModel):
    def __init__(self):
        super().__init__()
    
    def get_about_content(self):
        return {
            "software_summary": vk.LocalizedText("software_summary"),
            "system_requirements": vk.LocalizedText("system_requirements"),
            "repository_link": vk.LocalizedText("repository_link"),
            "gitignore_template_link": vk.LocalizedText("gitignore_template_link"),
            "gitattributes_template_link": vk.LocalizedText("gitattributes_template_link")
        }
    
