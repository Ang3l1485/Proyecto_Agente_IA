from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class chunk:
    id: str
    content: str
    metadata: Optional[Dict[str, str]] = None