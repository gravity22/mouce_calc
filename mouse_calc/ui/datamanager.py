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

