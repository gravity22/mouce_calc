from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *

from mouse_calc.lib import *
from mouse_calc.ui.datamanager import DataType, ErrorType, DataManager
from mouse_calc.ui.graphpagewidget import GraphPageWidget
from mouse_calc.ui.maxtemperaturegraphpagewidget import  MaxTemperatureGraphPageWidget
from mouse_calc.ui.mintemperaturegraphpagewidget import  MinTemperatureGraphPageWidget
from mouse_calc.ui.distancegraphpagewidget import DistanceGraphPageWidget
from mouse_calc.ui.corgraphpagewidget import CorGraphPageWidget


class GraphWidget(QTabWidget):
    def __init__(self, data, configs):
        super().__init__()
        self.data = data
        self.data_id = DataManager.new(self.data)

        if configs["temperature_timerange_predict"] or configs["distance_timerange_predict"] or configs["cor_timerange_predict"]:
            time_data = data.get_col(TIME)
            min_time = min(time_data)
            median_time = pd.Timestamp.fromordinal(int(time_data.apply(lambda x: x.toordinal()).median()))
            max_time = max(time_data)

        temperature_config = configs["temperature"]
        if configs["temperature_timerange_predict"]:
            temperature_config["bg_time_init"] = min_time
            temperature_config["bg_time_end"] = median_time
            temperature_config["tg_time_init"] = median_time
            temperature_config["tg_time_end"] = max_time

        maxTemperaturePage = MaxTemperatureGraphPageWidget(self, "max temperature", self.data_id, self.data, temperature_config)
        self.addTab(maxTemperaturePage, "max temperature")

        """
        minTemperaturePage = MinTemperatureGraphPageWidget(self, "min temperature", self.data_id, self.data, temperature_config)
        self.addTab(minTemperaturePage, "min temperature")
        """

        distance_config = configs["distance"]
        if configs["distance_timerange_predict"]:
            distance_config["bg_time_init"] = min_time
            distance_config["bg_time_end"] = median_time
            distance_config["tg_time_init"] = median_time
            distance_config["tg_time_end"] = max_time
        temperaturePage = DistanceGraphPageWidget(self, "distance", self.data_id, self.data, distance_config)
        self.addTab(temperaturePage, "distance")

        cor_config = configs["cor"]
        if configs["cor_timerange_predict"]:
            cor_config["bg_time_init"] = min_time
            cor_config["bg_time_end"] = median_time
            cor_config["tg_time_init"] = median_time
            cor_config["tg_time_end"] = max_time
        temperaturePage = CorGraphPageWidget(self, "cor", self.data_id, self.data, cor_config)
        temperaturePage.addpageSignal.connect(self.addtab)
        self.addTab(temperaturePage, "cor")

    def addtab(self, obj):
        x_data = obj["x_data"]
        y_data = obj["y_data"]
        name = obj["name"]
        widget = GraphPageWidget(self, name, self.data_id)
        widget.appendData(x_data, y_data, name)
        widget.updateGraph()
        self.addTab(widget, name)

