import threading
import datetime


class ConfigItem(object):
    def __init__(self, config_id, config):
        self.id = config_id
        self.config = config


class ConfigManager(object):
    __instance = None
    _lock = threading.Lock()
    __id_counter = 0

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

    def __new__(cls):
        raise

    @classmethod
    def __private_init__(cls, self):
        self.configs = []
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
    def new(cls, config):
        config_id = cls.__id_counter
        cls.__id_counter += 1

        cm = cls.get_instance()
        item = ConfigItem(config_id, config)
        cm.__append(item)
        return config_id

    @classmethod
    def get(cls, config_id):
        cm = cls.get_instance()
        return cm.__get(config_id)

    @classmethod
    def default(cls):
        config_id = cls.__id_counter
        cls.__id_counter += 1

        cm = cls.get_instance()
        item = ConfigItem(config_id, cls.default_config)
        cm.__append(item)
        return config_id

    @classmethod
    def set(cls, config_id, config):
        if type(config) is not ConfigItem:
            raise
        cm = cls.get_instance()
        cm.__set(config_id, config)

    def __append(self, item):
        self.configs.append(item)

    def __get(self, config_id):
        for item in self.configs:
            if item.id == config_id:
                return item.config
        return None

    def __all(self):
        for item in self.configs:
            yield item

    def __set(self, config_id, config):
        self.configs[config_id] = config
