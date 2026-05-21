"""Top-level package for deluge_cmd."""

__author__ = """Chris B Chamberlain"""
__email__ = 'chrisbc@artisan.co.nz'
from ._version import __version__
from .config import API_KEY, API_URL, S3_URL
from .toshi_file import ToshiFile
