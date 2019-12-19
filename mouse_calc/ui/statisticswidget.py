import sys
from collections import OrderedDict

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *

from mouse_calc.lib import *
from mouse_calc.ui.datamanager import DataType, ErrorType, DataManager
from mouse_calc.ui.graphviewwidget import GraphViewWidget


class StatisticsWidget(QWidget):
    def __init__(self, parent=None, datatype=None):
        super().__init__(parent)
        self.inner_layout = QHBoxLayout()
        self.setLayout(self.inner_layout)

        self.graphViewWidget = GraphViewWidget()
        self.inner_layout.addWidget(self.graphViewWidget)

        if datatype is ErrorType.MAX_TEMPERATURE_ERROR:
            self.max_temperature_error_draw()
        elif datatype is ErrorType.MIN_TEMPERATURE_ERROR:
            self.min_temperature_error_draw()
        elif datatype is ErrorType.DISTANCE_ERROR:
            self.distance_error_draw()
        elif datatype is ErrorType.COR_ERROR:
            self.cor_error_draw()
        elif datatype is ErrorType.SUM_ERROR:
            self.sum_error_draw()

    def max_temperature_error_draw(self):
        counters = []
        for dataitem in DataManager.all():
            name = 'data' + str(dataitem.id)
            for error in dataitem.errors:
                if error.type is ErrorType.MAX_TEMPERATURE_ERROR:
                    d = error.data.get_col(TEMPERATURE_ERROR_DATA)
                    d_bool = (d>0)
                    count = sum(d_bool)
                    counters.append(count)

        index = list(range(len(counters)))
        self.graphViewWidget.barh(index, counters)
        self.graphViewWidget.yticks(index, list(map(lambda x: 'error'+str(x), index)))
        self.graphViewWidget.draw()

    def min_temperature_error_draw(self):
        counters = []
        for dataitem in DataManager.all():
            name = 'data' + str(dataitem.id)
            for error in dataitem.errors:
                if error.type is ErrorType.MIN_TEMPERATURE_ERROR:
                    d = error.data.get_col(TEMPERATURE_ERROR_DATA)
                    d_bool = (d>0)
                    count = sum(d_bool)
                    counters.append(count)

        index = list(range(len(counters)))
        self.graphViewWidget.barh(index, counters)
        self.graphViewWidget.yticks(index, list(map(lambda x: 'error'+str(x), index)))
        self.graphViewWidget.draw()

    def distance_error_draw(self):
        counters = []
        for dataitem in DataManager.all():
            name = 'data' + str(dataitem.id)
            for error in dataitem.errors:
                if error.type is ErrorType.DISTANCE_ERROR:
                    d = error.data.get_col(ERROR_VALUE)
                    d_bool = (d>0)
                    count = sum(d_bool)
                    counters.append(count)

        index = list(range(len(counters)))
        self.graphViewWidget.barh(index, counters)
        self.graphViewWidget.yticks(index, list(map(lambda x: 'error'+str(x), index)))
        self.graphViewWidget.draw()

    def cor_error_draw(self):
        counters = []
        for dataitem in DataManager.all():
            name = 'data' + str(dataitem.id)
            for error in dataitem.errors:
                if error.type is ErrorType.COR_ERROR:
                    d = error.data.get_col(COR_ERROR_VALUE)
                    d_bool = (d>0)
                    count = sum(d_bool)
                    counters.append(count)

        index = list(range(len(counters)))
        self.graphViewWidget.barh(index, counters)
        self.graphViewWidget.yticks(index, list(map(lambda x: 'error'+str(x), index)))
        self.graphViewWidget.draw()

    def sum_error_draw(self):
        datas = {}
        for dataitem in DataManager.all():
            graphdata = OrderedDict()
            name = "data" + str(dataitem.id)
            reps = dataitem.get_reps()
            print(reps, file=sys.stderr)
            if reps['max_temperature']:
                d = reps['max_temperature'].data.get_col(TEMPERATURE_ERROR_DATA)
                d_bool = (d>0)
                count = sum(d_bool)
                graphdata["max_temperature"] = count
            if reps['min_temperature']:
                d = reps['min_temperature'].data.get_col(TEMPERATURE_ERROR_DATA)
                d_bool = (d>0)
                count = sum(d_bool)
                graphdata["min_temperature"] = count
            if reps['distance']:
                d = reps['distance'].data.get_col(ERROR_VALUE)
                d_bool = (d>0)
                count = sum(d_bool)
                graphdata["distance"] = count
            if reps['cor']:
                d = reps['cor'].data.get_col(COR_ERROR_VALUE)
                d_bool = (d>0)
                count = sum(d_bool)
                graphdata['cor'] = count
            datas[name] = (graphdata)

        for name, grpahdaa in datas.items():
            labels = list(map(lambda k: name+k, graphdata.keys()))
            values = graphdata.values()
            index = list(range(len(values)))
            self.graphViewWidget.barh(index, values)
            self.graphViewWidget.yticks(index, labels)
        self.graphViewWidget.draw()
