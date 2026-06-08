import tkinter as tk
from abc import ABC, abstractmethod


class View(ABC):
    def __init__(self, master=None, **kwargs):
        if 'state' in kwargs:
            print(f"错误: 不允许通过 kwargs 设置 state，请使用指定的方法（如 set_disabled()）设置状态")
            kwargs.pop('state')
        if master is not None:
            self._master = self._validate_master(master)
        else:
            self._master = None
        self._root_tk = None
        self._pack_params = None
        self._grid_params = None
        self._place_params = None
        self._hidden = False
        self._init_kwargs = kwargs
        self._loaded = False
        if master is not None:
            root = self._build_widget(self._master, **self._init_kwargs)
            if isinstance(root, View):
                self._root_tk = root._root_tk
            elif isinstance(root, tk.Misc):
                self._root_tk = root
            else:
                raise TypeError("_build_widget must return a tkinter widget or View instance")
            self._loaded = True
            self._destroyed = False
            self._is_appeared = False
            self._bind_map_events()

    @staticmethod
    def _validate_master(master):
        from .application import App
        from .window import Window
        if not isinstance(master, (App, Window, View, tk.Misc)):
            raise TypeError("master 必须是 App, Window, View 或 tkinter 组件类型")
        return master

    def _get_master_tk(self):
        if self._master is None:
            return None
        if isinstance(self._master, tk.Misc):
            return self._master
        return self._master.get_root_tk()

    def get_root_tk(self):
        return self._root_tk

    @abstractmethod
    def _build_widget(self, master=None, **kwargs):
        pass

    def _bind_map_events(self):
        if self._root_tk:
            self._map_callback = lambda e: self._on_appeared()
            self._unmap_callback = lambda e: self._on_disappeared()
            self._map_bind_id = self._root_tk.bind('<Map>', self._map_callback, add='+')
            self._unmap_bind_id = self._root_tk.bind('<Unmap>', self._unmap_callback, add='+')
            self._destroy_bind_id = self._root_tk.bind('<Destroy>', self._on_tk_destroy, add='+')

    def _unbind_map_events(self):
        if self._root_tk:
            try:
                if hasattr(self, '_map_bind_id') and self._map_bind_id:
                    self._root_tk.unbind('<Map>', self._map_bind_id)
                    self._map_bind_id = None
                if hasattr(self, '_unmap_bind_id') and self._unmap_bind_id:
                    self._root_tk.unbind('<Unmap>', self._unmap_bind_id)
                    self._unmap_bind_id = None
                if hasattr(self, '_destroy_bind_id') and self._destroy_bind_id:
                    self._root_tk.unbind('<Destroy>', self._destroy_bind_id)
                    self._destroy_bind_id = None
            except:
                pass

    def _on_appeared(self):
        self._is_appeared = True

    def _on_disappeared(self):
        self._is_appeared = False

    def _on_destroy(self):
        pass

    def _on_tk_destroy(self, event):
        """tk <Destroy> 事件回调，统一处理主动和被动销毁的清理逻辑"""
        if event.widget is not self._root_tk:
            return
        if self._destroyed:
            return
        self._destroyed = True
        self._unbind_map_events()
        # 保证生命周期完整：如果销毁前还在显示状态，先触发 disappeared
        if self._is_appeared:
            self._is_appeared = False
            self._on_disappeared()
        self._on_destroy()
        self._root_tk = None

    def destroy(self):
        if self._destroyed:
            return
        if self._root_tk:
            try:
                self._root_tk.destroy()
            except:
                pass

    def pack(self, **kwargs):
        self._pack_params = kwargs
        self._grid_params = None
        self._place_params = None
        if self._root_tk and not self._hidden:
            self._root_tk.pack(**kwargs)
        return self

    def pack_forget(self):
        if self._root_tk:
            self._root_tk.pack_forget()
            self._pack_params = None

    def grid(self, **kwargs):
        self._grid_params = kwargs
        self._pack_params = None
        self._place_params = None
        if self._root_tk and not self._hidden:
            self._root_tk.grid(**kwargs)
        return self

    def grid_forget(self):
        if self._root_tk:
            self._root_tk.grid_forget()
            self._grid_params = None

    def grid_remove(self):
        if self._root_tk:
            self._root_tk.grid_remove()

    def place(self, **kwargs):
        self._place_params = kwargs
        self._pack_params = None
        self._grid_params = None
        if self._root_tk and not self._hidden:
            self._root_tk.place(**kwargs)
        return self

    def place_forget(self):
        if self._root_tk:
            self._root_tk.place_forget()
            self._place_params = None

    def pack_propagate(self, flag):
        if self._root_tk:
            self._root_tk.pack_propagate(flag)

    def grid_columnconfigure(self, index, **kwargs):
        if self._root_tk:
            self._root_tk.grid_columnconfigure(index, **kwargs)

    def grid_rowconfigure(self, index, **kwargs):
        if self._root_tk:
            self._root_tk.grid_rowconfigure(index, **kwargs)

    def configure(self, *args, **kwargs):
        if 'state' in kwargs:
            print(f"错误: 不允许通过 configure 设置 state，请使用指定的方法（如 set_disabled()）设置状态")
            kwargs.pop('state')
        if self._root_tk:
            return self._root_tk.configure(*args, **kwargs)

    def config(self, *args, **kwargs):
        return self.configure(*args, **kwargs)

    def after(self, delay_ms, callback=None):
        if self._root_tk:
            return self._root_tk.after(delay_ms, callback)

    def after_cancel(self, after_id):
        if self._root_tk and after_id:
            self._root_tk.after_cancel(after_id)

    def hide(self, hidden: bool):
        self._hidden = hidden
        if not self._root_tk:
            return
        if hidden:
            if self._pack_params is not None:
                self._root_tk.pack_forget()
            if self._grid_params is not None:
                self._root_tk.grid_forget()
            if self._place_params is not None:
                self._root_tk.place_forget()
        else:
            if self._pack_params is not None:
                self._root_tk.pack(**self._pack_params)
            elif self._grid_params is not None:
                self._root_tk.grid(**self._grid_params)
            elif self._place_params is not None:
                self._root_tk.place(**self._place_params)
