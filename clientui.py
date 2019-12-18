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

    def barh(self, y, width, height=0.8, left=None, align='center'):
        barh = self.axes.barh(y, width, height=height)
        self.artists.append(barh)

    def yticks(self, tick, label):
        self.axes.set_yticks(tick)
        self.axes.set_yticklabels(label)

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
    def __init__(self, parent, page_name, data_id, config={}, graphoptions={}):
        super().__init__(parent=parent)
        self.parentwidget = parent
        self.threadpool = QThreadPool()
        self.graphoptions = graphoptions

        self.data_id = data_id
        self.config = config
        self.datas = []
        self.xlim = None
        self.ylim = None
        self.nowTranslation = None
        self.nowZooming = None
        self.history_index = -1
        self.limhistory = []
        self.require_updategraph = False

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

        if self.xlim is None:
            self.xlim = self.graphViewWidget.getXlim()
        else:
            self.graphViewWidget.setXlim(self.xlim)

        if self.ylim is None:
            self.ylim = self.graphViewWidget.getYlim()
        else:
            self.graphViewWidget.setYlim(self.ylim)

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
        self.threadpool.start(worker)

    def calcProcess(self, option, progress_callback):
        pass


class MaxTemperatureGraphPageWidget(GraphPageWidget):
    counter = 1

    def __init__(self, parent, page_name, data_id, data, config=None):
        self.data = data
        super().__init__(parent, page_name, data_id, config)

        data = DataManager.get_data(self.data_id)
        x_data = data.get_col(TIME)
        y_data = data.get_col(MAX_TEMPERATURE)
        self.appendData(x_data, y_data, "data", self.graphoptions)

        x_data = self.data.get_col(TIME) 
        self.xlim = (min(x_data), max(x_data))
        self.updateGraph()

    def calcProcess(self, option, progress_callback):
        bg_time_init = option["bg_time_init"]
        bg_time_end = option["bg_time_end"]
        tg_time_init = option["tg_time_init"]
        tg_time_end = option["tg_time_end"]
        step_size = option["step_size"]
        thres_sd_heat = option["thres_sd_heat"]
        label = "error" + str(self.counter)

        q = multiprocessing.Queue()
        f = lambda: q.put(temperature_process(self.data, bg_time_init, bg_time_end, tg_time_init, tg_time_end, step_size=step_size, thres_sd_heat=thres_sd_heat, save_svg=False, show_graph=False))
        p = multiprocessing.Process(target=f)
        p.start()
        error_data, _ = q.get()
        p.join()

        DataManager.append_error(self.data_id, ErrorType.MAX_TEMPERATURE_ERROR, error_data, option)

        x = error_data.get_col(TIME)
        y = error_data.get_col(TEMPERATURE_ERROR_DATA)
        self.appendData(x, y, label, {"twinx": True})
        self.updateGraph()
        self.counter += 1


class MinTemperatureGraphPageWidget(GraphPageWidget):
    counter = 1
    def __init__(self, parent, page_name, data_id, data, config=None):
        self.data = data
        super().__init__(parent, page_name, data_id, config)

        x_data = data.get_col(TIME)
        y_data = data.get_col(MIN_TEMPERATURE)
        self.appendData(x_data, y_data, "data", self.graphoptions)
        self.updateGraph()

    def calcProcess(self, option, progress_callback):
        bg_time_init = option["bg_time_init"]
        bg_time_end = option["bg_time_end"]
        tg_time_init = option["tg_time_init"]
        tg_time_end = option["tg_time_end"]
        step_size = option["step_size"]
        thres_sd_heat = option["thres_sd_heat"]
        label = "error" + str(self.counter)

        q = multiprocessing.Queue()
        f = lambda: q.put(temperature_process(self.data, bg_time_init, bg_time_end, tg_time_init, tg_time_end, step_size=step_size, thres_sd_heat=thres_sd_heat, save_svg=False, show_graph=False))
        p.start()
        error_data, _ = q.get()
        p.join()

        DataManager.append_error(self.data_id, ErrorType.MIN_TEMPERATURE_ERROR, error_data, option)

        x = error_data.get_col(TIME)
        y = error_data.get_col(TEMPERATURE_ERROR_DATA)
        self.appendData(x, y, label, {"twinx": True})
        self.updateGraph()
        self.counter += 1


class DistanceGraphPageWidget(GraphPageWidget):
    counter = 1
    def __init__(self, parent, page_name, data_id, data, config=None):
        self.data = data
        super().__init__(parent, page_name, data_id, config)

        x_data = data.get_col(TIME)
        y_data = data.get_col(DISTANCE)
        self.appendData(x_data, y_data, "data", self.graphoptions)
        self.updateGraph()

    def calcProcess(self, option, progress_callback):
        bg_time_init = option["bg_time_init"]
        bg_time_end = option["bg_time_end"]
        tg_time_init = option["tg_time_init"]
        tg_time_end = option["tg_time_end"]
        step_size = option["step_size"]
        welch_thres = option["welch_thres"]
        label = "error" + str(self.counter)

        q = multiprocessing.Queue()
        f = lambda: q.put(distance_process(self.data, bg_time_init, bg_time_end, tg_time_init, tg_time_end, step_size=step_size, save_svg=False, show_graph=False, welch_thres=welch_thres))
        p = multiprocessing.Process(target=f)
        p.start()
        error_data, _ = q.get()
        p.join()

        DataManager.append_error(self.data_id, ErrorType.DISTANCE_ERROR, error_data, option)

        x = error_data.get_col(TIME)
        y = error_data.get_col(ERROR_VALUE)
        self.appendData(x, y, label, {"twinx": True})
        self.counter += 1
        self.updateGraph()


class CorGraphPageWidget(GraphPageWidget):
    counter = 1
    addpageSignal = pyqtSignal(object)

    def __init__(self, parent, page_name, data_id, data, config=None):
        super().__init__(parent, page_name, data_id, config, {"graphtype": "scatter"})
        self.data = data

        worker = Worker(self.initProcess)
        self.threadpool.start(worker)

    def initProcess(self, progress_callback):
        self.window_data = window_process(self.data, 8)
        x_data = np.log2(self.window_data.get_col(DISTANCE_MEAN))
        y_data = self.window_data.get_col(MAX_TEMPERATURE_MEAN)
        self.appendData(x_data, y_data, 'data', self.graphoptions)
        self.updateGraph()

    def calcProcess(self, option, progress_callback):
        bg_time_init = option["bg_time_init"]
        bg_time_end = option["bg_time_end"]
        tg_time_init = option["tg_time_init"]
        tg_time_end = option["tg_time_end"]
        step_size = option["step_size"]
        sd_num = option["sd_num"]
        error_step = option["error_step"]

        q = multiprocessing.Queue()
        f = lambda: q.put(cor_process(self.data, bg_time_init, bg_time_end, tg_time_init, tg_time_end, step_size=step_size, SD_NUM=sd_num, ERROR_STEP=error_step, save_svg=False, show_graph=False))
        p = multiprocessing.Process(target=f)
        p.start()
        error_data, pb_info = q.get()
        p.join()

        DataManager.append_error(self.data_id, ErrorType.COR_ERROR, error_data, option)

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
        self.data_id = DataManager.new(self.data)

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

        maxTemperaturePage = MaxTemperatureGraphPageWidget(self, "max temperature", self.data_id, self.data, temperature_config)
        self.addTab(maxTemperaturePage, "max temperature")

        """
        minTemperaturePage = MinTemperatureGraphPageWidget(self, "min temperature", self.data_id, self.data, temperature_config)
        self.addTab(minTemperaturePage, "min temperature")
        """

        distance_config = configs["distance"]
        if configs["distance_timerange_predict"]:
            distance_config["bg_time_init"] = min_time
            distance_config["bg_time_end"] = median_time
            distance_config["tg_time_init"] = median_time
            distance_config["tg_time_end"] = max_time
        temperaturePage = DistanceGraphPageWidget(self, "distance", self.data_id, self.data, distance_config)
        self.addTab(temperaturePage, "distance")

        cor_config = configs["cor"]
        if configs["cor_timerange_predict"]:
            cor_config["bg_time_init"] = min_time
            cor_config["bg_time_end"] = median_time
            cor_config["tg_time_init"] = median_time
            cor_config["tg_time_end"] = max_time
        temperaturePage = CorGraphPageWidget(self, "cor", self.data_id, self.data, cor_config)
        temperaturePage.addpageSignal.connect(self.addtab)
        self.addTab(temperaturePage, "cor")

    def addtab(self, obj):
        x_data = obj["x_data"]
        y_data = obj["y_data"]
        name = obj["name"]
        widget = GraphPageWidget(self, name, self.data_id)
        widget.appendData(x_data, y_data, name)
        widget.updateGraph()
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

        self.innerLayout.addWidget(self.loadInfoWidget, 4)

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


@enum.unique
class DataType(enum.Enum):
    RAWDATA = enum.auto()
    ERROR = enum.auto()
    CACHE = enum.auto()
    CONFIG = enum.auto()

@enum.unique
class ErrorType(enum.Enum):
    MAX_TEMPERATURE_ERROR = enum.auto()
    MIN_TEMPERATURE_ERROR = enum.auto()
    DISTANCE_ERROR = enum.auto()
    COR_ERROR = enum.auto()
    SUM_ERROR = enum.auto()


class ErrorItem(object):
    def __init__(self, error_id, error_type, error_data, error_config):
        self.id = error_id
        self.type = error_type
        self.data = error_data
        self.config = error_config


class DataItem(object):
    def __init__(self, data_id, data, option={}):
        self.id = data_id
        self.data = data
        self.option = option
        self.errors = []
        self.__error_id_counter = 0
        self.max_temperature_rep_error_id = None
        self.min_temperature_rep_error_id = None
        self.cor_rep_error_id = None
        self.distance_rep_error_id = None

    def append_error(self, error_type, error_data, error_config):
        error_id = self.__error_id_counter
        self.__error_id_counter += 1

        error_item = ErrorItem(error_id, error_type, error_data, error_config)
        self.errors.append(error_item)

        if error_type is ErrorType.MAX_TEMPERATURE_ERROR:
            self.max_temperature_rep_error_id = error_item.id
        elif error_type is ErrorType.MIN_TEMPERATURE_ERROR:
            self.min_temperature_rep_error_id = error_item.id
        elif error_type is ErrorType.DISTANCE_ERROR:
            self.distance_rep_error_id = error_item.id
        elif error_type is ErrorType.COR_ERROR:
            self.cor_rep_error_id = error_item.id
        else:
            raise

        return error_id

    def query_error_type(self, query):
        if type(query) is not ErrorType:
            raise
        for error in self.errors:
            if error.type is query:
                yield error

    def get(self, error_id):
        return self.errors[error_id]

    def get_reps(self):
        ret = {}
        ret["max_temperature"] = self.get(self.max_temperature_rep_error_id) if self.max_temperature_rep_error_id else None
        ret["min_temperature"] = self.get(self.min_temperature_rep_error_id) if self.min_temperature_rep_error_id else None
        ret["distance"] = self.get(self.distance_rep_error_id) if self.distance_rep_error_id else None
        ret["cor"] = self.get(self.cor_rep_error_id) if self.cor_rep_error_id else None
        return ret


class DataManager(object):
    __instance = None
    _lock = threading.Lock()
    __id_counter = 0
    
    def __new__(cls):
        raise

    @classmethod
    def __private_init__(cls, self):
        self.datas = []
        self.__active_data = None
        return self

    @classmethod
    def __private_new__(cls):
        return cls.__private_init__(super().__new__(cls))

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls.__instance is None:
                cls.__instance = cls.__private_new__()
        return cls.__instance

    @classmethod
    def new(cls, data):
        data_id = cls.__id_counter
        cls.__id_counter += 1

        dm = cls.get_instance()
        item = DataItem(data_id, data) 
        dm.__append(item)
        dm.__activeted(data_id)
        return data_id

    @classmethod
    def get(cls, data_id):
        dm = cls.get_instance()
        return dm.__get(data_id)

    @classmethod
    def get_data(cls, data_id):
        dm = cls.get_instance()
        item = dm.__get(data_id)
        return item.data

    @classmethod
    def set(cls, data_id, data):
        raise

    @classmethod
    def append_error(cls, data_id, error_type, error_data, error_config):
        dm = cls.get_instance()
        data = dm.__get(data_id)
        return data.append_error(error_type, error_data, error_config)

    @classmethod
    def all(cls):
        dm = cls.get_instance()
        for item in dm.__all():
            yield item

    @classmethod
    def filter(cls, query):
        raise

    def __append(self, item):
        self.datas.append(item)

    def __get(self, data_id):
        for item in self.datas:
            if item.id == data_id:
                return item
        return None

    def __all(self):
        for item in self.datas:
            yield item

    def __activeted(self, data_id):
        self.__active_data = data_id


class DataListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        for item in DataManager.all():
            self.addItem(str(item.id))
            for error in item.errors:
                self.addItem(str(error.id))


class StatisticsWidget(QWidget):
    def __init__(self, parent=None, datatype=None):
        super().__init__(parent)
        self.inner_layout = QHBoxLayout()
        self.setLayout(self.inner_layout)

        self.graphViewWidget = GraphViewWidget()
        self.inner_layout.addWidget(self.graphViewWidget)

        if datatype is ErrorType.MAX_TEMPERATURE_ERROR:
            self.max_temperature_error_draw()
        elif datatype is ErrorType.MIN_TEMPERATURE_ERROR:
            self.min_temperature_error_draw()
        elif datatype is ErrorType.DISTANCE_ERROR:
            self.distance_error_draw()
        elif datatype is ErrorType.COR_ERROR:
            self.cor_error_draw()
        elif datatype is ErrorType.SUM_ERROR:
            self.sum_error_draw()

    def max_temperature_error_draw(self):
        counters = []
        for dataitem in DataManager.all():
            name = 'data' + str(dataitem.id)
            for error in dataitem.errors:
                if error.type is ErrorType.MAX_TEMPERATURE_ERROR:
                    d = error.data.get_col(TEMPERATURE_ERROR_DATA)
                    d_bool = (d>0)
                    count = sum(d_bool)
                    counters.append(count)

        index = list(range(len(counters)))
        self.graphViewWidget.barh(index, counters)
        self.graphViewWidget.yticks(index, list(map(lambda x: 'error'+str(x), index)))
        self.graphViewWidget.draw()

    def min_temperature_error_draw(self):
        counters = []
        for dataitem in DataManager.all():
            name = 'data' + str(dataitem.id)
            for error in dataitem.errors:
                if error.type is ErrorType.MIN_TEMPERATURE_ERROR:
                    d = error.data.get_col(TEMPERATURE_ERROR_DATA)
                    d_bool = (d>0)
                    count = sum(d_bool)
                    counters.append(count)

        index = list(range(len(counters)))
        self.graphViewWidget.barh(index, counters)
        self.graphViewWidget.yticks(index, list(map(lambda x: 'error'+str(x), index)))
        self.graphViewWidget.draw()

    def distance_error_draw(self):
        counters = []
        for dataitem in DataManager.all():
            name = 'data' + str(dataitem.id)
            for error in dataitem.errors:
                if error.type is ErrorType.DISTANCE_ERROR:
                    d = error.data.get_col(ERROR_VALUE)
                    d_bool = (d>0)
                    count = sum(d_bool)
                    counters.append(count)

        index = list(range(len(counters)))
        self.graphViewWidget.barh(index, counters)
        self.graphViewWidget.yticks(index, list(map(lambda x: 'error'+str(x), index)))
        self.graphViewWidget.draw()

    def cor_error_draw(self):
        counters = []
        for dataitem in DataManager.all():
            name = 'data' + str(dataitem.id)
            for error in dataitem.errors:
                if error.type is ErrorType.COR_ERROR:
                    d = error.data.get_col(COR_ERROR_VALUE)
                    d_bool = (d>0)
                    count = sum(d_bool)
                    counters.append(count)

        index = list(range(len(counters)))
        self.graphViewWidget.barh(index, counters)
        self.graphViewWidget.yticks(index, list(map(lambda x: 'error'+str(x), index)))
        self.graphViewWidget.draw()

    def sum_error_draw(self):
        datas = {}
        for dataitem in DataManager.all():
            graphdata = OrderedDict()
            name = "data" + str(dataitem.id)
            reps = dataitem.get_reps()
            print(reps, file=sys.stderr)
            if reps['max_temperature']:
                d = reps['max_temperature'].data.get_col(TEMPERATURE_ERROR_DATA)
                d_bool = (d>0)
                count = sum(d_bool)
                graphdata["max_temperature"] = count
            if reps['min_temperature']:
                d = reps['min_temperature'].data.get_col(TEMPERATURE_ERROR_DATA)
                d_bool = (d>0)
                count = sum(d_bool)
                graphdata["min_temperature"] = count
            if reps['distance']:
                d = reps['distance'].data.get_col(ERROR_VALUE)
                d_bool = (d>0)
                count = sum(d_bool)
                graphdata["distance"] = count
            if reps['cor']:
                d = reps['cor'].data.get_col(COR_ERROR_VALUE)
                d_bool = (d>0)
                count = sum(d_bool)
                graphdata['cor'] = count
            datas[name] = (graphdata)

        for name, grpahdaa in datas.items():
            labels = list(map(lambda k: name+k, graphdata.keys()))
            values = graphdata.values()
            index = list(range(len(values)))
            self.graphViewWidget.barh(index, values)
            self.graphViewWidget.yticks(index, labels)
        self.graphViewWidget.draw()


class MainWidget(QStackedWidget):
    graphWidgets = {}
    newwidget_signal = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.loadWidget = LoadWidget(self)
        self.loadWidget.loadSignal.connect(self.makeGraph)

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

    def openDMWidget(self):
        self.dmwidget = DataListWidget()
        self.dmwidget.show()

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

        windowMenu = menubar.addMenu('Window')
        windowMenu.addAction(openLoadWidgetAction)
        windowMenu.addAction(openDebugConsoleAction)
        windowMenu.addAction(openFileListWidgetAction)
        windowMenu.addAction(openDMWidgetOpenAction)

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


app = QApplication(sys.argv)

mainwindow = MainWindow()
mainwindow.show()

sys.exit(app.exec_())
