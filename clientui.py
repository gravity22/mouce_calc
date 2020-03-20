import sys
from io import BytesIO, StringIO
from io import TextIOWrapper
from datetime import timedelta

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
from bokeh.plotting import figure, output_file, save
from bokeh.io.export import get_layout_html

from lib import *

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


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()    

        self.kwargs['progress_callback'] = self.signals.progress        

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class InputForm(QHBoxLayout):
    def __init__(self, name, form_type):
        self.label = QLabel(name)
        self.addWidget(self.label)
        self.form = self.genForm(form_type)
        self.addWidget(self.form)

    def genForm(self, form_type):
        if form_type == "integer" or form_type == "int" or form_type == "float":
            return QSpinBox()
        elif form_type == "datetime":
            form = QDateTimeEdit()
            form.setCalendarPopup(True)
            return form
        elif form_type == "text":
            return QTextEdit()
        else:
            raise


def suggestInputForm(name, value):
    if type(data) is QDateTime or type(data) is pd._libs.tslibs.timestamps.Timestamp or type(dat) is datetime.datetime:
        return InputForm(name, value, "datetime")
    elif type(data) is int or type(data) is float:
        edit_widget = QSpinBox()
        edit_widget.setValue(data)
    elif type(data) is pd._libs.tslibs.timestamps.Timestamp:
        data = QDateTime(data)
        edit_widget = QDateTimeEdit(data)
        edit_widget.setCalendarPopup(True)
    elif type(data) is datetime.datetime:
        data = QDateTime(data)
        edit_widget = QDateTimeEdit(data)
        edit_widget.setCalendarPopup(True)
    else:
        print(data, file=sys.stderr)
        raise


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



class GraphViewWidget(FigureCanvas):
    press = None
    translationInitSignal = pyqtSignal()
    translationSignal = pyqtSignal(object)
    translationEndSiganal = pyqtSignal()
    zoomSelectSignal = pyqtSignal(object)
    zoomDecideSignal = pyqtSignal()
    requireRedrawSignal = pyqtSignal()

    def __init__(self, parent=None, width=5, height=4, dpi=100, title="example"):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.twinx = None
        super().__init__(self.fig)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setFocus()
        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.artists = []

        self.setTitle(title)
        self.initEventCallBack()

    def initEventCallBack(self):
        self.button_press_event = None
        self.button_release_event = None
        self.motion_notify_event = None
        self.key_press_event = None
        self.rectangle_selector = None

        self.modechange("zoom")

    def resetEventCallBack(self):
        if self.button_press_event:
            self.mpl_disconnect(self.button_press_event)
        self.button_press_event = None

        if self.button_release_event:
            self.mpl_disconnect(self.button_release_event)
        self.button_release_event = None

        if self.motion_notify_event:
            self.mpl_disconnect(self.motion_notify_event)
        self.motion_notify_event = None

        if self.key_press_event:
            self.mpl_disconnect(self.key_press_event)
        self.key_press_event = None

        if self.rectangle_selector:
            self.rectangle_selector.set_visible(False)
            self.rectangle_selector.set_active(False)
        self.rectangle_selector = None

    def modechange(self, mode):
        self.resetEventCallBack()
        if mode=="translation":
            self.modeTranslation()
        elif mode=="zoom":
            self.modeZoom()
        self.requireRedrawSignal.emit()

    def modeTranslation(self):
        self.button_press_event = self.mpl_connect("button_press_event", self.translation_on_press)
        self.button_release_event = self.mpl_connect("button_release_event", self.translation_on_release)
        self.motion_notify_event = self.mpl_connect("motion_notify_event", self.translation_on_motion)

    def modeZoom(self):
        self.rectangle_selector = RectangleSelector(
                self.axes,
                self.zoom_select_callback,
                drawtype="box",
                useblit=True,
                button=[1],
                interactive=True)
        self.key_press_event = self.mpl_connect("key_press_event", self.zoom_key_press)

    def updateCanvas(self):
        self.clear()

    def plot(self, x, y, label=None, twinx=False):
        if twinx:
            if self.twinx is None:
                self.twinx = self.axes.twinx()
                self.twinx.set_zorder(-0.1)
            ax = self.twinx
            self.axes.patch.set_visible(False)
        else:
            ax = self.axes

        line = ax.plot(x, y, label=label)
        if label:
            line[0].set_label(label)
            self.axes.legend()
        self.artists.append(line)

    def scatter(self, x, y, label=None, twinx=False):
        scatter = self.axes.scatter(x, y,  s=0.4)
        if label:
            scatter.set_label(label)
            self.axes.legend()
        self.artists.append(scatter)

    def getXlim(self):
        return self.axes.get_xlim()

    def getYlim(self, graphname="main"):
        return self.axes.get_ylim()

    def setXlim(self, rng, graphname="main"):
        self.axes.set_xlim(rng)

    def setYlim(self, rng, graphname="main"):
        self.axes.set_ylim(rng)

    def clear(self):
        self.artists = []
        self.axes.clear()

    def setTitle(self, title):
        self.axes.set_title(title)

    def translation_on_press(self, event):
        xlim = self.getXlim()
        ylim = self.getYlim()
        self.press = (event.x, event.y, xlim, ylim)
        self.translationInitSignal.emit()

    def translation_on_motion(self, event):
        if self.press is None:
            return
        xpress, ypress, xlim, ylim = self.press
        # FIXME: 気合で決めてるから良くない
        dx = (event.x - xpress) * -0.01
        dy = (event.y - ypress) * -0.01
        self.translationSignal.emit({"dx": dx, "dy": dy})

    def translation_on_release(self, event):
        self.press = None
        self.translationEndSiganal.emit()

    def zoom_select_callback(self, eclick, erelease):
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        self.zoomSelectSignal.emit({
            "xdata_init": min(x1, x2),
            "xdata_end": max(x1, x2),
            "ydata_init": min(y1, y2),
            "ydata_end": max(y1, y2),
        })

    def zoom_key_press(self, event):
        if event.key in ["enter"] and self.rectangle_selector.active:
            print("emit")
            self.zoomDecideSignal.emit()

        #if event.key in [] and self.rectangle_selector.active:


class GraphPageWidget(QWidget):
    def __init__(self, parent, page_name, x_data, y_data, config={}, graphoptions={}):
        super().__init__(parent=parent)
        self.parentwidget = parent
        self.threadpool = QThreadPool()

        self.config = config
        self.datas = []
        self.xlim = None
        self.ylim = None
        self.nowTranslation = None
        self.nowZooming = None
        self.history_index = -1
        self.limhistory = []
        self.require_updategraph = False

        self.appendData(x_data, y_data, "data", graphoptions)

        self.toolbar = QToolBar()
        self.inner_layout = QHBoxLayout()

        self.toolbar_select_action = self.toolbar.addAction("Select")
        self.toolbar_zoom_action = self.toolbar.addAction("Zoom")
        self.toolbar_back_action = self.toolbar.addAction("back")
        self.toolbar_next_action = self.toolbar.addAction("next")
        self.toolbar_reset_action = self.toolbar.addAction("reset")

        vbox = QVBoxLayout()
        vbox.addWidget(self.toolbar)
        vbox.addLayout(self.inner_layout)
        self.setLayout(vbox)

        self.graphViewWidget = GraphViewWidget(title=page_name)
        self.graphViewWidget.translationInitSignal.connect(self.translationInitEvent)
        self.graphViewWidget.translationSignal.connect(self.translationEvent)
        self.graphViewWidget.translationEndSiganal.connect(self.translationEndEvent)
        self.graphViewWidget.zoomSelectSignal.connect(self.zoomSelectEvent)
        self.graphViewWidget.zoomDecideSignal.connect(self.zoomDecideEvent)
        self.graphViewWidget.requireRedrawSignal.connect(self.updateGraph)

        self.calcOptionEditWidget = CalcOptionEditWidget(self.config)
        self.calcOptionEditWidget.calcSignal.connect(self.callCalcProcess)

        self.inner_layout.addWidget(self.graphViewWidget, 4)
        self.inner_layout.addWidget(self.calcOptionEditWidget, 1)

        self.toolbar_select_action.triggered.connect(lambda b, graphview=self.graphViewWidget: graphview.modechange("translation"))
        self.toolbar_zoom_action.triggered.connect(lambda b, graphview=self.graphViewWidget: graphview.modechange("zoom"))
        self.toolbar_back_action.triggered.connect(self.backLimHistory)
        self.toolbar_next_action.triggered.connect(self.nextLimHistory)
        self.toolbar_reset_action.triggered.connect(self.resetLim)

        self.updateGraph()

    def appendData(self, x, y, name, options={}):
        self.require_updategraph = True
        self.datas.append((name, x, y, options))

    def updateGraph(self):
        if self.require_updategraph is True:
            self.graphViewWidget.clear()
            for name, x, y, options in self.datas:
                graphtype = options.get("graphtype")
                twinx = options.get("twinx")
                if graphtype == "scatter":
                    self.graphViewWidget.scatter(x, y, label=name, twinx=twinx)
                else:
                    self.graphViewWidget.plot(x, y, label=name, twinx=twinx)
            self.require_updategraph = False

        if self.xlim:
            self.graphViewWidget.setXlim(self.xlim)
        else:
            self.xlim = self.graphViewWidget.getXlim()
        if self.ylim:
            self.graphViewWidget.setYlim(self.ylim)
        else:
            self.ylim = self.graphViewWidget.getYlim()

        self.graphViewWidget.draw()

        if self.history_index == -1:
            self.updateLimHistory()

    def updateLimHistory(self):
        self.history_index += 1
        self.limhistory.insert(self.history_index, (self.xlim, self.ylim))

    def resetLim(self):
        self.history_index = 0
        xlim, ylim = self.limhistory[self.history_index]
        self.xlim = xlim
        self.ylim = ylim
        self.updateGraph()

    def nextLimHistory(self):
        if self.history_index+1 < len(self.limhistory):
            self.history_index += 1
        xlim, ylim = self.limhistory[self.history_index]
        self.xlim = xlim
        self.ylim = ylim
        self.updateGraph()

    def backLimHistory(self):
        if self.history_index-1 >= 0:
            self.history_index -= 1
        xlim, ylim = self.limhistory[self.history_index]
        self.xlim = xlim
        self.ylim = ylim
        self.updateGraph()

    def translationInitEvent(self):
        self.nowTranslation = (self.xlim, self.ylim)

    def translationEvent(self, obj):
        if self.nowTranslation is None:
            return

        dx = obj["dx"]
        dy = obj["dy"]
        xlim, ylim =  self.nowTranslation

        if xlim and dx:
            min_value, max_value = xlim 
            if type(max_value) is QDateTime or type(max_value) is pd._libs.tslibs.timestamps.Timestamp or type(max_value) is datetime.datetime:
                dx = timedelta(dx)
            self.xlim = (min_value+dx, max_value+dx)

        if ylim and dy:
            min_value, max_value = ylim 
            self.ylim = (min_value+dy, max_value+dy)

        self.updateGraph()
        self.updateLimHistory()

    def translationEndEvent(self):
        self.nowTranslation = None

    def zoomSelectEvent(self, obj):
        xdata_init = obj["xdata_init"]
        xdata_end = obj["xdata_end"]
        ydata_init = obj["ydata_init"]
        ydata_end = obj["ydata_end"]
        self.nowZooming = (xdata_init, xdata_end, ydata_init, ydata_end)

    def zoomDecideEvent(self):
        if self.nowZooming:
            xdata_init, xdata_end, ydata_init, ydata_end = self.nowZooming
            print(xdata_init, xdata_end, file=sys.stderr)
            if type(self.xlim[0]) is QDateTime or type(self.xlim[0]) is pd._libs.tslibs.timestamps.Timestamp or type(self.xlim[0]) is datetime.datetime:
                xdata_init = matplotlib.dates.num2date(xdata_init)
                xdata_end = matplotlib.dates.num2date(xdata_end)
            self.xlim = (xdata_init, xdata_end)
            self.ylim = (ydata_init, ydata_end)
        self.updateGraph()
        self.updateLimHistory()

    def callCalcProcess(self, option):
        worker = Worker(self.calcProcess, option)
        #worker.signals.result.connect(self.tempGraphShow)
        self.threadpool.start(worker)

    def calcProcess(self, option, progress_callback):
        pass


class MaxTemperatureGraphPageWidget(GraphPageWidget):
    counter = 1

    def __init__(self, parent, page_name, data, config=None):
        x_data = data.get_col(TIME)
        y_data = data.get_col(MAX_TEMPERATURE)
        super().__init__(parent, page_name, x_data, y_data, config)
        self.data = data
        self.xlim = (min(x_data), max(x_data))
        self.updateGraph()
        self.ylim = self.graphViewWidget.getYlim()

    def calcProcess(self, option, progress_callback):
        bg_time_init = option["bg_time_init"]
        bg_time_end = option["bg_time_end"]
        tg_time_init = option["tg_time_init"]
        tg_time_end = option["tg_time_end"]
        step_size = option["step_size"]
        thres_sd_heat = option["thres_sd_heat"]
        error_data, _ = temperature_process(self.data, bg_time_init, bg_time_end, tg_time_init, tg_time_end, step_size=step_size, thres_sd_heat=thres_sd_heat, save_svg=False, show_graph=False)
        x = error_data.get_col(TIME)
        y = error_data.get_col(TEMPERATURE_ERROR_DATA)
        label = "error" + str(self.counter)
        self.appendData(x, y, label, {"twinx": True})
        self.counter += 1
        self.updateGraph()


class MinTemperatureGraphPageWidget(GraphPageWidget):
    counter = 1
    def __init__(self, parent, page_name, data, config=None):
        x_data = data.get_col(TIME)
        y_data = data.get_col(MIN_TEMPERATURE)
        super().__init__(parent, page_name, x_data, y_data, config)
        self.data = data
        self.xlim = (min(x_data), max(x_data))
        self.updateGraph()
        self.ylim = self.graphViewWidget.getYlim()

    def calcProcess(self, option, progress_callback):
        bg_time_init = option["bg_time_init"]
        bg_time_end = option["bg_time_end"]
        tg_time_init = option["tg_time_init"]
        tg_time_end = option["tg_time_end"]
        step_size = option["step_size"]
        thres_sd_heat = option["thres_sd_heat"]
        error_data, _ = temperature_process(self.data, bg_time_init, bg_time_end, tg_time_init, tg_time_end, step_size=step_size, thres_sd_heat=thres_sd_heat, save_svg=False, show_graph=False)
        x = error_data.get_col(TIME)
        y = error_data.get_col(TEMPERATURE_ERROR_DATA)
        label = "error" + str(self.counter)
        self.appendData(x, y, label, {"twinx": True})
        self.counter += 1
        self.updateGraph()


class DistanceGraphPageWidget(GraphPageWidget):
    counter = 1
    def __init__(self, parent, page_name, data, config=None):
        x_data = data.get_col(TIME)
        y_data = data.get_col(DISTANCE)
        super().__init__(parent, page_name, x_data, y_data, config)
        self.data = data
        self.xlim = (min(x_data), max(x_data))
        self.updateGraph()
        self.ylim = self.graphViewWidget.getYlim()

    def calcProcess(self, option, progress_callback):
        bg_time_init = option["bg_time_init"]
        bg_time_end = option["bg_time_end"]
        tg_time_init = option["tg_time_init"]
        tg_time_end = option["tg_time_end"]
        step_size = option["step_size"]
        welch_thres = option["welch_thres"]
        error_data, _ = distance_process(self.data, bg_time_init, bg_time_end, tg_time_init, tg_time_end, step_size=step_size, save_svg=False, show_graph=False, welch_thres=welch_thres)
        x = error_data.get_col(TIME)
        y = error_data.get_col(ERROR_VALUE)
        label = "error" + str(self.counter)
        self.appendData(x, y, label, {"twinx": True})
        self.counter += 1
        self.updateGraph()


class CorGraphPageWidget(GraphPageWidget):
    counter = 1
    addpageSignal = pyqtSignal(object)

    def __init__(self, parent, page_name, data, config=None):
        self.data = data
        self.window_data = window_process(self.data, 8)
        x_data = np.log2(self.window_data.get_col(DISTANCE_MEAN))
        y_data = self.window_data.get_col(MAX_TEMPERATURE_MEAN)
        super().__init__(parent, page_name, x_data, y_data, config, {"graphtype": "scatter"})
        self.updateGraph()
        self.ylim = self.graphViewWidget.getYlim()
        self.graphViewWidget.modechange("zoom")

    def calcProcess(self, option, progress_callback):
        bg_time_init = option["bg_time_init"]
        bg_time_end = option["bg_time_end"]
        tg_time_init = option["tg_time_init"]
        tg_time_end = option["tg_time_end"]
        step_size = option["step_size"]
        sd_num = option["sd_num"]
        error_step = option["error_step"]
        error_data, pb_info = cor_process(self.data, bg_time_init, bg_time_end, tg_time_init, tg_time_end, step_size=step_size, SD_NUM=sd_num, ERROR_STEP=error_step, save_svg=False, show_graph=False)

        slope = pb_info["slope"]
        n = pb_info["n"]
        n_plus = pb_info["n_plus"]
        n_minus = pb_info["n_minus"]

        t = np.log2(self.window_data.get_col(DISTANCE_MEAN))
        x = np.linspace(min(t), max(t), t.size)

        counter =  str(self.counter)

        y = x * slope + n
        self.appendData(x, y, "error"+counter)

        y = x * slope + n_plus
        self.appendData(x, y, "error"+counter)

        y = x * slope + n_minus
        self.appendData(x, y, "error"+counter)

        self.updateGraph()

        x_data = error_data.get_col(TIME)
        y_data = error_data.get_col(COR_ERROR_VALUE)
        name = "cor error"+counter
        self.addpageSignal.emit({"x_data": x_data, "y_data": y_data, "name": name})

        self.counter += 1



class GraphWidget(QTabWidget):
    def __init__(self, data, configs):
        super().__init__()
        self.data = data

        if configs["temperature_timerange_predict"] or configs["distance_timerange_predict"] or configs["cor_timerange_predict"]:
            time_data = data.get_col(TIME)
            min_time = min(time_data)
            median_time = pd.Timestamp.fromordinal(int(time_data.apply(lambda x: x.toordinal()).median()))
            max_time = max(time_data)

        temperature_config = configs["temperature"]
        if configs["temperature_timerange_predict"]:
            temperature_config["bg_time_init"] = min_time
            temperature_config["bg_time_end"] = median_time
            temperature_config["tg_time_init"] = median_time
            temperature_config["tg_time_end"] = max_time

        maxTemperaturePage = MaxTemperatureGraphPageWidget(self, "max temperature", self.data, temperature_config)
        self.addTab(maxTemperaturePage, "max temperature")

        minTemperaturePage = MinTemperatureGraphPageWidget(self, "min temperature", self.data, temperature_config)
        self.addTab(minTemperaturePage, "min temperature")

        distance_config = configs["distance"]
        if configs["distance_timerange_predict"]:
            distance_config["bg_time_init"] = min_time
            distance_config["bg_time_end"] = median_time
            distance_config["tg_time_init"] = median_time
            distance_config["tg_time_end"] = max_time
        temperaturePage = DistanceGraphPageWidget(self, "distance", self.data, distance_config)
        self.addTab(temperaturePage, "distance")

        cor_config = configs["cor"]
        if configs["cor_timerange_predict"]:
            cor_config["bg_time_init"] = min_time
            cor_config["bg_time_end"] = median_time
            cor_config["tg_time_init"] = median_time
            cor_config["tg_time_end"] = max_time
        temperaturePage = CorGraphPageWidget(self, "cor", self.data, cor_config)
        temperaturePage.addpageSignal.connect(self.addtab)
        self.addTab(temperaturePage, "cor")

    def addtab(self, obj):
        x_data = obj["x_data"]
        y_data = obj["y_data"]
        name = obj["name"]
        widget = GraphPageWidget(self, name, x_data, y_data)
        self.addTab(widget, name)

class LoadInfoWidget(QWidget):
    temperature_widgets = {}
    distance_widgets = {}
    cor_widgets = {}

    def __init__(self, configs):
        super().__init__()
        self.innerLayout = QGridLayout()
        self.setLayout(self.innerLayout)

        # temperature option
        temperature_config = configs["temperature"]
        self.temperature_group = QGroupBox("temperature")
        vbox = QVBoxLayout()

        temperature_time_group = QGroupBox("manual time range")
        temperature_time_group.setCheckable(True)
        temperature_time_group.setChecked(False)
        self.temperature_widgets["temperature_timerange_predict"] = temperature_time_group
        vbox.addWidget(temperature_time_group)
        predict_vbox = QVBoxLayout()
        temperature_time_group.setLayout(predict_vbox)

        layout = QHBoxLayout()
        label_widget = QLabel("bg_time_init")
        edit_widget = QDateTimeEdit(temperature_config["bg_time_init"])
        edit_widget.setCalendarPopup(True)
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        predict_vbox.addLayout(layout)
        self.temperature_widgets["bg_time_init"] = edit_widget

        layout = QHBoxLayout()
        label_widget = QLabel("bg_time_end")
        edit_widget = QDateTimeEdit(temperature_config["bg_time_end"])
        edit_widget.setCalendarPopup(True)
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        predict_vbox.addLayout(layout)
        self.temperature_widgets["bg_time_end"] = edit_widget

        layout = QHBoxLayout()
        label_widget = QLabel("tg_time_init")
        edit_widget = QDateTimeEdit(temperature_config["tg_time_init"])
        edit_widget.setCalendarPopup(True)
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        predict_vbox.addLayout(layout)
        self.temperature_widgets["tg_time_init"] = edit_widget

        layout = QHBoxLayout()
        label_widget = QLabel("tg_time_end")
        edit_widget = QDateTimeEdit(temperature_config["tg_time_end"])
        edit_widget.setCalendarPopup(True)
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        predict_vbox.addLayout(layout)
        self.temperature_widgets["tg_time_end"] = edit_widget

        layout = QHBoxLayout()
        label_widget = QLabel("step_size")
        edit_widget = QSpinBox()
        edit_widget.setValue(temperature_config["step_size"])
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        vbox.addLayout(layout)
        self.temperature_widgets["step_size"] = edit_widget

        layout = QHBoxLayout()
        label_widget = QLabel("thres_sd_heat")
        edit_widget = QDoubleSpinBox()
        edit_widget.setValue(temperature_config["thres_sd_heat"])
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        vbox.addLayout(layout)
        self.temperature_widgets["thres_sd_heat"] = edit_widget

        enable_loading_checkbox = QCheckBox("enable load time calc")
        vbox.addWidget(enable_loading_checkbox)
        self.temperature_widgets["enable_loading_calculation"] = enable_loading_checkbox

        self.temperature_group.setLayout(vbox)
        self.innerLayout.addWidget(self.temperature_group, 0, 0)

        # distance option
        distance_config = configs["distance"]
        self.distance_group = QGroupBox("distance")
        vbox = QVBoxLayout()

        distance_time_group = QGroupBox("manual time range")
        distance_time_group.setCheckable(True)
        distance_time_group.setChecked(False)
        self.distance_widgets["distance_timerange_predict"] = distance_time_group
        vbox.addWidget(distance_time_group)
        predict_vbox = QVBoxLayout()
        distance_time_group.setLayout(predict_vbox)

        layout = QHBoxLayout()
        label_widget = QLabel("bg_time_init")
        edit_widget = QDateTimeEdit(distance_config["bg_time_init"])
        edit_widget.setCalendarPopup(True)
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        predict_vbox.addLayout(layout)
        self.distance_widgets["bg_time_init"] = edit_widget

        layout = QHBoxLayout()
        label_widget = QLabel("bg_time_end")
        edit_widget = QDateTimeEdit(distance_config["bg_time_end"])
        edit_widget.setCalendarPopup(True)
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        predict_vbox.addLayout(layout)
        self.distance_widgets["bg_time_end"] = edit_widget

        layout = QHBoxLayout()
        label_widget = QLabel("tg_time_init")
        edit_widget = QDateTimeEdit(distance_config["tg_time_init"])
        edit_widget.setCalendarPopup(True)
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        predict_vbox.addLayout(layout)
        self.distance_widgets["tg_time_init"] = edit_widget

        layout = QHBoxLayout()
        label_widget = QLabel("tg_time_end")
        edit_widget = QDateTimeEdit(distance_config["tg_time_end"])
        edit_widget.setCalendarPopup(True)
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        predict_vbox.addLayout(layout)
        self.distance_widgets["tg_time_end"] = edit_widget

        layout = QHBoxLayout()
        label_widget = QLabel("step_size")
        edit_widget = QSpinBox()
        edit_widget.setValue(distance_config["step_size"])
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        vbox.addLayout(layout)
        self.distance_widgets["step_size"] = edit_widget

        layout = QHBoxLayout()
        label_widget = QLabel("welch_thres")
        edit_widget = QDoubleSpinBox()
        edit_widget.setValue(distance_config["welch_thres"])
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        vbox.addLayout(layout)
        self.distance_widgets["welch_thres"] = edit_widget

        enable_loading_checkbox = QCheckBox("enable load time calc")
        vbox.addWidget(enable_loading_checkbox)
        self.distance_widgets["enable_loading_calculation"] = enable_loading_checkbox

        self.distance_group.setLayout(vbox)
        self.innerLayout.addWidget(self.distance_group, 0, 1)

        # cor option
        cor_config = configs["cor"]
        self.cor_group = QGroupBox("cor")
        vbox = QVBoxLayout()

        cor_time_group = QGroupBox("manual time range")
        cor_time_group.setCheckable(True)
        cor_time_group.setChecked(False)
        self.cor_widgets["cor_timerange_predict"] = cor_time_group
        vbox.addWidget(cor_time_group)
        predict_vbox = QVBoxLayout()
        cor_time_group.setLayout(predict_vbox)

        layout = QHBoxLayout()
        label_widget = QLabel("bg_time_init")
        edit_widget = QDateTimeEdit(cor_config["bg_time_init"])
        edit_widget.setCalendarPopup(True)
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        predict_vbox.addLayout(layout)
        self.cor_widgets["bg_time_init"] = edit_widget

        layout = QHBoxLayout()
        label_widget = QLabel("bg_time_end")
        edit_widget = QDateTimeEdit(cor_config["bg_time_end"])
        edit_widget.setCalendarPopup(True)
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        predict_vbox.addLayout(layout)
        self.cor_widgets["bg_time_end"] = edit_widget

        layout = QHBoxLayout()
        label_widget = QLabel("tg_time_init")
        edit_widget = QDateTimeEdit(cor_config["tg_time_init"])
        edit_widget.setCalendarPopup(True)
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        predict_vbox.addLayout(layout)
        self.cor_widgets["tg_time_init"] = edit_widget

        layout = QHBoxLayout()
        label_widget = QLabel("tg_time_end")
        edit_widget = QDateTimeEdit(cor_config["tg_time_end"])
        edit_widget.setCalendarPopup(True)
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        predict_vbox.addLayout(layout)
        self.cor_widgets["tg_time_end"] = edit_widget

        layout = QHBoxLayout()
        label_widget = QLabel("step_size")
        edit_widget = QSpinBox()
        edit_widget.setValue(cor_config["step_size"])
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        vbox.addLayout(layout)
        self.cor_widgets["step_size"] = edit_widget

        layout = QHBoxLayout()
        label_widget = QLabel("error_step")
        edit_widget = QSpinBox()
        edit_widget.setValue(cor_config["error_step"])
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        vbox.addLayout(layout)
        self.cor_widgets["error_step"] = edit_widget

        layout = QHBoxLayout()
        label_widget = QLabel("sd_num")
        edit_widget = QDoubleSpinBox()
        edit_widget.setValue(cor_config["sd_num"])
        layout.addWidget(label_widget)
        layout.addWidget(edit_widget)
        vbox.addLayout(layout)
        self.cor_widgets["sd_num"] = edit_widget

        enable_loading_checkbox = QCheckBox("enable load time calc")
        vbox.addWidget(enable_loading_checkbox)
        self.cor_widgets["enable_loading_calculation"] = enable_loading_checkbox

        self.cor_group.setLayout(vbox)
        self.innerLayout.addWidget(self.cor_group, 1, 0)

        self.loadButton = QPushButton("Load")
        self.loadConfigButton = QPushButton("Config")
        hbox = QHBoxLayout()
        hbox.addWidget(self.loadButton)
        hbox.addWidget(self.loadConfigButton)
        self.innerLayout.addLayout(hbox, 2, 0)


class LoadOptionWidget(QWidget):
    def __init__(self):
        super().__init__()

class LoadWidget(QWidget):
    targetpath = ""
    loadSignal = pyqtSignal(object)

    default_config = {
        "temperature": {
            "bg_time_init": datetime.datetime.now(),
            "bg_time_end": datetime.datetime.now(),
            "tg_time_init": datetime.datetime.now(),
            "tg_time_end": datetime.datetime.now(),
            "step_size": 8,
            "thres_sd_heat": 1.5,
        },
        "distance": {
            "bg_time_init": datetime.datetime.now(),
            "bg_time_end": datetime.datetime.now(),
            "tg_time_init": datetime.datetime.now(),
            "tg_time_end": datetime.datetime.now(),
            "step_size": 8,
            "welch_thres": 0.5,
        },
        "cor": {
            "bg_time_init": datetime.datetime.now(),
            "bg_time_end": datetime.datetime.now(),
            "tg_time_init": datetime.datetime.now(),
            "tg_time_end": datetime.datetime.now(),
            "step_size": 8,
            "error_step": 1,
            "sd_num": 1.5
        },
        "temperature_timerange_predict": False,
        "distance_timerange_predict": False,
        "cor_timerange_predict": False,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.configs = self.default_config

        self.innerLayout = QHBoxLayout()
        self.setLayout(self.innerLayout)
        self.loadInfoWidget = LoadInfoWidget(self.configs)
        self.loadOptionWidget = LoadOptionWidget()

        self.innerLayout.addWidget(self.loadInfoWidget, 4)
        self.innerLayout.addWidget(self.loadOptionWidget, 1)

        self.loadInfoWidget.loadButton.clicked.connect(parent.openFile)

    def getOptions(self):
        w = self.loadInfoWidget.temperature_widgets
        self.configs["temperature"]["bg_time_init"] = w["bg_time_init"].dateTime().toPyDateTime()
        self.configs["temperature"]["bg_time_end"] = w["bg_time_end"].dateTime().toPyDateTime()
        self.configs["temperature"]["tg_time_init"] = w["tg_time_init"].dateTime().toPyDateTime()
        self.configs["temperature"]["tg_time_end"] = w["tg_time_end"].dateTime().toPyDateTime()
        self.configs["temperature"]["step_size"] = w["step_size"].value()
        self.configs["temperature"]["thres_sd_heat"] = w["thres_sd_heat"].value()
        self.configs["temperature_timerange_predict"] = not (w["temperature_timerange_predict"].isChecked())

        w = self.loadInfoWidget.distance_widgets
        self.configs["distance"]["bg_time_init"] = w["bg_time_init"].dateTime().toPyDateTime()
        self.configs["distance"]["bg_time_end"] = w["bg_time_end"].dateTime().toPyDateTime()
        self.configs["distance"]["tg_time_init"] = w["tg_time_init"].dateTime().toPyDateTime()
        self.configs["distance"]["tg_time_end"] = w["tg_time_end"].dateTime().toPyDateTime()
        self.configs["distance"]["step_size"] = w["step_size"].value()
        self.configs["distance"]["welch_thres"] = w["welch_thres"].value()
        self.configs["distance_timerange_predict"] = not (w["distance_timerange_predict"].isChecked())

        w = self.loadInfoWidget.cor_widgets
        self.configs["cor"]["bg_time_init"] = w["bg_time_init"].dateTime().toPyDateTime()
        self.configs["cor"]["bg_time_end"] = w["bg_time_end"].dateTime().toPyDateTime()
        self.configs["cor"]["tg_time_init"] = w["tg_time_init"].dateTime().toPyDateTime()
        self.configs["cor"]["tg_time_end"] = w["tg_time_end"].dateTime().toPyDateTime()
        self.configs["cor"]["step_size"] = w["step_size"].value()
        self.configs["cor"]["error_step"] = w["error_step"].value()
        self.configs["cor"]["sd_num"] = w["sd_num"].value()
        self.configs["cor_timerange_predict"] = not (w["cor_timerange_predict"].isChecked())

    def loadEvent(self):
        self.getOptions()
        datas = {}
        datas["datapath"] = self.targetpath
        datas["configs"] = self.configs
        self.loadSignal.emit(datas)

    def changeTargetPath(self, item):
        self.loadInfoWidget.targetPathLabel.setText(item)
        self.targetpath = item

    def openFile(self):
        (filename, kakutyousi) = QFileDialog.getOpenFileName(self, "Open CSV file", "./", "CSV files (*.csv)")
        if filename:
            self.targetpath = filename
            self.loadEvent()
            return filename
        else:
            return None


class FileListWidget(QDockWidget):
    def __init__(self, name):
        super().__init__(name)
        self.listwidget = QListWidget()
        self.setWidget(self.listwidget)

    def append(self, item):
        self.listwidget.addItem(item)


class DataItem(QListWidgetItem):
    def __init__(self, name, data_type, data, path=None):
        super().__init__(name)
        self.name = name
        self.data_type = data_type
        self.data_ = data
        self.path = path


class DataListWidget(QWidget):
    data_list = {}
    def __init__(self, name=None):
        super().__init__(name)
        self.listWidget = QListWidget()

    def appendData(self, name, data, path=None):
        item = DataCache(name, "DATA", data, path=path)
        data_list.append(item)
        self.append(item)

    def appendCache(self, name, data):
        item = DataCache(name, "DATA", data, path=path)
        data_list.append(item)
        self.append(item)


class MainWidget(QStackedWidget):
    graphWidgets = {}
    newwidget_signal = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.loadWidget = LoadWidget(self)
        self.loadWidget.loadSignal.connect(self.makeGraph)

        self.dataWidget = DataListWidget()

        self.addWidget(self.loadWidget)
        self.loadWidgetIndex = self.currentIndex()

    def makeGraph(self, datas):
        path = datas["datapath"]
        configs = datas["configs"]
        loader = Loader(path, names=[TIME, MAX_TEMPERATURE, MAX_POS_X, MAX_POS_Y, MIN_TEMPERATURE, MIN_POS_X, MIN_POS_Y])
        loader.set_preprocess(a3_preprocess)

        data = loader.load()
        data = calc_distance(data)

        widget = GraphWidget(data, configs)
        index = self.addWidget(widget)
        self.graphWidgets[path] = index

        self.setCurrentIndex(index)

    def openFile(self):
        filename = self.loadWidget.openFile()
        if filename:
            index = self.currentIndex()
            self.newwidget_signal.emit({"filename": filename, "index": index})

    def openLoadPage(self):
        self.setCurrentIndex(self.loadWidgetIndex)

    def changePage(self, path):
        index = self.graphWidgets[path]
        self.setCurrentIndex(index)


class MainWindow(QMainWindow):
    filelistWidget = None
    debugWidget = None

    def __init__(self):
        super().__init__()

        self.initUI()
        self.threadpool = QThreadPool()

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

        windowMenu = menubar.addMenu('Window')
        windowMenu.addAction(openLoadWidgetAction)
        windowMenu.addAction(openDebugConsoleAction)
        windowMenu.addAction(openFileListWidgetAction)

    def selectedFile(self, item):
        item = item.text()
        self.mainWidget.changePage(item)


app = QApplication(sys.argv)

mainwindow = MainWindow()
mainwindow.show()

sys.exit(app.exec_())
