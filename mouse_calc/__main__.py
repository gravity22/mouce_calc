import sys

from mouse_calc.ui.mainwindow import MainWindow
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *


app = QApplication(sys.argv)

mainwindow = MainWindow()
mainwindow.show()

sys.exit(app.exec_())
