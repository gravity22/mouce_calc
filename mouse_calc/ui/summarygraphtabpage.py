from mouse_calc.ui.summarygraphwidget import SummaryGraphWidget

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *


class SummaryGraphTabPage(QTabWidget):
    def __init__(self, config_id, data_ids=[]):
        super().__init__()
        self.summarys=[]
        for index, data_id in enumerate(data_ids):
            summarygraphwidget = SummaryGraphWidget(data_id, config_id=config_id)
            self.summarys.append(summarygraphwidget)
            self.addTab(summarygraphwidget, "{}".format(index+1))
