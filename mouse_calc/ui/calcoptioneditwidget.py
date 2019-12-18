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


class CalcOptionEditWidget(QWidget):
    calcSignal = pyqtSignal(object)
    resetSignal = pyqtSignal()

    def __init__(self, configs={}):
        super().__init__()

        self.option_value = configs
        self.init_option_value = self.option_value

        self.edit_layout = QVBoxLayout()
        for label, data in self.option_value.items():
            layout = QHBoxLayout()

            label_widget = QLabel(label)

            if type(data) is QDateTime:
                edit_widget = QDateTimeEdit(data)
                edit_widget.setCalendarPopup(True)
                edit_widget.dateTimeChanged.connect(lambda dt, label=label: self.option_value.update({label: dt.toPyDateTime()}))
            elif type(data) is int:
                edit_widget = QSpinBox()
                edit_widget.setValue(data)
                edit_widget.valueChanged.connect(lambda state, label=label: self.option_value.update({label: state}))
            elif type(data) is float:
                edit_widget = QDoubleSpinBox()
                edit_widget.setValue(data)
                edit_widget.setSingleStep(0.1)
                edit_widget.valueChanged.connect(lambda state, label=label: self.option_value.update({label: state}))
            elif type(data) is pd._libs.tslibs.timestamps.Timestamp:
                data = QDateTime(data)
                edit_widget = QDateTimeEdit(data)
                edit_widget.setCalendarPopup(True)
                edit_widget.dateTimeChanged.connect(lambda dt, label=label: self.option_value.update({label: dt.toPyDateTime()}))
            elif type(data) is datetime.datetime:
                data = QDateTime(data)
                edit_widget = QDateTimeEdit(data)
                edit_widget.setCalendarPopup(True)
                edit_widget.dateTimeChanged.connect(lambda dt, label=label: self.option_value.update({label: dt.toPyDateTime()}))
            else:
                print(label, data, file=sys.stderr)
                raise

            layout.addWidget(label_widget)
            layout.addWidget(edit_widget)
            self.edit_layout.addLayout(layout)

        layout = QHBoxLayout()
        self.doButton = QPushButton("Calc")
        self.doButton.clicked.connect(self.callCalc)
        self.resetButton = QPushButton("Reset")
        self.resetButton.clicked.connect(self.callReset)
        layout.addWidget(self.doButton)
        layout.addWidget(self.resetButton)
        self.edit_layout.addLayout(layout)

        self.setLayout(self.edit_layout)

    def callCalc(self):
        print(self.option_value)
        self.calcSignal.emit(self.option_value)

    def callReset(self):
        self.resetSignal.emit()
        self.option_value = self.init_option_value
