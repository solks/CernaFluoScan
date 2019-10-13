from PyQt5.QtWidgets import (QWidget, QMenu, QVBoxLayout, QHBoxLayout, QFrame, QSplitter, QDesktopWidget,
                             QPushButton, QComboBox, QGroupBox, QGridLayout, QLabel, QSizePolicy,
                             QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, qRgb

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.image as mpimg

import pyqtgraph as pg

import numpy as np
import random


class UI(QWidget):

    W_HEIGHT = 960
    W_WIDTH = 1440

    def __init__(self, main_window):
        super().__init__()

        main_window.resize(self.W_WIDTH, self.W_HEIGHT)
        self.center_window(main_window)

        main_window.setWindowTitle('CernaFluoScan')
        main_window.statusBar().showMessage("Cerna Fluorescence Scan Microscope control")

        self.fileMenu = QMenu('&File', main_window)
        self.helpMenu = QMenu('&Help', main_window)

        main_window.menuBar().addMenu(self.fileMenu)
        main_window.menuBar().addSeparator()
        main_window.menuBar().addMenu(self.helpMenu)

        self.mainWidget = QWidget(main_window)
        self.mainWidget.setFocus()
        main_window.setCentralWidget(self.mainWidget)

        self.ui_construct()

    def ui_construct(self):

        # --- Main Layout ---

        self.fileMenu.addAction('&Quit', self.file_quit, Qt.CTRL + Qt.Key_Q)
        self.helpMenu.addAction('&About', self.about)

        main_lay = QVBoxLayout(self.mainWidget)

        topleft_frame = QFrame(self.mainWidget)
        topleft_frame.setFrameShape(QFrame.StyledPanel)

        topright_frame = QFrame(self.mainWidget)
        topright_frame.setFrameShape(QFrame.StyledPanel)

        bottom_frame = QFrame(self.mainWidget)
        bottom_frame.setFrameShape(QFrame.StyledPanel)

        splitter1 = QSplitter(Qt.Horizontal)
        splitter1.addWidget(topleft_frame)
        splitter1.addWidget(topright_frame)
        splitter1.setSizes((250, 100))
        splitter1.setStretchFactor(0, 0)
        splitter1.setStretchFactor(1, 1)

        splitter2 = QSplitter(Qt.Vertical)
        splitter2.addWidget(splitter1)
        splitter2.addWidget(bottom_frame)
        splitter2.setSizes((100, 200))
        splitter2.setStretchFactor(0, 1)
        splitter2.setStretchFactor(1, 0)

        main_lay.addWidget(splitter2)

        # --- Actions frame ---

        action_btns_lay = QHBoxLayout(bottom_frame)
        action_btns_lay.setSpacing(50)

        stage_pos_group = QGroupBox('Stage position')
        stage_pos_group.setAlignment(Qt.AlignCenter)

        self.x_up = QPushButton('X+')
        self.x_down = QPushButton('X-')
        self.y_up = QPushButton('Y+')
        self.y_down = QPushButton('Y-')
        self.z_up = QPushButton('Z+')
        self.z_down = QPushButton('Z-')
        self.stop_move = QPushButton('Stop')
        self.step_val = QComboBox(self)
        self.step_val.setEditable(True)
        self.step_val.addItems(['1', '2', '5', '10', '20', '50', '100', '200', '500', '1000', '2000', '5000'])
        step_lbl = QLabel('Step size: ', self)
        self.distance_lbl = QLabel('Distance: 0.05um', self)

        stage_pos_lay = QGridLayout()
        stage_pos_lay.setColumnStretch(1, 1)
        stage_pos_lay.setColumnStretch(2, 1)
        stage_pos_lay.setColumnStretch(3, 1)
        stage_pos_lay.setColumnStretch(4, 1)

        stage_pos_lay.addWidget(self.x_up, 1, 2)
        stage_pos_lay.addWidget(self.x_down, 1, 0)
        stage_pos_lay.addWidget(self.y_up, 0, 1)
        stage_pos_lay.addWidget(self.y_down, 2, 1)
        stage_pos_lay.addWidget(self.y_up, 0, 3)
        stage_pos_lay.addWidget(self.y_down, 2, 3)
        stage_pos_lay.addWidget(self.z_up, 0, 3)
        stage_pos_lay.addWidget(self.z_down, 2, 3)
        stage_pos_lay.addWidget(self.stop_move, 1, 1)
        stage_pos_lay.addWidget(self.step_val, 3, 1)
        stage_pos_lay.addWidget(step_lbl, 3, 0)
        stage_pos_lay.addWidget(self.distance_lbl, 3, 2, 1, 2)
        stage_pos_group.setLayout(stage_pos_lay)

        self.acquire_btn = QPushButton('Acquire')
        self.acquire_btn.setFixedSize(120, 60)

        action_btns_lay.addStretch(1)
        action_btns_lay.addWidget(stage_pos_group, 0, Qt.AlignLeft)
        # action_btns_lay.addStretch(1)
        action_btns_lay.addWidget(self.acquire_btn, 0, Qt.AlignLeft)
        action_btns_lay.addStretch(1)

        # --- CCD Frame Layout ---

        self.CCDFrame = self.ccd_frame_widget()
        # self.CCDFrame.setXRange(0, 1024, padding=0)
        self.CCDRow = self.ccd_graph_widget()
        self.CCDRow.setLabels(left="Intensity", bottom="nm")
        self.CCDCol = self.ccd_graph_widget()
        self.CCDCol.setLabels(left="row", bottom="Intensity")

        ccd_lay = QGridLayout(topright_frame)
        ccd_lay.setRowStretch(0, 2)
        ccd_lay.setRowStretch(1, 3)
        ccd_lay.setColumnStretch(0, 1)
        ccd_lay.setColumnStretch(1, 6)
        ccd_lay.addWidget(self.CCDFrame, 0, 1)
        ccd_lay.addWidget(self.CCDRow, 1, 1)
        ccd_lay.addWidget(self.CCDCol, 0, 0)

        # --- Andor Camera Settings ---

        self.acquisitionMode = QComboBox(self)
        self.acquisitionMode.addItems(['Single', 'Accumulate', 'Kinetic', 'Photon Count', 'Fast Kinetic'])
        self.triggeringMode = QComboBox(self)
        self.triggeringMode.addItems(['Internal', 'External', 'Fast External', 'External Start'])
        self.readoutMode = QComboBox(self)
        self.readoutMode.addItems(['Image', 'Multi-Track', 'FVB'])
        acq_mode_lbl = QLabel('Acquisition Mode', self)
        trig_mode_lbl = QLabel('Triggering Mode', self)
        read_mode_lbl = QLabel('Readout Mode', self)

        self.exposureTime = QComboBox(self)
        self.exposureTime.setEditable(True)
        self.exposureTime.addItems(['0.01', '0.1', '1', '2', '5', '10', '20', '50', '100', '200', '500'])
        self.exposureTime.setCurrentIndex(3)
        self.framesPerImage = QComboBox(self)
        self.framesPerImage.setEditable(True)
        self.framesPerImage.addItems(['1', '2', '3', '5', '10', '15', '20', '30', '40', '50'])
        self.kineticLength = QComboBox(self)
        self.kineticLength.setEditable(True)
        self.kineticLength.addItems(['1', '2', '3', '5', '10', '15', '20', '30', '40', '50'])
        self.kineticLength.setCurrentIndex(3)
        self.kineticTime = QComboBox(self)
        self.kineticTime.setEditable(True)
        self.kineticTime.addItems(['0.76607'])
        exp_time_lbl = QLabel('Exposure (sec)')
        fpi_lbl = QLabel('Frames per Image')
        kinetic_len_lbl = QLabel('Kinetic Series')
        kinetic_time_lbl = QLabel('Kinetic Time (sec)')

        self.vShiftSpeed = QComboBox(self)
        self.vShiftSpeed.addItems(['12.9', '25.7', '51.3', '76.9', '102.5', '128.1', '153.7', '179.3'])
        self.vClkVoltage = QComboBox(self)
        self.vClkVoltage.addItems(['Normal', '+1'])
        vshift_speed_lbl = QLabel('Shift speed (usec)')
        vclk_volt_lbl = QLabel('Clock Voltage Amp')

        self.readoutRate = QComboBox(self)
        self.readoutRate.addItems(['50kHz at 16-bit', '1MHz at 16-bit', '3MHz at 16-bit'])
        self.preAmpGain = QComboBox(self)
        self.preAmpGain.addItems(['1x', '2x', '4x'])
        readout_rate_lbl = QLabel('Readout Rate')
        preamp_gain_lbl = QLabel('Pre-Amp Gain')

        cam_settings_lay = QVBoxLayout(topleft_frame)
        cam_settings_lay.setSpacing(20)

        cam_mode_group = QGroupBox("Mode")
        cam_mode_group.setAlignment(Qt.AlignCenter)
        cam_mode_lay = QGridLayout()
        cam_mode_lay.setColumnStretch(0, 1)
        cam_mode_lay.setColumnStretch(1, 1)
        cam_mode_lay.addWidget(acq_mode_lbl, 0, 0)
        cam_mode_lay.addWidget(self.acquisitionMode, 0, 1)
        cam_mode_lay.addWidget(trig_mode_lbl, 1, 0)
        cam_mode_lay.addWidget(self.triggeringMode, 1, 1)
        cam_mode_lay.addWidget(read_mode_lbl, 2, 0)
        cam_mode_lay.addWidget(self.readoutMode, 2, 1)
        cam_mode_group.setLayout(cam_mode_lay)

        cam_timing_group = QGroupBox("Timings")
        cam_timing_group.setAlignment(Qt.AlignCenter)
        cam_timing_lay = QGridLayout()
        cam_timing_lay.setColumnStretch(0, 1)
        cam_timing_lay.setColumnStretch(1, 1)
        cam_timing_lay.addWidget(exp_time_lbl, 0, 0)
        cam_timing_lay.addWidget(self.exposureTime, 0, 1)
        cam_timing_lay.addWidget(fpi_lbl, 1, 0)
        cam_timing_lay.addWidget(self.framesPerImage, 1, 1)
        cam_timing_lay.addWidget(kinetic_len_lbl, 2, 0)
        cam_timing_lay.addWidget(self.kineticLength, 2, 1)
        cam_timing_lay.addWidget(kinetic_time_lbl, 3, 0)
        cam_timing_lay.addWidget(self.kineticTime, 3, 1)
        cam_timing_group.setLayout(cam_timing_lay)

        cam_vshift_group = QGroupBox("Vertical Pixel Shift")
        cam_vshift_group.setAlignment(Qt.AlignCenter)
        cam_vshift_lay = QGridLayout()
        cam_vshift_lay.setColumnStretch(0, 1)
        cam_vshift_lay.setColumnStretch(1, 1)
        cam_vshift_lay.addWidget(vshift_speed_lbl, 0, 0)
        cam_vshift_lay.addWidget(self.vShiftSpeed, 0, 1)
        cam_vshift_lay.addWidget(vclk_volt_lbl, 1, 0)
        cam_vshift_lay.addWidget(self.vClkVoltage, 1, 1)
        cam_vshift_group.setLayout(cam_vshift_lay)

        cam_hshift_group = QGroupBox("Horizontal Pixel Shift")
        cam_hshift_group.setAlignment(Qt.AlignCenter)
        cam_hshift_lay = QGridLayout()
        cam_hshift_lay.setColumnStretch(0, 1)
        cam_hshift_lay.setColumnStretch(1, 1)
        cam_hshift_lay.addWidget(readout_rate_lbl, 0, 0)
        cam_hshift_lay.addWidget(self.readoutRate, 0, 1)
        cam_hshift_lay.addWidget(preamp_gain_lbl, 1, 0)
        cam_hshift_lay.addWidget(self.preAmpGain, 1, 1)
        cam_hshift_group.setLayout(cam_hshift_lay)

        cam_settings_lay.addWidget(cam_timing_group, 0, Qt.AlignCenter)
        cam_settings_lay.addWidget(cam_mode_group, 0, Qt.AlignCenter)
        cam_settings_lay.addWidget(cam_hshift_group, 0, Qt.AlignCenter)
        cam_settings_lay.addWidget(cam_vshift_group, 0, Qt.AlignCenter)

    def ccd_frame_widget(self):
        framedata = np.random.randint(0, 80, (255, 1024), dtype=np.uint8)
        framedata2 = np.random.randint(0, 250, (255, 1024), dtype=np.uint8)

        bg_color = pg.mkColor('#29353D')
        pg.setConfigOptions(background=bg_color)
        pg.setConfigOptions(imageAxisOrder='row-major')

        frame = pg.ImageView()
        img = pg.ImageItem(framedata, autoLevels=False)
        frame.addItem(img)
        # frame.autoRange()

        size_policy = QSizePolicy()
        size_policy.setHeightForWidth(True)
        size_policy.setHorizontalPolicy(QSizePolicy.Expanding)
        size_policy.setVerticalPolicy(QSizePolicy.Expanding)
        frame.setSizePolicy(size_policy)
        frame.setMinimumSize(512, 128)
        frame.ui.histogram.hide()
        frame.ui.roiBtn.hide()
        frame.ui.menuBtn.hide()

        # cross hair
        pen_color = pg.mkColor('#C8C86477')
        c_pen = pg.mkPen(color=pen_color, width=1)
        v_line = pg.InfiniteLine(angle=90, pen=c_pen, movable=True)
        h_line = pg.InfiniteLine(angle=0, pen=c_pen, movable=True)
        frame.addItem(v_line, ignoreBounds=True)
        frame.addItem(h_line, ignoreBounds=True)

        return frame

    def ccd_graph_widget(self):
        bg_color = pg.mkColor('#29353D')
        pg.setConfigOptions(background=bg_color)

        graph = pg.PlotWidget()
        graph.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        cross_arrow = pg.GraphicsObject()
        graph.addItem(cross_arrow)

        return graph

    def center_window(self, window):
        qr = window.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        window.move(qr.topLeft())

    def file_quit(self):
        self.main_window.close()

        # reply = QMessageBox.question(self, 'Message',
        #     "Are you sure to quit?", QMessageBox.Yes |
        #     QMessageBox.No, QMessageBox.No)
        #
        # if reply == QMessageBox.Yes:
        #     event.accept()
        # else:
        #     event.ignore()

    def about(self, window):
        QMessageBox.about(window, "About",
                          """Cerna Fluorescence Scan Microscope & MDR-3 
control software.

Developers: 
Oleksandr Stanovyi, astanovyi@gmail.com

© Copyright 2019"""
                          )