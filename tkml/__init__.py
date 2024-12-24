"""
A Single-File Library for Using XML to build TKinter applications
"""

from .drivers import TKMLDriver, TKMLTopLevelDriver
from .builder import TKMLWidgetBuilder, TKMLWidget
from . import widgets #Expose the internal widgets as well

__version__ = "1.1.0"
__author__ = "Randy Graham"