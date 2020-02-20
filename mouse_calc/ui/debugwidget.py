import sys
from io import TextIOWrapper

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *


class LogSignal(QObject):
    signal_str = pyqtSignal(str)
    def __init__(self):
        QObject.__init__(self)


class QtIO(TextIOWrapper):
    def __init__(self, stream):
        super().__init__(stream.buffer, encoding=stream.encoding, errors=stream.errors)
        self.signalobj = LogSignal()

    def write(self, s):
        super().write(s)
        self.signalobj.signal_str.emit(s)

    def connect(self, func):
        self.signalobj.signal_str.connect(func)


sys.stdout = qtio = QtIO(sys.stdout)

class DebugWidget(QDockWidget):
    def __init__(self, name):
        super().__init__(name)
        self.textarea = QTextEdit()
        self.textarea.setReadOnly(True)
        self.setWidget(self.textarea)
        sys.stdout.connect(self.write)

    def write(self, s):
        self.textarea.insertPlainText(s)
