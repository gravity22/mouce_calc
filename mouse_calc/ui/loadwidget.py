import datetime

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
        configs = ConfigManager.get(self.config_id)

        self.innerLayout = QHBoxLayout()
        self.setLayout(self.innerLayout)
        self.loadInfoWidget = LoadInfoWidget(configs)

        self.innerLayout.addWidget(self.loadInfoWidget, 4)

        self.loadInfoWidget.loadButton.clicked.connect(parent.openFile)
        self.loadInfoWidget.loadConfigButton.clicked.connect(self.openConfig)
        self.loadInfoWidget.saveConfigButton.clicked.connect(self.saveConfig)

    def getOptions(self):
        configs = ConfigManager.get(self.config_id)

        w = self.loadInfoWidget.temperature_widgets
        configs["temperature"]["bg_time_init"] = w["bg_time_init"].dateTime().toPyDateTime()
        configs["temperature"]["bg_time_end"] = w["bg_time_end"].dateTime().toPyDateTime()
        configs["temperature"]["tg_time_init"] = w["tg_time_init"].dateTime().toPyDateTime()
        configs["temperature"]["tg_time_end"] = w["tg_time_end"].dateTime().toPyDateTime()
        configs["temperature"]["step_size"] = w["step_size"].value()
        configs["temperature"]["thres_sd_heat"] = w["thres_sd_heat"].value()
        configs["temperature_timerange_predict"] = not (w["temperature_timerange_predict"].isChecked())

        w = self.loadInfoWidget.distance_widgets
        configs["distance"]["bg_time_init"] = w["bg_time_init"].dateTime().toPyDateTime()
        configs["distance"]["bg_time_end"] = w["bg_time_end"].dateTime().toPyDateTime()
        configs["distance"]["tg_time_init"] = w["tg_time_init"].dateTime().toPyDateTime()
        configs["distance"]["tg_time_end"] = w["tg_time_end"].dateTime().toPyDateTime()
        configs["distance"]["step_size"] = w["step_size"].value()
        configs["distance"]["welch_thres"] = w["welch_thres"].value()
        configs["distance_timerange_predict"] = not (w["distance_timerange_predict"].isChecked())

        w = self.loadInfoWidget.cor_widgets
        configs["cor"]["bg_time_init"] = w["bg_time_init"].dateTime().toPyDateTime()
        configs["cor"]["bg_time_end"] = w["bg_time_end"].dateTime().toPyDateTime()
        configs["cor"]["tg_time_init"] = w["tg_time_init"].dateTime().toPyDateTime()
        configs["cor"]["tg_time_end"] = w["tg_time_end"].dateTime().toPyDateTime()
        configs["cor"]["step_size"] = w["step_size"].value()
        configs["cor"]["error_step"] = w["error_step"].value()
        configs["cor"]["sd_num"] = w["sd_num"].value()
        configs["cor_timerange_predict"] = not (w["cor_timerange_predict"].isChecked())

    def setOptions(self, config_id):
        self.config_id = config_id
        configs = ConfigManager.get(self.config_id)

        w = self.loadInfoWidget.temperature_widgets
        w["bg_time_init"].setDateTime(configs["temperature"]["bg_time_init"])
        w["bg_time_end"].setDateTime(configs["temperature"]["bg_time_end"])
        w["tg_time_init"].setDateTime(configs["temperature"]["tg_time_init"])
        w["tg_time_end"].setDateTime(configs["temperature"]["tg_time_end"])
        w["step_size"].setValue(configs["temperature"]["step_size"])
        w["thres_sd_heat"].setValue(configs["temperature"]["thres_sd_heat"])

        w = self.loadInfoWidget.distance_widgets
        w["bg_time_init"].setDateTime(configs["distance"]["bg_time_init"])
        w["bg_time_end"].setDateTime(configs["distance"]["bg_time_end"])
        w["tg_time_init"].setDateTime(configs["distance"]["tg_time_init"])
        w["tg_time_end"].setDateTime(configs["distance"]["tg_time_end"])
        w["step_size"].setValue(configs["distance"]["step_size"])
        w["welch_thres"].setValue(configs["distance"]["welch_thres"])

        w = self.loadInfoWidget.cor_widgets
        w["bg_time_init"].setDateTime(configs["cor"]["bg_time_init"])
        w["bg_time_end"].setDateTime(configs["cor"]["bg_time_end"])
        w["tg_time_init"].setDateTime(configs["cor"]["tg_time_init"])
        w["tg_time_end"].setDateTime(configs["cor"]["tg_time_end"])
        w["step_size"].setValue(configs["cor"]["step_size"])
        w["error_step"].setValue(configs["cor"]["error_step"])
        w["sd_num"].setValue(configs["cor"]["sd_num"])

    def loadEvent(self):
        self.getOptions()
        datas = {}
        datas["datapath"] = self.targetpath
        datas["configs"] = ConfigManager.get(self.config_id)
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

    def openConfig(self):
        (filename, kakutyousi) = QFileDialog.getOpenFileName(self, "Open Json file", "./", "JSON files (*.json)")
        if filename:
            config_id = ConfigManager.file_open(filename)
            self.setOptions(config_id)
        else:
            return None

    def saveConfig(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.AnyFile)
        (filename, kakutyousi) = dialog.getSaveFileName(self, "Save Json file", "./", "JSON files (*.json)")
        if filename:
            ConfigManager.file_save(self.config_id, filename)
