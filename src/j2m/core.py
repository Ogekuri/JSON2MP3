"""Compatibility module for the renamed skeleton package.

The public distribution package is :mod:`json2mp3`; this module keeps imports
from the short project skeleton name working during local development.
"""

from json2mp3.core import main

__all__ = ["main"]
