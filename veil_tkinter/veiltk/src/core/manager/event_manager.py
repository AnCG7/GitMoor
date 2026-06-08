class Event:
    def __init__(self):
        self._listeners = []
    
    def add_listener(self, callback):
        if callback not in self._listeners:
            self._listeners.append(callback)
    
    def remove_listener(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def broadcast(self, *args, **kwargs):
        for callback in self._listeners:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"事件回调出错: {e}")
    
    def clear(self):
        self._listeners = []


class EventManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._events = {}
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def get_event(self, event_name):
        if event_name not in self._events:
            self._events[event_name] = Event()
        return self._events[event_name]
    
    def add_listener(self, event_name, callback):
        self.get_event(event_name).add_listener(callback)
    
    def remove_listener(self, event_name, callback):
        if event_name in self._events:
            self._events[event_name].remove_listener(callback)
    
    def broadcast(self, event_name, *args, **kwargs):
        if event_name in self._events:
            self._events[event_name].broadcast(*args, **kwargs)
    
    def clear_event(self, event_name):
        if event_name in self._events:
            self._events[event_name].clear()
    
    def clear_all(self):
        for event in self._events.values():
            event.clear()
        self._events = {}
