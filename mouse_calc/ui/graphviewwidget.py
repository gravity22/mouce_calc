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
from PyQt5.QtWebEngineWidgets import *
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

    def __init__(self, parent=None, width=5, height=4, dpi=100, title="example"):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.twinx = None
        super().__init__(self.fig)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setFocus()
        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.artists = []

        self.setTitle(title)
        self.initEventCallBack()

        if parent:
            parent.toolbar = NavigationToolbar(self, parent)

    def initEventCallBack(self):
        self.button_press_event = None
        self.button_release_event = None
        self.motion_notify_event = None
        self.key_press_event = None
        self.rectangle_selector = None

        self.modechange("zoom")

    def resetEventCallBack(self):
        if self.button_press_event:
            self.mpl_disconnect(self.button_press_event)
        self.button_press_event = None

        if self.button_release_event:
            self.mpl_disconnect(self.button_release_event)
        self.button_release_event = None

        if self.motion_notify_event:
            self.mpl_disconnect(self.motion_notify_event)
        self.motion_notify_event = None

        if self.key_press_event:
            self.mpl_disconnect(self.key_press_event)
        self.key_press_event = None

        if self.rectangle_selector:
            self.rectangle_selector.set_visible(False)
            self.rectangle_selector.set_active(False)
        self.rectangle_selector = None

    def modechange(self, mode):
        self.resetEventCallBack()
        if mode=="translation":
            self.modeTranslation()
        elif mode=="zoom":
            self.modeZoom()
        self.requireRedrawSignal.emit()

    def modeTranslation(self):
        self.button_press_event = self.mpl_connect("button_press_event", self.translation_on_press)
        self.button_release_event = self.mpl_connect("button_release_event", self.translation_on_release)
        self.motion_notify_event = self.mpl_connect("motion_notify_event", self.translation_on_motion)

    def modeZoom(self):
        self.rectangle_selector = RectangleSelector(
                self.axes,
                self.zoom_select_callback,
                drawtype="box",
                useblit=True,
                button=[1],
                interactive=True)
        self.key_press_event = self.mpl_connect("key_press_event", self.zoom_key_press)

    def updateCanvas(self):
        self.clear()

    def plot(self, x, y, label=None, **option):
        twinx = option.get("twinx")
        color = option.get("color")
        linestyle = option.get("linestyle")
        if twinx:
            if self.twinx is None:
                self.twinx = self.axes.twinx()
                self.twinx.set_zorder(0.1)
            ax = self.twinx
            self.axes.patch.set_visible(False)
        else:
            ax = self.axes

        line = ax.plot(x, y, label=label, color=color, linestyle=linestyle)
        if label:
            line[0].set_label(label)
            self.axes.legend()
        self.artists.append(line)

    def scatter(self, x, y, label=None, **option):
        twinx = option.get('twinx')
        marker = option.get('marker')
        scatter = self.axes.scatter(x, y,  s=0.4, marker=marker)
        if label:
            scatter.set_label(label)
            self.axes.legend()
        self.artists.append(scatter)

    def barh(self, y, width, height=0.8, left=None, align='center'):
        barh = self.axes.barh(y, width, height=height)
        self.artists.append(barh)

    def yticks(self, tick, label):
        self.axes.set_yticks(tick)
        self.axes.set_yticklabels(label)

    def getXlim(self):
        return self.axes.get_xlim()

    def getYlim(self, graphname="main"):
        return self.axes.get_ylim()

    def setXlim(self, rng, graphname="main"):
        self.axes.set_xlim(rng)

    def setYlim(self, rng, graphname="main"):
        self.axes.set_ylim(rng)

    def clear(self):
        self.artists = []
        self.axes.clear()

    def setTitle(self, title):
        self.axes.set_title(title)

    def translation_on_press(self, event):
        xlim = self.getXlim()
        ylim = self.getYlim()
        self.press = (event.x, event.y, xlim, ylim)
        self.translationInitSignal.emit()

    def translation_on_motion(self, event):
        if self.press is None:
            return
        xpress, ypress, xlim, ylim = self.press
        # FIXME: 気合で決めてるから良くない
        dx = (event.x - xpress) * -0.01
        dy = (event.y - ypress) * -0.01
        self.translationSignal.emit({"dx": dx, "dy": dy})

    def translation_on_release(self, event):
        self.press = None
        self.translationEndSiganal.emit()

    def zoom_select_callback(self, eclick, erelease):
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        self.zoomSelectSignal.emit({
            "xdata_init": min(x1, x2),
            "xdata_end": max(x1, x2),
            "ydata_init": min(y1, y2),
            "ydata_end": max(y1, y2),
        })

    def zoom_key_press(self, event):
        if event.key in ["enter"] and self.rectangle_selector.active:
            print("emit")
            self.zoomDecideSignal.emit()
