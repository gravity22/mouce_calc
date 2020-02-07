from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *

from mouse_calc.ui.loadingnotifywidget import LoadingNotifyWidget

class StatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inner_widget = LoadingNotifyWidget()
        self.addWidget(self.inner_widget)
