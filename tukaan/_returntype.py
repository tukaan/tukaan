from typing import Any, Dict

from .utils import reversed_dict


class Callback:
    ...


class DictKey:
    def __init__(self, dict: Dict[str, Any]):
        self.dictionary = dict

    def __getitem__(self, key: Any) -> Any:
        return reversed_dict(self.dictionary)[key]
