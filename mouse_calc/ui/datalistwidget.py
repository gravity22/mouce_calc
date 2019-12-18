import sys
from io import BytesIO, StringIO
from io import TextIOWrapper
from datetime import timedelta
from collections import OrderedDict
import hashlib
import threading
import enum
import multiprocessing

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *

from mouse_calc.lib import *


class DataListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        for item in DataManager.all():
            self.addItem(str(item.id))
            for error in item.errors:
                self.addItem(str(error.id))

