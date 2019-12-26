import sys
import threading
import enum
import copy

from PyQt5.QtCore import *

from mouse_calc.ui.configmanager import ConfigManager

@enum.unique
class ProcessType(enum.Enum):
    MAX_TEMPERATURE = enum.auto()
    MIN_TEMPERATURE = enum.auto()
    DISTANCE = enum.auto()
    COR = enum.auto()


class LoadingManagerSignals(QObject):
    updateSignal = pyqtSignal()

class LoadingManager(object):
    __instance = None
    _lock = threading.Lock()
    __id_counter = 0

    def __new__(cls):
        raise

    @classmethod
    def __private_init__(cls, self):
        self.loading_process = {}
        self.signals = LoadingManagerSignals()
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
    def append(cls, process_type, config_id):
        new_id = cls.__id_counter
        cls.__id_counter += 1

        config = copy.deepcopy(ConfigManager.get(config_id))

        lm = cls.get_instance()
        lm.loading_process[new_id] = (True, process_type, config)
        lm.signals.updateSignal.emit()
        return new_id

    @classmethod
    def remove(cls, remove_id):
        lm = cls.get_instance()
        lm.loading_process.pop(remove_id)
        lm.signals.updateSignal.emit()

    @classmethod
    def all(cls):
        lm = cls.get_instance()
        for item in lm.loading_process.values():
            yield item
