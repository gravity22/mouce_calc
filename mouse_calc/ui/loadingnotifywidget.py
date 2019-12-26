from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *

from mouse_calc.ui.loadingmanager import LoadingManager, ProcessType


class LoadingNotifyWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.updateView()

    def updateView(self):
        self.clear()
        for enable, processtype, config in LoadingManager.all():
            if enable:
                item = ""
                if processtype is ProcessType.MAX_TEMPERATURE:
                    item += "max temperature: "
                    item += str(config["temperature"]["thres_sd_heat"])
                elif processtype is ProcessType.DISTANCE:
                    item += "distance: "
                elif processtype is ProcessType.COR:
                    item += "cor: "
                self.addItem(item)
