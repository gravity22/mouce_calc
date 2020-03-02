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
    def __init__(self, data_id, control_data_id=None, config_id=None):
        super().__init__()
        self.data_id = data_id
        self.control_data_id = control_data_id
        self.config_id = config_id
        self.inner_layout = QVBoxLayout()
        self.setLayout(self.inner_layout)

        self.graphViewWidget = GraphViewWidget(nrows=4)
        self.toolBar = self.graphViewWidget.make_navigationtoolbar()

        self.graphViewWidget.setTitle("temperature and distance", row=0)
        self.graphViewWidget.setTitle("temperature and error", row=1)
        self.graphViewWidget.setTitle("distance and error", row=2)
        self.graphViewWidget.setTitle("cor and error", row=3)

        self.inner_layout.addWidget(self.toolBar)
        self.inner_layout.addWidget(self.graphViewWidget)
        
        data = DataManager.get_data(data_id)
        error = DataManager.get_reps(data_id)
        temperature_error = error["max_temperature"]
        distance_error = error["distance"]
        cor_error = error["cor"]

        x_data = data.get_col(TIME)
        y_data = data.get_col(MAX_TEMPERATURE)
        self.graphViewWidget.plot(x_data, y_data, row=0, color="gray", linewidth=0.2)
        
        x_data = data.get_col(TIME)
        y_data = data.get_col(DISTANCE)
        self.graphViewWidget.plot(x_data, y_data, row=0, color="gray", linewidth=0.2, twinx=True)

        x_data = data.get_col(TIME)
        y_data = data.get_col(MAX_TEMPERATURE)
        self.graphViewWidget.plot(x_data, y_data, row=1, color="orange", linewidth=0.2)

        x_data = temperature_error.data.get_col(TIME)
        y_data = temperature_error.data.get_col(TEMPERATURE_ERROR_DATA)
        self.graphViewWidget.plot(x_data, y_data, row=1, color="red", linewidth=0.2, twinx=True)

        x_data = data.get_col(TIME)
        y_data = data.get_col(DISTANCE)
        self.graphViewWidget.plot(x_data, y_data, row=2, color="g", linewidth=0.2)

        x_data = distance_error.data.get_col(TIME)
        y_data = distance_error.data.get_col(ERROR_VALUE)
        self.graphViewWidget.plot(x_data, y_data, row=2, color="red", linewidth=0.2, twinx=True)

        x_data = data.get_col(TIME)
        y_data = data.get_col(MAX_TEMPERATURE)
        self.graphViewWidget.plot(x_data, y_data, row=3, color="orange", linewidth=0.2)

        x_data = data.get_col(TIME)
        y_data = data.get_col(DISTANCE)
        self.graphViewWidget.plot(x_data, y_data, row=3, color="green", linewidth=0.2)

        x_data = cor_error.data.get_col(TIME)
        y_data = cor_error.data.get_col(COR_ERROR_VALUE)
        self.graphViewWidget.plot(x_data, y_data, row=3, color="red", linewidth=0.2, twinx=True)


