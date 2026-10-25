"""Convert WordPress / Squarespace XML exports into Zensical sites."""

from importlib.metadata import version

from .config import ConfigError
from .convert import convert_site

__version__ = version("quaternionspace")
__all__ = ["ConfigError", "__version__", "convert_site"]
