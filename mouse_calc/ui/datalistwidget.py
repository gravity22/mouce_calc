from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *

from mouse_calc.lib import *
from mouse_calc.ui.datamanager import DataManager


class DataListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        for item in DataManager.all():
            self.addItem(str(item.id))
            for error in item.errors:
                self.addItem(str(error.id))

