from abc import ABC as AbstractBaseClass, abstractmethod

class BaseViewModel(AbstractBaseClass):
    """
    ViewModel 基类
    提供基础的生命周期支持
    """
    
    def __init__(self):
        self._is_destroyed = False
    
    def destroy(self):
        """
        销毁 ViewModel，清理所有资源
        
        子类可以重写此方法，但应该调用 super().destroy()
        """
        self._is_destroyed = True
    
    @property
    def is_destroyed(self):
        """检查 ViewModel 是否已销毁"""
        return self._is_destroyed
