import multiprocessing

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *

from mouse_calc.lib import *
from mouse_calc.ui.graphpagewidget import GraphPageWidget, ErrorColormap
from mouse_calc.ui.datamanager import DataType, ErrorType, DataManager
from mouse_calc.ui.configmanager import ConfigManager
from mouse_calc.ui.worker import Worker


class CorGraphPageWidget(GraphPageWidget):
    counter = 1
    addpageSignal = pyqtSignal(object)

    def __init__(self, parent, page_name, data_id, config_id):
        super().__init__(parent, page_name, data_id, config_id, {"graphtype": "scatter"})
        self.loadConfigSiganl.connect(self.reload_config)

        worker = Worker(self.initProcess)
        self.threadpool.start(worker)

    def initCalcOptionEditWidget(self):
        config = ConfigManager.get(self.config_id)
        cor_config = config["cor"]
        self.calcOptionEditWidget.makeForms(cor_config)
        self.calcOptionEditWidget.saveConfigButton.clicked.connect(self.saveConfig)
        self.calcOptionEditWidget.loadConfigButton.clicked.connect(self.loadConfig)

    def initProcess(self, progress_callback):
        data = DataManager.get_data(self.data_id)
        self.window_data = window_process(data, 8)
        x_data = np.log2(self.window_data.get_col(DISTANCE_MEAN))
        y_data = self.window_data.get_col(MAX_TEMPERATURE_MEAN)
        self.appendData(x_data, y_data, 'data', self.graphoptions)
        self.updateGraph()

    def calcProcess(self, progress_callback):
        config = ConfigManager.get(self.config_id)
        option = config["cor"]

        bg_time_init = option["bg_time_init"]
        bg_time_end = option["bg_time_end"]
        tg_time_init = option["tg_time_init"]
        tg_time_end = option["tg_time_end"]
        step_size = option["step_size"]
        sd_num = option["sd_num"]
        error_step = option["error_step"]

        data = DataManager.get_data(self.data_id)
        q = multiprocessing.Queue()
        f = lambda: q.put(cor_process(data, bg_time_init, bg_time_end, tg_time_init, tg_time_end, step_size=step_size, SD_NUM=sd_num, ERROR_STEP=error_step, save_svg=False, show_graph=False))
        p = multiprocessing.Process(target=f)
        p.start()
        error_data, pb_info = q.get()
        p.join()

        DataManager.append_error(self.data_id, ErrorType.COR_ERROR, error_data, option)

        slope = pb_info["slope"]
        n = pb_info["n"]
        n_plus = pb_info["n_plus"]
        n_minus = pb_info["n_minus"]

        t = np.log2(self.window_data.get_col(DISTANCE_MEAN))
        x = np.linspace(min(t), max(t), t.size)

        counter =  str(self.counter)
        error_color = self.error_color_map.generate()

        y = x * slope + n
        self.appendData(x, y, "error"+counter, {"color": error_color})

        y = x * slope + n_plus
        self.appendData(x, y, "error"+counter, {"color": error_color, "linestyle": "--"})

        y = x * slope + n_minus
        self.appendData(x, y, "error"+counter, {"color": error_color, "linestyle": "--"})

        self.updateGraph()

        x_data = error_data.get_col(TIME)
        y_data = error_data.get_col(COR_ERROR_VALUE)
        name = "cor error"+counter
        self.addpageSignal.emit({"x_data": x_data, "y_data": y_data, "name": name})

        self.counter += 1

    def reload_config(self):
        config = ConfigManager.get(self.config_id)
        cor_config = config["cor"]
        self.calcOptionEditWidget.reloadForms(cor_config)
