import tkinter as tk
from enum import Enum
from ..core.view import View
from ..core.manager.ui_style_manager import UIStyleManager
from ..core.manager.event_manager import Event
from ..core.manager.localization_manager import LocalizedText
from .frame import Frame
from .button import Button


class MenuPosition(Enum):
    Left = "left"
    Top = "top"


class PageMode(Enum):
    Cache = "cache"
    Destroy = "destroy"


class MenuButton(Button):
    def __init__(self, master=None, text=None, selected=False, **kwargs):
        if text is not None and not isinstance(text, LocalizedText):
            raise TypeError("text 参数必须是 LocalizedText 类型")
        self.selected = selected
        super().__init__(master, text=text, **kwargs)

    def _config_styles(self):
        current_style = self.styles.get_style()

        if self.selected:
            return {
                "bg": current_style.component.menu.button.active.bg.color,
                "fg": current_style.component.menu.button.active.fg.color,
                "activebackground": current_style.component.menu.button.active.bg.color,
                "activeforeground": current_style.component.menu.button.active.fg.color,
                "hover_bg": current_style.component.menu.button.active.bg.color,
                "hover_fg": current_style.component.menu.button.active.fg.color,
                "focus_bg": current_style.component.menu.button.focus.bg.color,
                "focus_fg": current_style.component.menu.button.focus.fg.color,
                "disable_bg": current_style.component.menu.button.disable.bg.color,
                "disable_fg": current_style.component.menu.button.disable.fg.color,
                "border": current_style.component.menu.button.active.border.color,
                "hover_border": current_style.component.menu.button.active.border.color,
                "press_border": current_style.component.menu.button.active.border.color,
                "focus_border": current_style.component.menu.button.focus.border.color,
                "disable_border": current_style.component.menu.button.disable.border.color
            }
        else:
            return {
                "bg": current_style.component.menu.button.normal.bg.color,
                "fg": current_style.component.menu.button.normal.fg.color,
                "activebackground": current_style.component.menu.button.press.bg.color,
                "activeforeground": current_style.component.menu.button.press.fg.color,
                "hover_bg": current_style.component.menu.button.hover.bg.color,
                "hover_fg": current_style.component.menu.button.hover.fg.color,
                "focus_bg": current_style.component.menu.button.focus.bg.color,
                "focus_fg": current_style.component.menu.button.focus.fg.color,
                "disable_bg": current_style.component.menu.button.disable.bg.color,
                "disable_fg": current_style.component.menu.button.disable.fg.color,
                "border": current_style.component.menu.button.normal.border.color,
                "hover_border": current_style.component.menu.button.hover.border.color,
                "press_border": current_style.component.menu.button.press.border.color,
                "focus_border": current_style.component.menu.button.focus.border.color,
                "disable_border": current_style.component.menu.button.disable.border.color
            }

    def set_selected(self, selected):
        self.selected = selected
        self.refresh_theme()

    def _apply_style(self):
        super()._apply_style()

        if self._disabled:
            border = self._button_style.get("disable_border", self._button_style.get("border", "#000000"))
        elif self._pressed:
            border = self._button_style.get("press_border", self._button_style.get("border", "#000000"))
        elif self._focused:
            border = self._button_style.get("focus_border", self._button_style.get("border", "#000000"))
        elif self._hovered:
            border = self._button_style.get("hover_border", self._button_style.get("border", "#000000"))
        else:
            border = self._button_style.get("border", "#000000")

        self._tk_label.config(
            relief=tk.FLAT,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=border,
            highlightcolor=border
        )


class Menu(Frame):
    def __init__(self, master=None, menu_items=None, position=MenuPosition.Left, 
                 page_mode=PageMode.Cache, initial_item_index=None, 
                 menu_width=180, menu_height=56, **kwargs):
        if not isinstance(position, MenuPosition):
            raise TypeError("position 参数必须是 MenuPosition 枚举类型")
        if not isinstance(page_mode, PageMode):
            raise TypeError("page_mode 参数必须是 PageMode 枚举类型")
        
        self.styles = UIStyleManager.get_instance()
        self._disabled = False

        default_kwargs = {
            "bg": self.styles.get_style().component.frame.bg.color
        }
        default_kwargs.update(kwargs)

        super().__init__(master, **default_kwargs)

        self.menu_items = menu_items if menu_items else []
        self.position = position
        self.page_mode = page_mode
        self.menu_width = menu_width
        self.menu_height = menu_height

        self.on_select = Event()

        self.menu_buttons = {}
        self.pages = {}
        self.current_page_instance = None
        self.current_selected_index = None

        self._create_layout()
        self._create_menu_and_pages()

        initial_index = 0
        if initial_item_index is not None and 0 <= initial_item_index < len(self.menu_items):
            initial_index = initial_item_index

        if self.menu_items:
            self.select_item(initial_index)

    def refresh_theme(self):
        super().refresh_theme()
        border_color = self.styles.get_style().component.menu.border.color
        self.side_border.config(bg=border_color)

    def _create_layout(self):
        self.menu_frame = Frame(self)
        self.main_area = Frame(self)

        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.config(padx=8, pady=10)

        border_color = self.styles.get_style().component.menu.border.color

        if self.position == MenuPosition.Left:
            self.menu_frame.config(width=self.menu_width)
            self.menu_frame.pack_propagate(False)
            self.menu_frame.pack(side=tk.LEFT, fill=tk.Y)
            self.side_border = tk.Frame(self._root_tk, bg=border_color, width=1)
            self.side_border.pack(side=tk.LEFT, fill=tk.Y)
            self.main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        elif self.position == MenuPosition.Top:
            self.menu_frame.config(height=self.menu_height)
            self.menu_frame.pack_propagate(False)
            self.menu_frame.pack(side=tk.TOP, fill=tk.X)
            self.side_border = tk.Frame(self._root_tk, bg=border_color, height=1)
            self.side_border.pack(side=tk.TOP, fill=tk.X)
            self.main_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _create_menu_and_pages(self):
        for i, item in enumerate(self.menu_items):
            text = item['text']
            disabled = item.get('disabled', False)

            if self.page_mode == PageMode.Cache:
                page_class = item['page']
                page = page_class(self.main_area)
                self.pages[i] = page
                page.grid(row=0, column=0, sticky='nsew')
                page.grid_remove()

            btn_kwargs = {}
            if self.position == MenuPosition.Left:
                btn_kwargs = {'anchor': 'w', 'padx': 20}

            btn = MenuButton(self.menu_frame, text=text, **btn_kwargs)

            if disabled:
                btn.set_disable(True)

            def create_click_handler(idx):
                def handler():
                    self._handle_click(idx)
                return handler

            btn.on_click.add_listener(create_click_handler(i))

            if self.position == MenuPosition.Left:
                btn.pack(fill=tk.X, pady=1, ipady=10)
            else:
                btn.pack(side=tk.LEFT, padx=1, fill=tk.Y, ipadx=15)

            self.menu_buttons[i] = btn

    def _handle_click(self, item_index):
        if self._disabled or item_index == self.current_selected_index:
            return

        if self.menu_items[item_index].get('disabled', False):
            return

        self.select_item(item_index)

    def select_item(self, item_index):
        if not (0 <= item_index < len(self.menu_items)):
            return
        if item_index == self.current_selected_index:
            return
        if self.current_selected_index is not None:
            prev_btn = self.menu_buttons[self.current_selected_index]
            prev_btn.set_selected(False)
            if self.page_mode == PageMode.Cache:
                self.pages[self.current_selected_index].grid_remove()
            elif self.page_mode == PageMode.Destroy:
                if self.current_page_instance:
                    self.current_page_instance.destroy()

        curr_btn = self.menu_buttons[item_index]
        curr_btn.set_selected(True)
        if self.page_mode == PageMode.Cache:
            curr_page = self.pages[item_index]
            curr_page.grid()
        elif self.page_mode == PageMode.Destroy:
            page_class = self.menu_items[item_index]['page']
            curr_page = page_class(self.main_area)
            curr_page.grid(row=0, column=0, sticky='nsew')
            self.current_page_instance = curr_page

        self.current_selected_index = item_index
        self.on_select.broadcast(item_index, self.menu_items[item_index]['text'], curr_page)

    def set_disabled(self, disabled):
        self._disabled = disabled
        for button in self.menu_buttons.values():
            button.set_disabled(disabled)

    def set_item_disable(self, item_index, disabled):
        if 0 <= item_index < len(self.menu_items):
            self.menu_items[item_index]['disabled'] = disabled
            if item_index in self.menu_buttons:
                self.menu_buttons[item_index].set_disabled(disabled)
