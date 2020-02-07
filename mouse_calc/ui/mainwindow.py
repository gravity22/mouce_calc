from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *

from mouse_calc.ui.mainwidget import MainWidget
from mouse_calc.ui.debugwidget import DebugWidget
from mouse_calc.ui.filelistwidget import FileListWidget
from mouse_calc.ui.statisticswidget import StatisticsWidget
from mouse_calc.ui.datamanager import DataType, ErrorType, DataManager
from mouse_calc.ui.datalistwidget import DataListWidget
from mouse_calc.ui.loadingnotifywidget import LoadingNotifyWidget
from mouse_calc.ui.statusbar import StatusBar


class MainWindow(QMainWindow):
    filelistWidget = None
    debugWidget = None

    def __init__(self):
        super().__init__()

        self.initUI()
        self.threadpool = QThreadPool()

        self.statusBar = StatusBar()
        self.setStatusBar(self.statusBar)

    def initUI(self):
        self.initMenuBar()

        self.mainWidget = MainWidget(self)
        self.setCentralWidget(self.mainWidget)

        self.openDebugWidget()
        self.openFileListWidget()

    def openDebugWidget(self):
        if self.debugWidget:
            self.debugWidget.show()
        else:
            self.debugWidget = DebugWidget("debug console")
        self.addDockWidget(Qt.BottomDockWidgetArea, self.debugWidget)

    def openFileListWidget(self):
        if self.filelistWidget:
            self.filelistWidget.show()
        else:
            self.filelistWidget = FileListWidget("file list")
            self.filelistWidget.listwidget.itemClicked.connect(self.selectedFile)
            self.mainWidget.newwidget_signal.connect(self.addNewWidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.filelistWidget)

    def openDMWidget(self):
        self.dmwidget = DataListWidget()
        self.dmwidget.show()

    def openLMWidget(self):
        self.lmwidget = LoadingNotifyWidget()
        self.lmwidget.show()

    def openMaxTemperatureStatisticsWidget(self):
        self.statisticswidget = StatisticsWidget(datatype=ErrorType.MAX_TEMPERATURE_ERROR)
        self.statisticswidget.show()

    def openMinTemperatureStatisticsWidget(self):
        self.statisticswidget = StatisticsWidget(datatype=ErrorType.MIN_TEMPERATURE_ERROR)
        self.statisticswidget.show()

    def openDistanceStatisticsWidget(self):
        self.statisticswidget = StatisticsWidget(datatype=ErrorType.DISTANCE_ERROR)
        self.statisticswidget.show()

    def openCorStatisticsWidget(self):
        self.statisticswidget = StatisticsWidget(datatype=ErrorType.COR_ERROR)
        self.statisticswidget.show()

    def openSumStatisticsWidget(self):
        self.statisticswidget = StatisticsWidget(datatype=ErrorType.SUM_ERROR)
        self.statisticswidget.show()

    def addNewWidget(self, obj):
        filename = obj["filename"]
        self.filelistWidget.append(filename)

    def openLoadWidget(self):
        self.mainWidget.openLoadPage()

    def openFileActionTrigger(self):
        self.mainWidget.openFile()

    def openConfigFileActionTrigger(self):
        (filename, kakutyousi) = QFileDialog.getOpenFileName(self, "Open Config file", "./", "json files (*.json)")

    def initMenuBar(self):
        menubar = self.menuBar()

        openFileAction = QAction("Open", self)
        openFileAction.setShortcut("Ctrl+O")
        openFileAction.setStatusTip("Open File")
        openFileAction.triggered.connect(self.openFileActionTrigger)

        openDirAction = QAction("Open Directory", self)
        openDirAction.setStatusTip("Directory File")

        openConfigFileAction = QAction("Open Config", self)
        openConfigFileAction .setStatusTip("Config file")
        openConfigFileAction.triggered.connect(self.openConfigFileActionTrigger)

        exitAction = QAction("Exit", self)
        exitAction.setShortcut("Ctrl+Q")
        exitAction.setStatusTip("Exit Application")
        exitAction.triggered.connect(qApp.quit)

        fileMenu = menubar.addMenu('File')
        fileMenu.addAction(openFileAction)
        fileMenu.addAction(openDirAction)
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)

        openLoadWidgetAction = QAction("load window", self)
        openLoadWidgetAction.setStatusTip("Open LoadWindow")
        openLoadWidgetAction.triggered.connect(self.openLoadWidget)

        openDebugConsoleAction = QAction('DebugConsole', self)
        openDebugConsoleAction.setStatusTip("Open DebugConsole")
        openDebugConsoleAction.triggered.connect(self.openDebugWidget)

        openFileListWidgetAction = QAction('File list', self)
        openFileListWidgetAction.setStatusTip("Open filelist view")
        openFileListWidgetAction.triggered.connect(self.openFileListWidget)

        openDMWidgetOpenAction = QAction('Data manager', self)
        openDMWidgetOpenAction.setStatusTip("Open Data Manager")
        openDMWidgetOpenAction.triggered.connect(self.openDMWidget)

        openLMWidgetOpenAction = QAction("Loading information", self)
        openLMWidgetOpenAction.setStatusTip('')
        openLMWidgetOpenAction.triggered.connect(self.openLMWidget)

        windowMenu = menubar.addMenu('Window')
        windowMenu.addAction(openLoadWidgetAction)
        windowMenu.addAction(openDebugConsoleAction)
        windowMenu.addAction(openFileListWidgetAction)
        windowMenu.addAction(openDMWidgetOpenAction)
        windowMenu.addAction(openLMWidgetOpenAction)

        openMaxTemperatureStatisticsWidgetAction = QAction('max temperature statistics', self)
        openMaxTemperatureStatisticsWidgetAction.setStatusTip("Open statistics")
        openMaxTemperatureStatisticsWidgetAction.triggered.connect(self.openMaxTemperatureStatisticsWidget)

        openMinTemperatureStatisticsWidgetAction = QAction('min temperature statistics', self)
        openMinTemperatureStatisticsWidgetAction.setStatusTip("Open statistics")
        openMinTemperatureStatisticsWidgetAction.triggered.connect(self.openMinTemperatureStatisticsWidget)

        openDistanceStatisticsWidgetAction = QAction('distance statistics', self)
        openDistanceStatisticsWidgetAction.setStatusTip("Open statistics")
        openDistanceStatisticsWidgetAction.triggered.connect(self.openDistanceStatisticsWidget)

        openCorStatisticsWidgetAction = QAction('cor statistics', self)
        openCorStatisticsWidgetAction.setStatusTip("Open statistics")
        openCorStatisticsWidgetAction.triggered.connect(self.openCorStatisticsWidget)

        openSumStatisticsWidgetAction = QAction('sum statistics', self)
        openSumStatisticsWidgetAction.setStatusTip("Open statistics")
        openSumStatisticsWidgetAction.triggered.connect(self.openSumStatisticsWidget)

        statisticsMenu = menubar.addMenu('Statistics')
        statisticsMenu.addAction(openMaxTemperatureStatisticsWidgetAction)
        statisticsMenu.addAction(openMinTemperatureStatisticsWidgetAction)
        statisticsMenu.addAction(openDistanceStatisticsWidgetAction)
        statisticsMenu.addAction(openCorStatisticsWidgetAction)
        statisticsMenu.addAction(openSumStatisticsWidgetAction)

    def selectedFile(self, item):
        item = item.text()
        self.mainWidget.changePage(item)
