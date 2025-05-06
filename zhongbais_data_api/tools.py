from typing import Callable, Any, Optional, List, Dict


class ObservableDict(dict):
    """
    带两类回调的字典：
    1. 数据变更回调（原来的）：cb(key, old, new, action)
    2. key 列表变更回调：key_cb(current_keys: List[str])
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._callbacks: List[Callable[[Dict[str, str]], None]] = []
        self._key_callbacks: List[Callable[[List[str]], None]] = []

    def register_callback(self, cb: Callable[[Dict[str, str]], None]) -> None:
        """注册数据增删改时触发的回调"""
        self._callbacks.append(cb)

    def register_key_callback(self, key_cb: Callable[[List[str]], None]) -> None:
        """注册仅在 key 列表发生变化时触发的回调"""
        self._key_callbacks.append(key_cb)

    def _trigger_key_callbacks(self):
        keys = list(self.keys())
        for key_cb in self._key_callbacks:
            key_cb(keys)

    def __setitem__(self, key: str, value: Any) -> None:
        is_new = key not in self
        old = self.get(key)
        if old == value:
            return
        super().__setitem__(key, value)
        # 数据变更回调
        for cb in self._callbacks:
            cb(self.copy())
        # 如果是新插入键，则触发 key 变更回调
        if is_new:
            self._trigger_key_callbacks()

    def __delitem__(self, key: str) -> None:
        if key not in self:
            return
        super().__delitem__(key)
        # 数据删除回调
        for cb in self._callbacks:
            cb(self.copy())
        # key 列表变更回调
        self._trigger_key_callbacks()

    def pop(self, key: str, default: Optional[Any] = None) -> Any:
        if key in self:
            val = super().pop(key)
            for cb in self._callbacks:
                cb(self.copy())
            self._trigger_key_callbacks()
            return val
        return default

    def update(self, *args, **kwargs) -> None:
        for k, v in dict(*args, **kwargs).items():
            # 利用 __setitem__ 自动处理新旧、回调和 key 变更
            self.__setitem__(k, v)
