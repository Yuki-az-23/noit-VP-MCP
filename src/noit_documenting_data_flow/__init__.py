"""
NOit Documenting Data Flow

STAR diagram pieces → interactive viewer + overview.
Architecture documentation that stays in sync.

Author: NOit (https://noit2.com)
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("noit-documenting-data-flow")
except PackageNotFoundError:  # running from a source tree without installing
    __version__ = "0+unknown"
__author__ = "NOit"
__email__ = "hello@noit2.com"
__url__ = "https://noit2.com"
