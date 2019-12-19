import multiprocessing

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *

from mouse_calc.lib import *
from mouse_calc.ui.graphpagewidget import GraphPageWidget
from mouse_calc.ui.datamanager import DataType, ErrorType, DataManager
from mouse_calc.ui.worker import Worker


class MaxTemperatureGraphPageWidget(GraphPageWidget):
    counter = 1

    def __init__(self, parent, page_name, data_id, data, config=None):
        self.data = data
        super().__init__(parent, page_name, data_id, config)

        data = DataManager.get_data(self.data_id)
        x_data = data.get_col(TIME)
        y_data = data.get_col(MAX_TEMPERATURE)
        self.appendData(x_data, y_data, "data", self.graphoptions)

        x_data = self.data.get_col(TIME) 
        self.xlim = (min(x_data), max(x_data))
        self.updateGraph()

    def calcProcess(self, option, progress_callback):
        bg_time_init = option["bg_time_init"]
        bg_time_end = option["bg_time_end"]
        tg_time_init = option["tg_time_init"]
        tg_time_end = option["tg_time_end"]
        step_size = option["step_size"]
        thres_sd_heat = option["thres_sd_heat"]
        label = "error" + str(self.counter)

        q = multiprocessing.Queue()
        f = lambda: q.put(temperature_process(self.data, bg_time_init, bg_time_end, tg_time_init, tg_time_end, step_size=step_size, thres_sd_heat=thres_sd_heat, save_svg=False, show_graph=False))
        p = multiprocessing.Process(target=f)
        p.start()
        error_data, _ = q.get()
        p.join()

        DataManager.append_error(self.data_id, ErrorType.MAX_TEMPERATURE_ERROR, error_data, option)

        x = error_data.get_col(TIME)
        y = error_data.get_col(TEMPERATURE_ERROR_DATA)
        self.appendData(x, y, label, {"twinx": True})
        self.updateGraph()
        self.counter += 1


