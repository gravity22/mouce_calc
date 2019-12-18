from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *

from mouse_calc.lib import *

from mouse_calc.ui.loadwidget import LoadWidget
from mouse_calc.ui.graphwidget import GraphWidget

class MainWidget(QStackedWidget):
    graphWidgets = {}
    newwidget_signal = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.loadWidget = LoadWidget(self)
        self.loadWidget.loadSignal.connect(self.makeGraph)

        self.addWidget(self.loadWidget)
        self.loadWidgetIndex = self.currentIndex()

    def makeGraph(self, datas):
        path = datas["datapath"]
        configs = datas["configs"]
        loader = Loader(path, names=[TIME, MAX_TEMPERATURE, MAX_POS_X, MAX_POS_Y, MIN_TEMPERATURE, MIN_POS_X, MIN_POS_Y])
        loader.set_preprocess(a3_preprocess)

        data = loader.load()
        data = calc_distance(data)

        widget = GraphWidget(data, configs)
        index = self.addWidget(widget)
        self.graphWidgets[path] = index

        self.setCurrentIndex(index)

    def openFile(self):
        filename = self.loadWidget.openFile()
        if filename:
            index = self.currentIndex()
            self.newwidget_signal.emit({"filename": filename, "index": index})

    def openLoadPage(self):
        self.setCurrentIndex(self.loadWidgetIndex)

    def changePage(self, path):
        index = self.graphWidgets[path]
        self.setCurrentIndex(index)

