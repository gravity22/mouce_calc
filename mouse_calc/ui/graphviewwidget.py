from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *


class GraphViewWidget(FigureCanvas):
    press = None
    translationInitSignal = pyqtSignal()
    translationSignal = pyqtSignal(object)
    translationEndSiganal = pyqtSignal()
    zoomSelectSignal = pyqtSignal(object)
    zoomDecideSignal = pyqtSignal()
    requireRedrawSignal = pyqtSignal()

    def __init__(self, parent=None, width=5, height=4, dpi=100, title="example", nrows=1, ncols=1):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.subplots(nrows=nrows, ncols=ncols, squeeze=False)
        self.twinx = [[None for w in range(width)] for h in range(height)]
        super().__init__(self.fig)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setFocus()
        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.artists = []

        self.setTitle(title)

        if parent:
            parent.toolbar = self.make_navigationtoolbar(parent)

    def make_navigationtoolbar(self, parent=None):
        return NavigationToolbar(self, parent)

    def updateCanvas(self):
        self.clear()

    def plot(self, x, y, label=None, row=0, col=0, **option):
        twinx = option.get("twinx")
        color = option.get("color")
        linestyle = option.get("linestyle")
        linewidth = option.get("linewidth")
        if twinx:
            if self.twinx[row][col] is None:
                self.twinx[row][col] = self.axes[row][col].twinx()
                self.twinx[row][col].set_zorder(0.1)
            ax = self.twinx[row][col]
            self.axes[row][col].patch.set_visible(False)
        else:
            ax = self.axes[row][col]

        line = ax.plot(x, y, label=label, color=color, linestyle=linestyle, linewidth=linewidth)
        if label:
            line[0].set_label(label)
            self.axes[row][col].legend()
        self.artists.append(line)

    def scatter(self, x, y, label=None, row=0, col=0, **option):
        twinx = option.get('twinx')
        marker = option.get('marker')
        scatter = self.axes[row][col].scatter(x, y,  s=0.4, marker=marker)
        if label:
            scatter.set_label(label)
            self.axes[row][col].legend()
        self.artists.append(scatter)

    def barh(self, y, width, height=0.8, left=None, align='center', row=0, col=0):
        barh = self.axes[row][col].barh(y, width, height=height)
        self.artists.append(barh)

    def xticks(self, tick, label, row=0, col=0):
        self.axes[row][col].set_xticks(tick)
        self.axes[row][col].set_xticklabels(label)

    def yticks(self, tick, label, row=0, col=0):
        self.axes[row][col].set_yticks(tick)
        self.axes[row][col].set_yticklabels(label)

    def getXlim(self, row=0, col=0):
        return self.axes[row][col].get_xlim()

    def getYlim(self, row=0, col=0):
        return self.axes[row][col].get_ylim()

    def setXlim(self, rng,  row=0, col=0):
        self.axes[row][col].set_xlim(rng)

    def setYlim(self, rng,  row=0, col=0):
        self.axes[row][col].set_ylim(rng)

    def clear(self, row=0, col=0):
        self.artists = []
        self.axes[row][col].clear()

    def setTitle(self, title, row=0, col=0):
        self.axes[row][col].set_title(title)

