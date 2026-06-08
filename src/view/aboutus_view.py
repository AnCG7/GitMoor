import veiltk as vk
from src.view.base_view import BaseView
from src.viewmodel.aboutus_viewmodel import AboutViewModel
from src.utils.utils import Utils, AppFont


class AboutView(BaseView):
    def __init__(self, parent):
        self.about_viewmodel = AboutViewModel()

        super().__init__(parent)

    def on_create(self):
        self._create_content()

    def _create_content(self):
        about_content = self.about_viewmodel.get_about_content()
        title_font = AppFont.TITLE

        summary_title = vk.Label(self, text=vk.LocalizedText("software_summary_title"), font=title_font)
        summary_title.pack(anchor='w', pady=10, padx=20)

        software_summary = vk.Label(self, text=about_content["software_summary"], responsive_wrap=True, justify='left')
        software_summary.pack(fill='x', pady=5, padx=20)

        system_title = vk.Label(self, text=vk.LocalizedText("system_requirements_title"), font=title_font)
        system_title.pack(anchor='w', pady=10, padx=20)

        system_requirements = vk.Label(self, text=about_content["system_requirements"], responsive_wrap=True, justify='left')
        system_requirements.pack(fill='x', pady=5, padx=20)

        link_title = vk.Label(self, text=vk.LocalizedText("repository_link_title"), font=title_font)
        link_title.pack(anchor='w', pady=10, padx=20)

        link_text = about_content["repository_link"].get_text()
        description, url = Utils.parse_markdown_link(link_text)
        if description and url:
            repository_link = vk.LinkButton(self, text=vk.LocalizedText(description), url=url)
            repository_link.pack(anchor='w', pady=5, padx=20)

        reference_title = vk.Label(self, text=vk.LocalizedText("reference_links_title"), font=title_font)
        reference_title.pack(anchor='w', pady=5, padx=20)

        gitignore_link = about_content["gitignore_template_link"].get_text()
        description, url = Utils.parse_markdown_link(gitignore_link)
        if description and url:
            gitignore_link_button = vk.LinkButton(self, text=vk.LocalizedText(description), url=url)
            gitignore_link_button.pack(anchor='w', pady=2, padx=20)

        gitattributes_link = about_content["gitattributes_template_link"].get_text()
        description, url = Utils.parse_markdown_link(gitattributes_link)
        if description and url:
            gitattributes_link_button = vk.LinkButton(self, text=vk.LocalizedText(description), url=url)
            gitattributes_link_button.pack(anchor='w', pady=2, padx=20)

    def on_destroy(self):
        pass
