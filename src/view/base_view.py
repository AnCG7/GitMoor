import veiltk as vk


class BaseView(vk.Frame):
    """
    View 基类
    
    继承自 veiltk.Frame，提供完整的界面生命周期管理：
    - on_create(): 创建界面时调用（子类必须实现）
    - on_start(): 界面显示时调用
    - on_stop(): 界面隐藏时调用
    - on_destroy(): 销毁界面时调用
    
    使用方式：
    1. 继承 BaseView
    2. 实现 on_create() 方法创建界面（直接在self上添加组件）
    3. 可选重写 on_start(), on_stop(), on_destroy()
    4. 在 on_destroy() 中调用 remove_event_listeners() 移除监听器
    
    注意：
    - BaseView 本身就是一个 vk.Frame，子类直接在 self 上添加组件
    - 子类不需要创建额外的 frame 容器
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self._is_created = False
        self._is_destroyed = False
        self._vm_listeners = []
        self._frame_listeners = []
        
        self._create()
    
    def _create(self):
        """内部创建方法，调用 on_create"""
        if self._is_created:
            return
        
        self.on_create()
        self._is_created = True
        
        self._bind_lifecycle_events()
    
    def _bind_lifecycle_events(self):
        """绑定生命周期事件"""
        self.on_map.add_listener(self._on_map)
        self.on_unmap.add_listener(self._on_unmap)
    
    def _on_map(self):
        """界面显示事件"""
        if not self._is_destroyed:
            self.on_start()
    
    def _on_unmap(self):
        """界面隐藏事件"""
        if not self._is_destroyed:
            self.on_stop()
    
    def on_create(self):
        """
        创建界面时调用
        
        子类必须实现此方法，在此方法中创建所有 UI 组件
        直接在 self 上添加组件，不需要创建额外的 frame 容器
        """
        pass
    
    def on_start(self):
        """
        界面显示时调用
        
        子类可以重写此方法以执行显示时的逻辑
        默认实现为空
        """
        pass
    
    def on_stop(self):
        """
        界面隐藏时调用
        
        子类可以重写此方法以执行隐藏时的逻辑
        默认实现为空
        """
        pass
    
    def on_destroy(self):
        """
        销毁界面时调用
        
        子类应该重写此方法以：
        1. 移除事件监听器（调用 remove_event_listeners）
        2. 清理其他资源
        
        注意：如果重写此方法，应该调用 super().on_destroy()
        """
        pass
    
    def remove_event_listeners(self):
        """
        移除所有事件监听器
        
        子类应该实现此方法，移除所有注册的事件监听器
        """
        pass
    
    def _register_vm_listener(self, event, callback):
        """
        注册ViewModel事件监听器
        
        Args:
            event: 事件对象（通常是ViewModel的事件属性）
            callback: 回调函数
        """
        event.add_listener(callback)
        self._vm_listeners.append((event, callback))
    
    def _destroy(self):
        """内部销毁方法"""
        if self._is_destroyed:
            return
        
        self._is_destroyed = True
        self.on_destroy()
        self.remove_event_listeners()
        
        # 移除ViewModel事件监听器
        for event, callback in self._vm_listeners:
            try:
                event.remove_listener(callback)
            except:
                pass
        self._vm_listeners.clear()
    
    def destroy(self):
        """公开的销毁方法，供外部调用"""
        try:
            # 先调用内部销毁方法，确保监听器被移除
            self._destroy()
            
            # 然后销毁自己（因为BaseView本身就是Frame）
            super().destroy()
        except Exception as e:
            # 忽略销毁时的错误，因为组件可能已经被销毁
            print(f"销毁视图时出错: {e}")
            pass
    
    def is_exists(self):
        try:
            return self._root_tk is not None and self._root_tk.winfo_exists() and not self._is_destroyed
        except Exception:
            return False
    
    @property
    def is_destroyed(self):
        """检查界面是否已销毁"""
        return self._is_destroyed