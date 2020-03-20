from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *

from mouse_calc.lib import *
from mouse_calc.ui.datamanager import DataManager
from mouse_calc.ui.configmanager import ConfigManager
from mouse_calc.ui.allcalculation import  AllCalculation
from mouse_calc.ui.graphviewwidget import GraphViewWidget
from mouse_calc.ui.allcalculation import AllCalculation


class SummaryGraphWidget(QWidget):
    def __init__(self,
                 data_id,
                 control_data_id=None,
                 config_id=None,
                 linewidth=0.3,
                 temperature_graph_enable=True,
                 distance_graph_enable=True,
                 cor_graph_enable=True):
        super().__init__()
        self.data_id = data_id
        self.control_data_id = control_data_id
        self.config_id = config_id
        self.linewidth = linewidth
        self.temperature_graph_enable = temperature_graph_enable
        self.distance_graph_enable = distance_graph_enable
        self.cor_graph_enable = cor_graph_enable
        self.nrows = self.distance_graph_enable + self.temperature_graph_enable + self.cor_graph_enable

        self.inner_layout = QVBoxLayout()
        self.setLayout(self.inner_layout)

        self.graphViewWidget = GraphViewWidget(nrows=self.nrows)
        self.toolBar = self.graphViewWidget.make_navigationtoolbar()

        self.inner_layout.addWidget(self.toolBar)
        self.inner_layout.addWidget(self.graphViewWidget)
        
        self.draw_graph()

    def remake_graphview(self, nrows=None):
        self.nrow = nrows
        self.graphViewWidget = GraphViewWidget(nrows=self.nrows)
    
    def draw_graph(self):
        data = DataManager.get_data(self.data_id)
        error = DataManager.get_reps(self.data_id)
        temperature_error = error["max_temperature"]
        distance_error = error["distance"]
        cor_error = error["cor"]

        row = 0

        if True:
            self.graphViewWidget.setTitle("temperature and distance", row=row)

            x_data = data.get_col(TIME)
            y_data = data.get_col(MAX_TEMPERATURE)
            self.graphViewWidget.plot(x_data, y_data, row=row, color="gray", linewidth=self.linewidth)
            
            x_data = data.get_col(TIME)
            y_data = data.get_col(DISTANCE)
            self.graphViewWidget.plot(x_data, y_data, row=row, color="gray", linewidth=self.linewidth, twinx=True)

            row += 1

        if self.temperature_graph_enable:
            self.graphViewWidget.setTitle("temperature and error", row=row)
            x_data = data.get_col(TIME)
            y_data = data.get_col(MAX_TEMPERATURE)
            self.graphViewWidget.plot(x_data, y_data, row=row, color="orange", linewidth=self.linewidth)

            x_data = temperature_error.data.get_col(TIME)
            y_data = temperature_error.data.get_col(TEMPERATURE_ERROR_DATA)
            self.graphViewWidget.plot(x_data, y_data, row=row, color="red", linewidth=self.linewidth, twinx=True)

            row += 1

        if self.distance_graph_enable:
            self.graphViewWidget.setTitle("distance and error", row=row)
            x_data = data.get_col(TIME)
            y_data = data.get_col(DISTANCE)
            self.graphViewWidget.plot(x_data, y_data, row=row, color="g", linewidth=self.linewidth)

            x_data = distance_error.data.get_col(TIME)
            y_data = distance_error.data.get_col(ERROR_VALUE)
            self.graphViewWidget.plot(x_data, y_data, row=row, color="red", linewidth=self.linewidth, twinx=True)

            row += 1

        if self.cor_graph_enable:
            self.graphViewWidget.setTitle("cor and error", row=row)

            x_data = data.get_col(TIME)
            y_data = data.get_col(MAX_TEMPERATURE)
            self.graphViewWidget.plot(x_data, y_data, row=row, color="orange", linewidth=self.linewidth)

            x_data = data.get_col(TIME)
            y_data = data.get_col(DISTANCE)
            self.graphViewWidget.plot(x_data, y_data, row=row, color="green", linewidth=self.linewidth)

            x_data = cor_error.data.get_col(TIME)
            y_data = cor_error.data.get_col(COR_ERROR_VALUE)
            self.graphViewWidget.plot(x_data, y_data, row=row, color="red", linewidth=self.linewidth, twinx=True)

            row += 1
