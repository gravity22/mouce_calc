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

from lib import *

BG_INIT_TIME = datetime.datetime(year=2019, month=6, day=26)
BG_END_TIME = datetime.datetime(year=2019, month=7, day=4)
TG_INIT_TIME = datetime.datetime(year=2019, month=7, day=4)
TG_END_TIME = datetime.datetime(year=2019, month=7, day=10)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('load_file', help="load data csv file")
    parser.add_argument("bg_time_range", help="target time range. format: %Y/%m/%d-%Y/%m/%d")
    parser.add_argument("tg_time_range", help="target time range. format: %Y/%m/%d-%Y/%m/%d")
    parser.add_argument("--use-cache", help="save inner process data", action="store_true")
    parser.add_argument("--target", help="process target (distance, max_heat_temperature etc...)", default="all")
    parser.add_argument("--header-format", help="csv file header format. if csv has header, set use_header", default="a3")
    parser.add_argument("--step-size", help="window size datasplit", default=8)
    parser.add_argument("--error-step-size", help="error step size using cor process", default=1)
    parser.add_argument("--thres-sd-heat", help="value using temperature process", default=1.5)
    parser.add_argument("--show-graph", help="show graph. default True", action="store_true", default=True)
    parser.add_argument("--save-svg", help="graph save as svg file. default True", action="store_true", default=True)
    args = parser.parse_args()

    save_svg = args.save_svg
    show_graph = args.show_graph
    csv_file_path = args.load_file
    tg_time_range = args.tg_time_range
    bg_time_range = args.bg_time_range
    step_size = args.step_size
    error_step_size = args.error_step_size
    thres_sd_heat = args.thres_sd_heat

    bg_time_init = datetime.datetime.strptime(bg_time_range.split('-')[0], "%Y/%m/%d")
    bg_time_end = datetime.datetime.strptime(bg_time_range.split('-')[1], "%Y/%m/%d")
    tg_time_init = datetime.datetime.strptime(tg_time_range.split('-')[0], "%Y/%m/%d")
    tg_time_end = datetime.datetime.strptime(tg_time_range.split('-')[1], "%Y/%m/%d")

    print("BG init: ", bg_time_init)
    print("BG end : ", bg_time_end)
    print("TG init: ", tg_time_init)
    print("TG end : ", tg_time_end)

    if args.header_format == "a3":
        loader = Loader(csv_file_path, names=[TIME, MAX_TEMPERATURE, MAX_POS_X, MAX_POS_Y, MIN_TEMPERATURE, MIN_POS_X, MIN_POS_Y])
        loader.set_preprocess(a3_preprocess)
    elif args.header_format == "lepton":
        loader = Loader(csv_file_path, names=[TIME, MAX_TEMPERATURE, MAX_POS_X, MAX_POS_Y, MIN_TEMPERATURE, MIN_POS_X, MIN_POS_Y])
        loader.set_preprocess(a3_preprocess)
    else:
        #FIXME: error process
        raise

    # preprocess
    data = loader.load()
    data = calc_distance(data)

    if args.target == "distance":
        print("[#] Make Distance Graph")
        distance_process(data, bg_time_init, bg_time_end, tg_time_init, tg_time_end, step_size=step_size, save_svg=save_svg, show_graph=show_graph)
        print("[!] Process has done")
        exit(0)
    elif args.target == "max_temperature" or args.target == "temperature":
        print("[#] Make Max temperature Grpah")
        temperature_process(data, bg_time_init, bg_time_end, tg_time_init, tg_time_end, step_size=step_size, save_svg=save_svg, show_graph=show_graph)
        print("[!] process has done")
        exit(0)
    elif args.target == "min_temperature":
        raise
    elif args.target == "cor":
        print("[#] Make Cor Graph")
        cor_process(data ,bg_time_init, bg_time_end, tg_time_init, tg_time_end, step_size=step_size, save_svg=save_svg, show_graph=show_graph)
        print("[!] process has done")
    elif args.target == "all":
        print("[#] Make all graph")
        all_graph(data, bg_time_init, bg_time_end, tg_time_init, tg_time_end, save_svg=save_svg, show_graph=show_graph)
        print("[!] process has done")
    elif args.target == "debug":
        debug(data)
    else:
        #FIXME: error process
        raise


