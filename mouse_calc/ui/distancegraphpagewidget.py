import multiprocessing

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *

from mouse_calc.lib import *
from mouse_calc.ui.graphpagewidget import GraphPageWidget
from mouse_calc.ui.datamanager import DataType, ErrorType, DataManager
from mouse_calc.ui.configmanager import ConfigManager
from mouse_calc.ui.worker import Worker


class DistanceGraphPageWidget(GraphPageWidget):
    counter = 1
    def __init__(self, parent, page_name, data_id, config_id):
        super().__init__(parent, page_name, data_id, config_id)

        data = DataManager.get_data(self.data_id)
        x_data = data.get_col(TIME)
        y_data = data.get_col(DISTANCE)
        self.appendData(x_data, y_data, "data", self.graphoptions)
        self.updateGraph()

    def initCalcOptionEditWidget(self):
        config = ConfigManager.get(self.config_id)
        temperature_config = config["distance"]
        self.calcOptionEditWidget.makeForms(temperature_config)

    def calcProcess(self, progress_callback):
        config = ConfigManager.get(self.config_id)
        option = config["distance"]

        bg_time_init = option["bg_time_init"]
        bg_time_end = option["bg_time_end"]
        tg_time_init = option["tg_time_init"]
        tg_time_end = option["tg_time_end"]
        step_size = option["step_size"]
        welch_thres = option["welch_thres"]
        label = "error" + str(self.counter)

        data = DataManager.get_data(self.data_id)
        q = multiprocessing.Queue()
        f = lambda: q.put(distance_process(data, bg_time_init, bg_time_end, tg_time_init, tg_time_end, step_size=step_size, save_svg=False, show_graph=False, welch_thres=welch_thres))
        p = multiprocessing.Process(target=f)
        p.start()
        error_data, _ = q.get()
        p.join()

        DataManager.append_error(self.data_id, ErrorType.DISTANCE_ERROR, error_data, option)

        x = error_data.get_col(TIME)
        y = error_data.get_col(ERROR_VALUE)
        self.appendData(x, y, label, {"twinx": True})
        self.counter += 1
        self.updateGraph()


