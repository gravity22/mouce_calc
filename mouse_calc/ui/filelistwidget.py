from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *


class FileListWidget(QDockWidget):
    def __init__(self, name):
        super().__init__(name)
        self.listwidget = QListWidget()
        self.setWidget(self.listwidget)

    def append(self, item):
        self.listwidget.addItem(item)

