import sys
from io import BytesIO, StringIO
from io import TextIOWrapper
from datetime import timedelta
from collections import OrderedDict
import hashlib
import threading
import enum
import multiprocessing

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *

from mouse_calc.lib import *

from mouse_calc.ui.loadinfowidget import LoadInfoWidget



class LoadWidget(QWidget):
    targetpath = ""
    loadSignal = pyqtSignal(object)

    default_config = {
        "temperature": {
            "bg_time_init": datetime.datetime.now(),
            "bg_time_end": datetime.datetime.now(),
            "tg_time_init": datetime.datetime.now(),
            "tg_time_end": datetime.datetime.now(),
            "step_size": 8,
            "thres_sd_heat": 1.5,
        },
        "distance": {
            "bg_time_init": datetime.datetime.now(),
            "bg_time_end": datetime.datetime.now(),
            "tg_time_init": datetime.datetime.now(),
            "tg_time_end": datetime.datetime.now(),
            "step_size": 8,
            "welch_thres": 0.5,
        },
        "cor": {
            "bg_time_init": datetime.datetime.now(),
            "bg_time_end": datetime.datetime.now(),
            "tg_time_init": datetime.datetime.now(),
            "tg_time_end": datetime.datetime.now(),
            "step_size": 8,
            "error_step": 1,
            "sd_num": 1.5
        },
        "temperature_timerange_predict": False,
        "distance_timerange_predict": False,
        "cor_timerange_predict": False,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.configs = self.default_config

        self.innerLayout = QHBoxLayout()
        self.setLayout(self.innerLayout)
        self.loadInfoWidget = LoadInfoWidget(self.configs)

        self.innerLayout.addWidget(self.loadInfoWidget, 4)

        self.loadInfoWidget.loadButton.clicked.connect(parent.openFile)

    def getOptions(self):
        w = self.loadInfoWidget.temperature_widgets
        self.configs["temperature"]["bg_time_init"] = w["bg_time_init"].dateTime().toPyDateTime()
        self.configs["temperature"]["bg_time_end"] = w["bg_time_end"].dateTime().toPyDateTime()
        self.configs["temperature"]["tg_time_init"] = w["tg_time_init"].dateTime().toPyDateTime()
        self.configs["temperature"]["tg_time_end"] = w["tg_time_end"].dateTime().toPyDateTime()
        self.configs["temperature"]["step_size"] = w["step_size"].value()
        self.configs["temperature"]["thres_sd_heat"] = w["thres_sd_heat"].value()
        self.configs["temperature_timerange_predict"] = not (w["temperature_timerange_predict"].isChecked())

        w = self.loadInfoWidget.distance_widgets
        self.configs["distance"]["bg_time_init"] = w["bg_time_init"].dateTime().toPyDateTime()
        self.configs["distance"]["bg_time_end"] = w["bg_time_end"].dateTime().toPyDateTime()
        self.configs["distance"]["tg_time_init"] = w["tg_time_init"].dateTime().toPyDateTime()
        self.configs["distance"]["tg_time_end"] = w["tg_time_end"].dateTime().toPyDateTime()
        self.configs["distance"]["step_size"] = w["step_size"].value()
        self.configs["distance"]["welch_thres"] = w["welch_thres"].value()
        self.configs["distance_timerange_predict"] = not (w["distance_timerange_predict"].isChecked())

        w = self.loadInfoWidget.cor_widgets
        self.configs["cor"]["bg_time_init"] = w["bg_time_init"].dateTime().toPyDateTime()
        self.configs["cor"]["bg_time_end"] = w["bg_time_end"].dateTime().toPyDateTime()
        self.configs["cor"]["tg_time_init"] = w["tg_time_init"].dateTime().toPyDateTime()
        self.configs["cor"]["tg_time_end"] = w["tg_time_end"].dateTime().toPyDateTime()
        self.configs["cor"]["step_size"] = w["step_size"].value()
        self.configs["cor"]["error_step"] = w["error_step"].value()
        self.configs["cor"]["sd_num"] = w["sd_num"].value()
        self.configs["cor_timerange_predict"] = not (w["cor_timerange_predict"].isChecked())

    def loadEvent(self):
        self.getOptions()
        datas = {}
        datas["datapath"] = self.targetpath
        datas["configs"] = self.configs
        self.loadSignal.emit(datas)

    def changeTargetPath(self, item):
        self.loadInfoWidget.targetPathLabel.setText(item)
        self.targetpath = item

    def openFile(self):
        (filename, kakutyousi) = QFileDialog.getOpenFileName(self, "Open CSV file", "./", "CSV files (*.csv)")
        if filename:
            self.targetpath = filename
            self.loadEvent()
            return filename
        else:
            return None

