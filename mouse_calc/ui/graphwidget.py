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
from mouse_calc.ui.configmanager import ConfigManager


class GraphWidget(QTabWidget):
    loadConfigSiganl = pyqtSignal()
    saveConfigSiganl = pyqtSignal()
    changeConfigIDSignal = pyqtSignal(int)

    @property
    def config_id(self):
        return self.__config_id

    @config_id.setter
    def config_id(self, config_id):
        self.__config_id = config_id
        self.changeConfigIDSignal.emit(config_id)

    def __init__(self, data, config_id):
        super().__init__()
        self.data = data
        self.data_id = DataManager.new(self.data)
        self.config_id = config_id
        self.configchange_callbacks = []

        configs = ConfigManager.get(config_id)
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

        distance_config = configs["distance"]
        if configs["distance_timerange_predict"]:
            distance_config["bg_time_init"] = min_time
            distance_config["bg_time_end"] = median_time
            distance_config["tg_time_init"] = median_time
            distance_config["tg_time_end"] = max_time

        cor_config = configs["cor"]
        if configs["cor_timerange_predict"]:
            cor_config["bg_time_init"] = min_time
            cor_config["bg_time_end"] = median_time
            cor_config["tg_time_init"] = median_time
            cor_config["tg_time_end"] = max_time

        maxTemperaturePage = MaxTemperatureGraphPageWidget(self, "max temperature", self.data_id, config_id)
        self.addTab(maxTemperaturePage, "max temperature")
        self.changeConfigIDSignal.connect(lambda cid: maxTemperaturePage.changeConfigID(cid))

        """
        minTemperaturePage = MinTemperatureGraphPageWidget(self, "min temperature", self.data_id, self.data, temperature_config)
        self.addTab(minTemperaturePage, "min temperature")
        """

        distancePage = DistanceGraphPageWidget(self, "distance", self.data_id, config_id)
        self.addTab(distancePage, "distance")
        self.changeConfigIDSignal.connect(lambda cid: distancePage.changeConfigID(cid))

        corPage = CorGraphPageWidget(self, "cor", self.data_id, config_id)
        corPage.addpageSignal.connect(self.addtab)
        self.addTab(corPage, "cor")
        self.changeConfigIDSignal.connect(lambda cid: corPage.changeConfigID(cid))

    def addtab(self, obj):
        x_data = obj["x_data"]
        y_data = obj["y_data"]
        name = obj["name"]
        widget = GraphPageWidget(self, name, self.data_id, self.config_id)
        widget.appendData(x_data, y_data, name)
        widget.updateGraph()
        self.addTab(widget, name)

    def saveConfigCallback(self, config_id):
        self.config_id = config_id
        self.loadConfigSiganl.emit()
