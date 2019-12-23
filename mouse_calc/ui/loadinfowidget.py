from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *

from mouse_calc.lib import *


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

        self.loadConfigButton = QPushButton("Load Config")
        self.saveConfigButton = QPushButton("Svae Config")
        hbox = QHBoxLayout()
        hbox.addWidget(self.saveConfigButton)
        hbox.addWidget(self.loadConfigButton)
        self.innerLayout.addLayout(hbox, 2, 0)

        hbox = QHBoxLayout()
        self.loadButton = QPushButton("Load")
        hbox.addWidget(self.loadButton)
        self.innerLayout.addLayout(hbox, 3, 0)

