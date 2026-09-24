from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional, Union
import json


@dataclass
class LiveDataSnapshot:
    provider: str
    kind: str
    scope: Union[str, Dict[str, Any]]
    status: str
    fetched_at: str
    expires_at: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    source_url: Optional[str] = None
    error_code: Optional[str] = None
    notice: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def __contains__(self, item: str) -> bool:
        return hasattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def __str__(self) -> str:
        return self.to_json()
