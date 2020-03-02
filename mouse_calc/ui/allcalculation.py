import multiprocessing
from concurrent import futures

from mouse_calc.lib import *
from mouse_calc.ui.datamanager import DataType, ErrorType, DataManager
from mouse_calc.ui.configmanager import ConfigManager


class AllCalculation():
    def __init__(self, data_ids=[], control_data_id=None, config_id=None):
        self.data_ids = data_ids
        self.control_data_id = control_data_id
        self.config_id = config_id

    def run(self):
        self.allcalculation()
        self.duration()

    def duration(self):
        pass

    def result_callback(self, future):
        result = future.result()
        data_id = result["data_id"]
        error_type = result["error_type"]
        error_data = result["error_data"]
        error_option = result["option"]
        DataManager.append_error(data_id, error_type, error_data, error_option)

    def allcalculation(self):
        future_list = []
        self.results = None

        with futures.ProcessPoolExecutor(max_workers=4) as executor:
            config = ConfigManager.get(self.config_id)

            if self.control_data_id is not None:
                data = DataManager.get_data(self.control_data_id)

                future = executor.submit(fn=temperature_calc, index=self.control_data_id,  data=data, config=config)
                future.add_done_callback(self.result_callback)
                future_list.append(future)

                future = executor.submit(fn=distance_calc, index=self.control_data_id, data=data, config=config)
                future.add_done_callback(self.result_callback)
                future_list.append(future)

                future = executor.submit(fn=cor_calc, index=self.control_data_id, data=data, config=config)
                future.add_done_callback(self.result_callback)
                future_list.append(future)

            for data_id in self.data_ids:
                data = DataManager.get_data(data_id)

                future = executor.submit(fn=temperature_calc, index=data_id,  data=data, config=config)
                future.add_done_callback(self.result_callback)
                future_list.append(future)

                future = executor.submit(fn=distance_calc, index=data_id, data=data, config=config)
                future.add_done_callback(self.result_callback)
                future_list.append(future)

                future = executor.submit(fn=cor_calc, index=data_id, data=data, config=config)
                future.add_done_callback(self.result_callback)
                future_list.append(future)

            self.results = futures.as_completed(fs=future_list)


### Calc Functions ###

def temperature_calc(index, data, config):
    print("data %d temperature calculation is started" % index)
    option = config["temperature"]
    bg_time_init = option["bg_time_init"]
    bg_time_end = option["bg_time_end"]
    tg_time_init = option["tg_time_init"]
    tg_time_end = option["tg_time_end"]
    step_size = option["step_size"]
    thres_sd_heat = option["thres_sd_heat"]

    error_data, _ = temperature_process(data, bg_time_init, bg_time_end, tg_time_init, tg_time_end, step_size=step_size, thres_sd_heat=thres_sd_heat, save_svg=False, show_graph=False)

    return {"data_id": index, "error_type": ErrorType.MAX_TEMPERATURE_ERROR, "error_data": error_data, "option": option}


def distance_calc(index, data, config):
    print("data %d distance calculation is started" % index)
    option = config["distance"]
    bg_time_init = option["bg_time_init"]
    bg_time_end = option["bg_time_end"]
    tg_time_init = option["tg_time_init"]
    tg_time_end = option["tg_time_end"]
    step_size = option["step_size"]
    welch_thres = option["welch_thres"]

    error_data, _ = distance_process(data, bg_time_init, bg_time_end, tg_time_init, tg_time_end, step_size=step_size, save_svg=False, show_graph=False, welch_thres=welch_thres)

    return {"data_id": index, "error_type": ErrorType.DISTANCE_ERROR, "error_data": error_data, "option": option}


def cor_calc(index, data, config):
    print("data %d cor calculation is started" % index)
    option = config["cor"]
    bg_time_init = option["bg_time_init"]
    bg_time_end = option["bg_time_end"]
    tg_time_init = option["tg_time_init"]
    tg_time_end = option["tg_time_end"]
    step_size = option["step_size"]
    error_step = option["error_step"]
    sd_num = option["sd_num"]

    error_data, _ = cor_process(data, bg_time_init, bg_time_end, tg_time_init, tg_time_end, step_size=step_size, SD_NUM=sd_num, ERROR_STEP=error_step, save_svg=False, show_graph=False)

    return {"data_id": index, "error_type": ErrorType.COR_ERROR, "error_data": error_data, "option": option}


######################
