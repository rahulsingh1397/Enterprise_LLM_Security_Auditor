"""
Abstract base class for all security scanners.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseScanner(ABC):
    name: str = "BaseScanner"
    category: str = "generic"

    @property
    @abstractmethod
    def attacks(self) -> List[Dict[str, Any]]:
        """Return list of attack dicts: [{name, prompt, expected_behavior}]."""
        ...
