from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *

from mouse_calc.lib import *
from mouse_calc.ui.loadinfowidget import LoadInfoWidget
from mouse_calc.ui.configmanager import ConfigManager


class LoadWidget(QWidget):
    targetpath = ""
    loadSignal = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_id = ConfigManager.default()
        self.configs = ConfigManager.get(self.config_id)

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
        datas["config_id"] = self.config_id
        self.loadSignal.emit(datas)

    def openFile(self):
        (filename, kakutyousi) = QFileDialog.getOpenFileName(self, "Open CSV file", "./", "CSV files (*.csv)")
        if filename:
            self.targetpath = filename
            self.loadEvent()
            return filename
        else:
            return None

