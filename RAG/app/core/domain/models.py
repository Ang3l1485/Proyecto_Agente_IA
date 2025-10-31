from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class Chunk:
    id: str
    content: str
    metadata: Optional[Dict[str, str]] = None