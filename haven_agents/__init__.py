"""
Compatibility shim so the hyphenated `haven-agents` source directory can be
imported as the canonical `haven_agents` package.
"""

from __future__ import annotations

import sys
from pathlib import Path

_hyphenated_dir = Path(__file__).resolve().parent.parent / "haven-agents"
if not _hyphenated_dir.is_dir():
    raise ImportError("Expected sibling directory 'haven-agents' for shimmed package.")

# Redirect this package's module search path to the actual implementation folder.
__path__ = [str(_hyphenated_dir)]
__all__: list[str] = []

# Ensure direct imports such as `from models import ...` continue to resolve.
if str(_hyphenated_dir) not in sys.path:
    sys.path.insert(0, str(_hyphenated_dir))
