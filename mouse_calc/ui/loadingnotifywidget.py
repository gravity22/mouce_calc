import sys
import datetime

import pandas as pd

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *

from mouse_calc.ui.loadingmanager import LoadingManager, ProcessType


def clearLayout(layout):
    item = layout.takeAt(0)
    while item:
        if item.layout():
            inner_layout = item.layout()
            clearLayout(inner_layout)
            del inner_layout
        if item.widget():
            widget = item.widget()
            widget.hide()
            del widget
        del item
        item = layout.takeAt(0)

class Item(QListWidgetItem):
    def __init__(self, processtype, config):
        super().__init__()
        self.processtype = processtype
        self.configs = config

        if processtype is ProcessType.MAX_TEMPERATURE:
            self.setText("最高温度")
        elif processtype is ProcessType.DISTANCE:
            self.setText("距離")
        elif processtype is ProcessType.COR:
            self.setText("発熱行動相関")


class OptionViewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.form_widgets = {}
        self.inner_layout = QVBoxLayout()
        self.setLayout(self.inner_layout)

    def resetInnerLayout(self):
        clearLayout(self.inner_layout)

    def makeForms(self, configs):
        self.resetInnerLayout()
        for label, data in configs.items():
            layout = QHBoxLayout()

            label_widget = QLabel(label)

            if type(data) is pd._libs.tslibs.timestamps.Timestamp:
                data = data.to_pydatetime().strftime("%y/%m/%d %H:%M:%S")
            elif type(data) is int or type(data) is float:
                data = str(data)
            data_widget = QLabel(data)

            layout.addWidget(label_widget)
            layout.addWidget(data_widget)
            self.inner_layout.addLayout(layout)
        self.update(self.rect())


class LoadingNotifyWidget(QSplitter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.leftWidget = QWidget()
        self.leftLayout = QVBoxLayout()
        self.leftWidget.setLayout(self.leftLayout)
        self.leftLayoutName = QLabel("計算中プロセス")
        self.listWidget = QListWidget()
        self.leftLayout.addWidget(self.leftLayoutName)
        self.leftLayout.addWidget(self.listWidget)

        self.rightWidget = QWidget()
        self.rightLayout = QVBoxLayout()
        self.rightWidget.setLayout(self.rightLayout)
        self.rightLayoutName = QLabel("詳細")
        self.rightLayoutName.setAlignment(Qt.AlignTop)
        self.rightLayoutName.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.optionViewWidget = OptionViewWidget()
        self.rightLayout.addWidget(self.rightLayoutName)
        self.rightLayout.addWidget(self.optionViewWidget)
        self.rightLayout.addStretch()

        self.addWidget(self.leftWidget)
        self.addWidget(self.rightWidget)

        LoadingManager.connect(self.updateView)
        self.listWidget.itemClicked.connect(self.changeActiveItem)

    def updateView(self):
        self.listWidget.clear()
        for enable, processtype, config in LoadingManager.all():
            if enable:
                item = Item(processtype, config)
                self.listWidget.addItem(item)

    def changeActiveItem(self, item):
        if item.processtype is ProcessType.MAX_TEMPERATURE:
            config = item.configs["temperature"]
        elif item.processtype is ProcessType.DISTANCE:
            config = item.configs["distance"]
        elif item.processtype is ProcessType.COR:
            config = item.configs["cor"]

        self.optionViewWidget.makeForms(config)
