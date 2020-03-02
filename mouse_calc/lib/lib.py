#!/usr/bin/env python3
#encoding: utf-8
import csv
import json
import datetime
import argparse
import copy
import itertools
import statistics
from io import BytesIO
import xml.etree.ElementTree as ET
ET.register_namespace("", "http://www.w3.org/2000/svg")

from concurrent.futures import ProcessPoolExecutor

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
matplotlib.rcParams["figure.figsize"] = (27, 9)

TIME = "time"
MAX_TEMPERATURE = "max_temperature"
MAX_POS_X = "max_pos_x"
MAX_POS_Y = "max_pos_y"
MIN_TEMPERATURE = "min_temperature"
MIN_POS_X = "min_pos_x"
MIN_POS_Y = "min_pos_y"
DISTANCE = "distance"

MEAN_SUFFIX = "_mean"
MAX_TEMPERATURE_MEAN = MAX_TEMPERATURE + MEAN_SUFFIX
MAX_POS_X_MEAN = MAX_POS_X + MEAN_SUFFIX
MAX_POS_Y_MEAN = MAX_POS_Y + MEAN_SUFFIX
MIN_TEMPERATURE_MEAN = MIN_TEMPERATURE + MEAN_SUFFIX
MIN_POS_X_MEAN = MIN_POS_X + MEAN_SUFFIX
MIN_POS_Y_MEAN = MIN_POS_Y + MEAN_SUFFIX
DISTANCE_MEAN = DISTANCE + MEAN_SUFFIX

STD_SUFFIX = "_std"
MAX_TEMPERATURE_STD = MAX_TEMPERATURE + STD_SUFFIX
MAX_POS_X_STD = MAX_POS_X + STD_SUFFIX
MAX_POS_Y_STD = MAX_POS_Y + STD_SUFFIX
MIN_TEMPERATURE_STD = MIN_TEMPERATURE + STD_SUFFIX
MIN_POS_X_STD = MIN_POS_X + STD_SUFFIX
MIN_POS_Y_STD = MIN_POS_Y + STD_SUFFIX
DISTANCE_STD = DISTANCE + STD_SUFFIX

MEDIAN_SUFFIX = "_median"
MAX_TEMPERATURE_MEDIAN = MAX_TEMPERATURE + MEDIAN_SUFFIX
MAX_POS_X_MEDIAN = MAX_POS_X + MEDIAN_SUFFIX
MAX_POS_Y_MEDIAN = MAX_POS_Y + MEDIAN_SUFFIX
MIN_TEMPERATURE_MEDIAN = MIN_TEMPERATURE + MEDIAN_SUFFIX
MIN_POS_X_MEDIAN = MIN_POS_X + MEDIAN_SUFFIX
MIN_POS_Y_MEDIAN = MIN_POS_Y + MEDIAN_SUFFIX
DISTANCE_MEDIAN = DISTANCE + MEDIAN_SUFFIX

TEMPERATURE_ERROR_DATA = "temperature_error_data"
WELCH_P_VALUE = "welch_p_value"
ERROR_VALUE = "error_value"
COR_ERROR_VALUE = "cor_error_value"

SD_NUM = 1.5
CACHE_DIR = "./cache"


class Data(object):
    inner_data = None
    labels = {}
    auto_columns_rename = True
    
    def __init__(self, data=pd.DataFrame(), labels=None):
        if type(data) is pd.core.series.Series:
            if labels:
                self.inner_data = pd.DataFrame(data, columns=labels)
            else:
                raise
        elif type(data) is pd.core.frame.DataFrame:
            self.inner_data = data
            if labels:
                self.inner_data.columns = labels
        elif labels and data is list:
            self.inner_data = pd.DataFrame(data, columns=labels)
        elif labels:
            self.inner_data = pd.DataFrame([data], columns=labels)
        else:
            raise

        if labels:
            self.labels = labels
        else:
            self.labels = self.gen_labels()

    def get(self, columns=None):
        if columns:
            if type(columns) is list:
                return self.inner_data.loc[:, [columns]]
            else:
                return self.inner_data[columns]
        else:
            return self.inner_data

    def get_col(self, col_name):
        return self.inner_data[col_name]

    def query(self, query):
        return Data(self.inner_data.query(query))

    def sort(self, key):
        self.inner_data = self.inner_data.sort_values(key)

    def isempty(self):
        return self.inner_data.empty

    def between_time(self, start, end):
        if type(start) is datetime.time:
            start = start.__str__()
        if type(end) is datetime.time:
            end = end.__str__()
        index = pd.DatetimeIndex(self.inner_data[TIME])
        return Data(self.inner_data.iloc[index.indexer_between_time(start, end)])

    def median(self):
        labels = None
        if self.auto_columns_rename:
            labels = list(map(lambda n: n+MEDIAN_SUFFIX, self.inner_data.columns))
        return Data(pd.DataFrame([self.inner_data.median()]), labels=labels)

    def mean(self):
        labels = None
        if self.auto_columns_rename:
            labels = list(map(lambda n: n+MEAN_SUFFIX, self.inner_data.columns))
        return Data(pd.DataFrame([self.inner_data.mean()]), labels=labels)

    def std(self):
        labels = None
        if self.auto_columns_rename:
            labels = list(map(lambda n: n+STD_SUFFIX, self.inner_data.columns))
        return Data(pd.DataFrame([self.inner_data.std()]), labels=labels)

    def map(self, func):
        if not callable(func):
            raise
        return Data(self.inner_data.applymap(func))

    def apply(self, func):
        if not callable(func):
            raise
        return Data(self.inner_data.append(func))
    
    def merge(self, df):
        data = self.inner_data.merge(df.inner_data)
        return Data(data)

    def join(self, df):
        data = self.inner_data.join(df.inner_data)
        return Data(data)

    def append(self, data):
        self.inner_data = pd.concat([self.inner_data, data.inner_data])

    def split(self, step):
        l = self.inner_data
        for idx in range(0, len(l), step):
            yield Data(l[idx: idx+step])

    def reset_index(self):
        self.inner_data = self.inner_data.reset_index(drop=True)

    def set_columns_name(self, names_list):
        pass

    def save_csv(self, filename):
        self.inner_data

    def gen_labels(self):
        labels = {}
        for value in self.inner_data.columns:
            labels[value] = value
        return  labels

    def shallow_copy(self):
        return copy.copy(self)

    def deep_copy(self):
        data = copy.deepcopy(sefl.inner_data)
        return Data(data)

    def __getitem__(self, item):
        cp = self.shallow_copy()
        if type(item) == list:
            keys = [self.labels[i] for i in item]
        else:
            keys = [item]
        data = cp.inner_data.loc[:, keys]
        return Data(data)

    def __add__(self, data):
        data = self.inner_data + data.inner_data
        return Data(data)

    def __sub__(self, data):
        data = self.inner_data - data.inner_data
        return Data(data)

    def __str__(self):
        return self.inner_data.__str__()


class Loader(object):
    preprocess = None
    use_pandas = True
    use_index = False
 
    def __init__(self, filename, sep=",", header=None, names=None):
        self.sep = sep
        self.header = header
        self.filename = filename
        self.names = names

    def load(self):
        data = self._load()
        if self.preprocess and callable(self.preprocess):
            data = self.preprocess(data)
        return Data(data)

    def set_preprocess(self, func):
        if callable(func) == False:
            raise
        self.preprocess = func

    def _load(self):
        if self.use_pandas:
            index_col = 0 if self.use_index else None
            df = pd.read_csv(self.filename, sep=self.sep, index_col=index_col, header=self.header, names=self.names)
            return df
        else:
            datas = []
            with open(self.filename) as f:
                reader = csv.reader(csvfile, delimiter=self.sep)
                for data in reader:
                    datas.append(data)
            return datas


def a3_preprocess(data):
    data[TIME] = data[TIME].apply(lambda x: datetime.datetime.strptime(x, "%Y/%m/%d %H:%M:%S"))
    return data

def lepton_preprocess(data):
    data[TIME] = data[TIME].apply(lambda x: datetime.datetime(x))
    return data

def calc_distance(data):
    x1 = data.get_col(MAX_POS_X)
    x2 = x1.shift(periods=1, fill_value=x1[0])
    y1 = data.get_col(MAX_POS_Y)
    y2 = y1.shift(periods=1, fill_value=y1[0])
    distance = Data( ((x1-x2)**2 + (y1-y2)**2)**0.5, labels=[DISTANCE])
    joined_data = data.join(distance)
    return joined_data

def timerange_to_query(init_datetime, end_datetime, field_name=TIME):
    return init_datetime.strftime("%Y%m%d%H%M%S") +  ' < ' + field_name + ' < ' + end_datetime.strftime("%Y%m%d%H%M%S")

def date_window_separate(data, window_size):
    data_window = Data()
    for d in data.split(window_size):
        d_time_mean = d.get_col(TIME).mean()
        d_time_mean_data = Data(d_time_mean, labels=[TIME])
        d_data = d[[MAX_TEMPERATURE, MAX_POS_X, MAX_POS_Y, MIN_TEMPERATURE, MIN_POS_X, MIN_POS_Y, DISTANCE]]
        d_data_mean = d_data.mean()
        d_data_std = d_data.std()
        data_ = d_time_mean_data.join(d_data_mean).join(d_data_std)
        data_window.append(data_)
    data_window.reset_index()

def temperature_process(data, bg_init_time, bg_end_time, tg_init_time, tg_end_time, step_size=8, thres_sd_heat=1.5, save_svg=False, show_graph=False, svg_filepath="temperature.svg"):
    bg = data.query(timerange_to_query(bg_init_time, bg_end_time))
    tg = data.query(timerange_to_query(tg_init_time, tg_end_time))

    print(bg)
    print(tg)

    bg_preprocess_data = Data()
    temperature_error_data = Data()

    if True:
        t = datetime.time(hour=0, minute=0, second=0)
        delta = datetime.timedelta(minutes=step_size)
        today = datetime.date.today()
        dt = datetime.datetime.combine(today, t)
        while(dt.date() == today):
            bg_between_time = bg.between_time(dt.time(), (dt+delta).time())
            bg_between_time_time = Data(bg_between_time.get_col(TIME).mean(), labels=[TIME])
            bg_between_time_mean = bg_between_time[[MAX_TEMPERATURE, MIN_TEMPERATURE, DISTANCE]].mean()
            bg_between_time_std = bg_between_time[[MAX_TEMPERATURE, MIN_TEMPERATURE, DISTANCE]].std()
            bg_preprocess_data.append(bg_between_time_time.join(bg_between_time_mean).join(bg_between_time_std))

            bg_mean = bg_between_time_mean.get_col(MAX_TEMPERATURE_MEAN)[0]
            bg_std = bg_between_time_std.get_col(MAX_TEMPERATURE_STD)[0]

            for index, bg_data in bg_between_time.inner_data.iterrows():
                temperature_error_data.append(Data([bg_data[TIME], np.abs(bg_data[MAX_TEMPERATURE] - bg_mean)/bg_std], labels=[TIME, TEMPERATURE_ERROR_DATA]))

            tg_between_time = tg.between_time(dt.time(), (dt+delta).time())
            for index, tg_data in tg_between_time.inner_data.iterrows():
                temperature_error_data.append(Data([tg_data[TIME], np.abs(tg_data[MAX_TEMPERATURE] - bg_mean)/bg_std], labels=[TIME, TEMPERATURE_ERROR_DATA]))

            dt += delta
        bg_preprocess_data.reset_index()
        temperature_error_data.sort(TIME)
        temperature_error_data.reset_index()

    print(temperature_error_data)

    error_data = Data()
    error_value = 0
    for index, data in temperature_error_data.inner_data.iterrows():
        time = data[TIME]
        if data[TEMPERATURE_ERROR_DATA] > thres_sd_heat:
            error_value += (data[TEMPERATURE_ERROR_DATA] / thres_sd_heat) * 0.1
        else:
            error_value -= 0.5
            if error_value < 0:
                error_value = 0
        error_data.append(Data([time, error_value], labels=[TIME, TEMPERATURE_ERROR_DATA]))
    error_data.reset_index()

    if show_graph or save_svg:
        fig = plt.figure()
        ax1 = fig.add_subplot(111)

        time = bg.get_col(TIME)
        temperature = bg.get_col(MAX_TEMPERATURE)
        min_time = min(time)
        ax1.plot(time, temperature)

        time = tg.get_col(TIME)
        temperature = tg.get_col(MAX_TEMPERATURE)
        max_time = max(time)
        ax1.plot(time, temperature)

        ax1.set_xlim([min_time, max_time])

        time = error_data.get_col(TIME)
        error_data = error_data.get_col(TEMPERATURE_ERROR_DATA)

        ax2 = ax1.twinx()
        ax2.plot(time, error_data, color="r")

        if save_svg:
            plt.savefig(svg_filepath, format="svg")
        if show_graph:
            plt.show()

    return (error_data, temperature_error_data)

def distance_process(data, bg_init_time, bg_end_time, tg_init_time, tg_end_time, step_size=8, welch_thres=0.5, show_graph=False, save_svg=True, svg_filepath="distance.svg"):
    print("bg_init_time", bg_init_time)
    print("bg_end_time",  bg_end_time)
    print("tg_init_time", tg_init_time)
    print("tg_end_time",  tg_end_time)
    data_window = Data()
    for d in data.split(step_size):
        d_time_mean = d.get_col(TIME).mean()
        d_time_mean_data = Data(d_time_mean, labels=[TIME])
        d_data = d[[MAX_TEMPERATURE, MAX_POS_X, MAX_POS_Y, MIN_TEMPERATURE, MIN_POS_X, MIN_POS_Y, DISTANCE]]
        d_data_mean = d_data.mean()
        d_data_std = d_data.std()
        data_ = d_time_mean_data.join(d_data_mean).join(d_data_std)
        data_window.append(data_)
    data_window.reset_index()

    data_window_time = data_window.get_col(TIME)
    data_window_distance_mean = data_window.get_col(DISTANCE_MEAN)
    data_window_max_temperature_mean = data_window.get_col(MAX_TEMPERATURE_MEAN)
    data_window_min_temperature_mean = data_window.get_col(MIN_TEMPERATURE_MEAN)

    bg = data.query(timerange_to_query(bg_init_time, bg_end_time))
    tg = data.query(timerange_to_query(tg_init_time, tg_end_time))

    print(bg)
    print(tg)

    welch_data = Data()
    if True:
        t = datetime.time(hour=0, minute=0, second=0)
        delta = datetime.timedelta(minutes=step_size)
        today = datetime.date.today()
        dt = datetime.datetime.combine(today, t)

        while(dt.date() == today):
            bg_between_time = bg.between_time(dt.time(), (dt+delta).time())
            tg_between_time = tg.between_time(dt.time(), (dt+delta).time())
            diff = (tg_end_time - tg_init_time).days + 1
            for i in range(diff):
                target = tg_between_time.query(timerange_to_query(tg_init_time+datetime.timedelta(days=i), tg_init_time+datetime.timedelta(days=i+1)))
                if target.isempty():
                    pass
                else:
                    time = target.get_col(TIME).mean()
                    print(target)
                    _, p_value = stats.ttest_ind(target.inner_data[DISTANCE], bg_between_time.inner_data[DISTANCE], equal_var=False)
                    welch_data.append(Data([time, p_value], labels=[TIME, WELCH_P_VALUE])) 
            dt += delta
        welch_data.sort(TIME)
        welch_data.reset_index()
        print(welch_data)

    error_value = 0
    error_data = Data()
    for index, w_data in welch_data.inner_data.iterrows():
        p = w_data[WELCH_P_VALUE]
        time = w_data[TIME]
        if p < welch_thres:
            error_value += -0.1 * (np.log10(p))
        else:
            error_value -= 1.0
            if error_value < 0:
                error_value = 0
        error_data.append(Data([time, error_value], labels=[TIME, ERROR_VALUE]))
    error_data.reset_index()
    print(error_data)

    if show_graph or save_svg:
        fig = plt.figure()
        ax1 = fig.add_subplot(111)

        time = bg.get_col(TIME)
        bg_y = bg.get_col(DISTANCE) 
        ax1.plot(time, bg_y)
        min_x = min(time)

        time = tg.get_col(TIME)
        tg_y = tg.get_col(DISTANCE)
        ax1.plot(time, tg_y)
        max_x = max(time)

        ax1.set_xlim([min_x, max_x])
        ax1.set_ylim([0, 150])

        ax2 = ax1.twinx()
        time = welch_data.get_col(TIME)
        e_value = error_data.get_col(ERROR_VALUE)
        ax2.plot(time, e_value, color="r")
        ax2.scatter(time, e_value, s=0.1, marker='x', color='b')
        ax2.set_ylim([0, 150])

        if save_svg:
            plt.savefig(svg_filepath, format="svg")
        if show_graph:
            plt.show()

    return (error_data, welch_data)


def passing_bablock(x_data, y_data, multi_thread=False):
    assert(x_data.size == y_data.size)
    n = x_data.size
    ng_count = 0
    pb_list = []

    for i, j in itertools.combinations(range(n), 2):
        if np.isnan(x_data[i] - x_data[j]):
            pass
        elif i<j and x_data[i]-x_data[j] != 0.0:
            slope = (y_data[i]-y_data[j]) / (x_data[i]-x_data[j])
            if slope is not np.nan:
                pb_list.append(slope)
                if slope < -1:
                    ng_count += 1
        else:
            pass

    shift = ng_count
    pb_list.sort()
    del pb_list[:shift]

    pb_coef = statistics.median(pb_list)

    sec = (y_data - x_data * pb_coef).mean()

    c_alpha=(1-0.95/2)*np.sqrt(n*(n-1)*(2*n+5)/18)
    n_pb_list=len(pb_list)
    m1=int(round((n_pb_list-c_alpha)/2))
    m2=n_pb_list-m1+1

    pb_upper = pb_list[m2]
    pb_lower = pb_list[m1]

    return pb_coef, sec, pb_upper, pb_lower

def cor_process(data, bg_init_time, bg_end_time, tg_init_time, tg_end_time, step_size=8, ERROR_STEP=1, SD_NUM=1.5, svg_filepath="cor.svg", show_graph=False, save_svg=False):
    data_window = Data(pd.DataFrame())
    for d in data.split(step_size):
        d_time_mean = d.get_col(TIME).mean()
        d_time_mean_data = Data(d_time_mean, labels=[TIME])
        d_data = d[[MAX_TEMPERATURE, MAX_POS_X, MAX_POS_Y, MIN_TEMPERATURE, MIN_POS_X, MIN_POS_Y, DISTANCE]]
        d_data_mean = d_data.mean()
        d_data_std = d_data.std()
        data_ = d_time_mean_data.join(d_data_mean).join(d_data_std)
        data_window.append(data_)
    data_window.reset_index()

    bg = data_window.query(timerange_to_query(bg_init_time, bg_end_time))
    tg = data_window.query(timerange_to_query(tg_init_time, tg_end_time))

    bg_distance = np.log2(bg.get_col(DISTANCE_MEAN))
    bg_distance = bg_distance.replace(-np.inf, 1/step_size)
    bg_temperature = bg.get_col(MAX_TEMPERATURE_MEAN)

    tg_distance = np.log2(tg.get_col(DISTANCE_MEAN))
    tg_distance = tg_distance.replace(-np.inf, 1/step_size)
    tg_temperature = tg.get_col(MAX_TEMPERATURE_MEAN)

    slope, sec, upper, lower = passing_bablock(bg_distance, bg_temperature)
    print("slope: ", slope)
    print("sec: ", sec)

    side = (bg_temperature  - (bg_distance * slope + sec))/((1+slope**2)**0.5)
    d2 = side.std()*SD_NUM
    n_plus = sec + d2*(1+slope**2)**0.5
    n_minus = sec - d2*(1+slope**2)**0.5

    error_data = Data()
    error_value = 0
    ex_time = 0
    for index, data in tg.inner_data.iterrows():
        time = data[TIME]
        x = np.log2(data[DISTANCE_MEAN])
        y = data[MAX_TEMPERATURE_MEAN]
        if y > x*slope + n_plus:
            error_value += abs(y - x*slope - n_plus) / ((1+slope**2)**0.5)
            ex_time = 0
        elif y < x*slope + n_minus:
            error_value += abs(y - (x*slope + n_minus)) / ((1+slope**2)**0.5)
            ex_time = 0
        elif ex_time > ERROR_STEP:
            error_value = 0
            ex_time = 0
        else:
            ex_time += 1
        error_data.append(Data([time, error_value], labels=[TIME, COR_ERROR_VALUE]))
    error_data.sort(TIME)
    error_data.reset_index()
    print(error_data)

    if show_graph or save_svg:
        fig = plt.figure()
        ax1 = fig.add_subplot(121)

        ax1.scatter(bg_distance, bg_temperature, s=0.4)
        ax1.scatter(tg_distance, tg_temperature, s=0.4, color='g')
        ax1.set_xlim([0, max(bg_distance)])
        ax1.set_ylim([min(bg_temperature)-2, max(bg_temperature)+2])

        x = np.linspace(min(bg_distance), max(bg_distance), bg_distance.size)
        bg_y = x * slope + sec
        ax1.plot(x, bg_y, color="r")

        bg_y = x * slope + n_plus
        ax1.plot(x, bg_y, color="y", linestyle="dashed")

        bg_y = x * slope + n_minus
        ax1.plot(x, bg_y, color="y", linestyle="dashed")

        ax2 = fig.add_subplot(122)
        time = error_data.get_col(TIME)
        error = error_data.get_col(COR_ERROR_VALUE)
        ax2.plot(time, error)
        ax2.set_xlim([min(time), max(time)])

        if save_svg:
            plt.savefig(svg_filepath, format="svg")
        if show_graph:
            plt.show()

    return (error_data, {"slope": slope, "n": sec, "n_plus": n_plus, "n_minus": n_minus})

def window_process(data, step_size):
    data_window = Data(pd.DataFrame())
    for d in data.split(step_size):
        d_time_mean = d.get_col(TIME).mean()
        d_time_mean_data = Data(d_time_mean, labels=[TIME])
        d_data = d[[MAX_TEMPERATURE, MAX_POS_X, MAX_POS_Y, MIN_TEMPERATURE, MIN_POS_X, MIN_POS_Y, DISTANCE]]
        d_data_mean = d_data.mean()
        d_data_std = d_data.std()
        data_ = d_time_mean_data.join(d_data_mean).join(d_data_std)
        data_window.append(data_)
    data_window.reset_index()
    return data_window

def all_graph(data, bg_init_time, bg_end_time, tg_init_time, tg_end_time, save_svg=True, show_graph=True):

    data_time = data.get_col(TIME)
    data_distance = data.get_col(DISTANCE)
    data_max_temperature = data.get_col(MAX_TEMPERATURE)
    data_min_temperature = data.get_col(MIN_TEMPERATURE)

    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    #ax3 = fig.add_subplot(313)

    ax1.set_xlim([min(data_time), max(data_time)])
    ax1.plot(data_time, data_distance, color="g")
    ax1_error = ax1.twinx()
    error_data, _ = distance_process(data,
                                     bg_init_time, bg_end_time,
                                     tg_init_time, tg_end_time,
                                     save_svg=False, show_graph=False)
    time = error_data.get_col(TIME)
    error_value = error_data.get_col(ERROR_VALUE)
    ax1_error.plot(time, error_value, color="b")

    ax2 = ax1.twinx()
    ax2.plot(data_time, data_max_temperature, color="y")
    ax2_error = ax2.twinx()
    error_data, _ = temperature_process(data,
                                        bg_init_time, bg_end_time,
                                        tg_init_time, tg_end_time,
                                        save_svg=False, show_graph=False)
    time = error_data.get_col(TIME)
    error_value = error_data.get_col(TEMPERATURE_ERROR_DATA)
    ax2_error.plot(time, error_value, color="m")

    ax3 = ax1.twinx()
    error_data, _ = cor_process(data,
                               bg_init_time, bg_end_time,
                               tg_init_time, tg_end_time,
                               save_svg=False, show_graph=False)
    time = error_data.get_col(TIME)
    time = error_data.get_col(TIME)
    error_value = error_data.get_col(COR_ERROR_VALUE)
    ax3.plot(time, error_value, color="r")

    if save_svg:
        plt.savefig("allgraph.svg", format="svg")
    if show_graph:
        plt.show()

def fig_to_svgtree(fig):
    f = BytesIO()
    plt.savefig(f, format="svg")
    tree, xmlid = ET.XMLID(f.getvalue())
    return tree, xmlid
    
