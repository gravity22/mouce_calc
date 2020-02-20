import sys
from datetime import timedelta
from abc import ABCMeta, abstractmethod
from itertools import cycle

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *

from mouse_calc.lib import *
from mouse_calc.ui.graphviewwidget import GraphViewWidget
from mouse_calc.ui.calcoptioneditwidget import CalcOptionEditWidget
from mouse_calc.ui.worker import Worker
from mouse_calc.ui.configmanager import ConfigManager


class ErrorColormap(object):
    def __init__(self):
        self.color_list = cycle(["red", "orangered", "darkorange", "tomato", "orange", "firebrick", "crimson"])

    def generate(self):
        return self.color_list.__next__()


class GraphPageWidget(QWidget):
    __metaclass__ = ABCMeta

    loadConfigSiganl = pyqtSignal(int)
    saveConfigSiganl = pyqtSignal()

    def __init__(self, parent, page_name, data_id, config_id, graphoptions={}):
        super().__init__(parent=parent)
        self.parentwidget = parent
        self.threadpool = QThreadPool()
        self.graphoptions = graphoptions
        self.toolbar = None

        self.data_id = data_id
        self.config_id = config_id
        self.config = ConfigManager.get(config_id)
        self.datas = []
        self.xlim = None
        self.ylim = None
        self.nowTranslation = None
        self.nowZooming = None
        self.history_index = -1
        self.limhistory = []
        self.require_updategraph = False
        self.error_color_map = ErrorColormap()

        self.graphViewWidget = GraphViewWidget(self, title=page_name)
        self.graphViewWidget.translationInitSignal.connect(self.translationInitEvent)
        self.graphViewWidget.translationSignal.connect(self.translationEvent)
        self.graphViewWidget.translationEndSiganal.connect(self.translationEndEvent)
        self.graphViewWidget.zoomSelectSignal.connect(self.zoomSelectEvent)
        self.graphViewWidget.zoomDecideSignal.connect(self.zoomDecideEvent)
        self.graphViewWidget.requireRedrawSignal.connect(self.updateGraph)

        self.inner_layout = QHBoxLayout()
        if self.toolbar is None:
            self.toolbar = QToolBar()

            self.toolbar_select_action = self.toolbar.addAction("Select")
            self.toolbar_zoom_action = self.toolbar.addAction("Zoom")
            self.toolbar_back_action = self.toolbar.addAction("back")
            self.toolbar_next_action = self.toolbar.addAction("next")
            self.toolbar_reset_action = self.toolbar.addAction("reset")

            self.toolbar_select_action.triggered.connect(lambda b, graphview=self.graphViewWidget: graphview.modechange("translation"))
            self.toolbar_zoom_action.triggered.connect(lambda b, graphview=self.graphViewWidget: graphview.modechange("zoom"))
            self.toolbar_back_action.triggered.connect(self.backLimHistory)
            self.toolbar_next_action.triggered.connect(self.nextLimHistory)
            self.toolbar_reset_action.triggered.connect(self.resetLim)


        vbox = QVBoxLayout()
        vbox.addWidget(self.toolbar)
        vbox.addLayout(self.inner_layout)
        self.setLayout(vbox)

        self.calcOptionEditWidget = CalcOptionEditWidget()
        self.calcOptionEditWidget.calcSignal.connect(self.callCalcProcess)
        self.initCalcOptionEditWidget()

        self.inner_layout.addWidget(self.graphViewWidget, 4)
        self.inner_layout.addWidget(self.calcOptionEditWidget, 1)
        parent.loadConfigSiganl.connect(self.reload_config)
        self.loadConfigSiganl.connect(parent.saveConfigCallback)

    @abstractmethod
    def initCalcOptionEditWidget(self):
        pass

    def changeConfigID(self, cid):
        self.config_id = cid

    def appendData(self, x, y, name, options={}):
        self.require_updategraph = True
        self.datas.append((name, x, y, options))

    def updateGraph(self):
        if self.require_updategraph is True:
            self.graphViewWidget.clear()
            for name, x, y, options in self.datas:
                graphtype = options.get("graphtype")
                if graphtype == "scatter":
                    self.graphViewWidget.scatter(x, y, label=name, **options)
                else:
                    self.graphViewWidget.plot(x, y, label=name, **options)
            self.require_updategraph = False

        if self.xlim is None:
            self.xlim = self.graphViewWidget.getXlim()
        else:
            self.graphViewWidget.setXlim(self.xlim)

        if self.ylim is None:
            self.ylim = self.graphViewWidget.getYlim()
        else:
            self.graphViewWidget.setYlim(self.ylim)

        self.graphViewWidget.draw()

        if self.history_index == -1:
            self.updateLimHistory()

    def updateLimHistory(self):
        self.history_index += 1
        self.limhistory.insert(self.history_index, (self.xlim, self.ylim))

    def resetLim(self):
        self.history_index = 0
        xlim, ylim = self.limhistory[self.history_index]
        self.xlim = xlim
        self.ylim = ylim
        self.updateGraph()

    def nextLimHistory(self):
        if self.history_index+1 < len(self.limhistory):
            self.history_index += 1
        xlim, ylim = self.limhistory[self.history_index]
        self.xlim = xlim
        self.ylim = ylim
        self.updateGraph()

    def backLimHistory(self):
        if self.history_index-1 >= 0:
            self.history_index -= 1
        xlim, ylim = self.limhistory[self.history_index]
        self.xlim = xlim
        self.ylim = ylim
        self.updateGraph()

    def translationInitEvent(self):
        self.nowTranslation = (self.xlim, self.ylim)

    def translationEvent(self, obj):
        if self.nowTranslation is None:
            return

        dx = obj["dx"]
        dy = obj["dy"]
        xlim, ylim =  self.nowTranslation

        if xlim and dx:
            min_value, max_value = xlim 
            if type(max_value) is QDateTime or type(max_value) is pd._libs.tslibs.timestamps.Timestamp or type(max_value) is datetime.datetime:
                dx = timedelta(dx)
            self.xlim = (min_value+dx, max_value+dx)

        if ylim and dy:
            min_value, max_value = ylim 
            self.ylim = (min_value+dy, max_value+dy)

        self.updateGraph()
        self.updateLimHistory()

    def translationEndEvent(self):
        self.nowTranslation = None

    def zoomSelectEvent(self, obj):
        xdata_init = obj["xdata_init"]
        xdata_end = obj["xdata_end"]
        ydata_init = obj["ydata_init"]
        ydata_end = obj["ydata_end"]
        self.nowZooming = (xdata_init, xdata_end, ydata_init, ydata_end)

    def zoomDecideEvent(self):
        if self.nowZooming:
            xdata_init, xdata_end, ydata_init, ydata_end = self.nowZooming
            print(xdata_init, xdata_end, file=sys.stderr)
            if type(self.xlim[0]) is QDateTime or type(self.xlim[0]) is pd._libs.tslibs.timestamps.Timestamp or type(self.xlim[0]) is datetime.datetime:
                xdata_init = matplotlib.dates.num2date(xdata_init)
                xdata_end = matplotlib.dates.num2date(xdata_end)
            self.xlim = (xdata_init, xdata_end)
            self.ylim = (ydata_init, ydata_end)
        self.updateGraph()
        self.updateLimHistory()

    def callCalcProcess(self):
        worker = Worker(self.calcProcess)
        self.threadpool.start(worker)

    @abstractmethod
    def calcProcess(self,  progress_callback):
        pass

    def saveConfig(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.AnyFile)
        (filename, kakutyousi) = dialog.getSaveFileName(self, "Save Json file", "./", "JSON files (*.json)")
        if filename:
            ConfigManager.file_save(self.config_id, filename)

    def loadConfig(self):
        (filename, kakutyousi) = QFileDialog.getOpenFileName(self, "Open Json file", "./", "JSON files (*.json)")
        if filename:
            self.config_id = ConfigManager.file_open(filename)
            self.loadConfigSiganl.emit(self.config_id)
        else:
            return None

    @abstractmethod
    def reload_config(self):
        pass
