from PyQt5.QtWidgets import (QWidget, QMenu, QVBoxLayout, QHBoxLayout, QFrame, QSplitter, QDesktopWidget,
                             QPushButton, QComboBox, QGroupBox, QGridLayout, QLabel, QSizePolicy,
                             QMessageBox)
from PyQt5.QtCore import Qt, QRectF, QLineF, QPointF
from PyQt5.QtGui import QImage, QPixmap, qRgb

import pyqtgraph as pg

import numpy as np

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
        self.image = pg.ImageItem()
        self.CCDFrame.addItem(self.image)
        self.vLine = self.cross_hair(a='v')
        self.hLine = self.cross_hair(a='h')
        self.CCDFrame.addItem(self.vLine)
        self.CCDFrame.addItem(self.hLine)

        self.CCDRow = self.ccd_graph_widget(w='row')
        self.rowCurve = self.CCDRow.plot(pen='y')
        self.rowGraphCursor = self.cross_cursor()
        self.cursorPosLbl = pg.TextItem(text="X = 0, Y = 0", anchor=(-5, -1), color=pg.mkColor("#99999988"))
        self.cursorPosLbl.setParentItem(self.CCDRow.plotItem)
        self.CCDRow.addItem(self.rowGraphCursor)

        self.CCDCol = self.ccd_graph_widget(w='col')
        self.colCurve = self.CCDCol.plot(pen='y')
        self.colGraphCursor = self.cross_cursor()
        self.CCDCol.addItem(self.colGraphCursor)

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
        bg_color = pg.mkColor('#29353D')
        pg.setConfigOptions(background=bg_color)
        pg.setConfigOptions(imageAxisOrder='row-major')

        frame = pg.ImageView()
        frame.getView().setLimits(xMin=0, xMax=1025, yMin=0, yMax=256)

        size_policy = QSizePolicy()
        size_policy.setHorizontalPolicy(QSizePolicy.Expanding)
        size_policy.setVerticalPolicy(QSizePolicy.Expanding)
        frame.setSizePolicy(size_policy)
        frame.setMinimumSize(512, 128)
        frame.ui.histogram.hide()
        frame.ui.roiBtn.hide()
        frame.ui.menuBtn.hide()

        return frame

    def ccd_graph_widget(self, w='row'):
        bg_color = pg.mkColor('#29353D')
        pg.setConfigOptions(background=bg_color)

        graph = pg.PlotWidget()
        graph.showGrid(x=True, y=True)
        graph.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        graph.setMouseTracking(True)


        if w == 'row':
            graph.setLabels(left='Intensity', bottom='Wavelength (nm)')
            graph.setYRange(0, 40000)
            graph.setXRange(0, 1024)
            graph.setLimits(xMin=0, xMax=1024)
            graph.plotItem.setContentsMargins(0, 20, 20, 0)
            graph.plotItem.showAxis('top', True)
            graph.plotItem.showAxis('right', True)
            graph.plotItem.getAxis('top').setStyle(showValues=False)
            graph.plotItem.getAxis('right').setStyle(showValues=False)
        else:
            # graph.setLabels(right='Row')
            graph.setYRange(0, 255)
            graph.setLimits(yMin=0, yMax=255)
            graph.plotItem.setContentsMargins(10, 10, 0, 0)
            graph.plotItem.showAxis('top', True)
            graph.plotItem.showAxis('right', True)
            graph.plotItem.getAxis('top').setStyle(showValues=False)
            graph.plotItem.getAxis('left').setStyle(showValues=False)

        return graph

    def cross_hair(self, a='h'):
        # cross hair
        pen = pg.mkPen(color=pg.mkColor('#C8C86466'), width=1)
        hover_pen = pg.mkPen(color=pg.mkColor('#FF000077'), width=1)
        if a == 'h':
            line = pg.InfiniteLine(pos=10, angle=0, pen=pen, hoverPen=hover_pen, movable=True, bounds=(0.5, 254.5))
        else:
            line = pg.InfiniteLine(pos=10, angle=90, pen=pen, hoverPen=hover_pen, movable=True, bounds=(0.5, 1234.5))

        return line

    def cross_cursor(self):
        pen_color = pg.mkColor('#C8C86477')
        c_pen = pg.mkPen(color=pen_color, width=1)
        cursor_obj = CrossCursor(pen=c_pen)

        return cursor_obj

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


# Create a subclass of GraphicsObject.
class CrossCursor(pg.InfiniteLine):
    def __init__(self, size=30, pos=None, pen=None, bounds=None, label=None, labelOpts=None, name=None):
        pg.InfiniteLine.__init__(self, pos, 0, pen, False, bounds, None, label, labelOpts, name)

        # self.vb = vb
        self.cursorSize = size

    def boundingRect(self):
        if self._boundingRect is None:
            # br = UIGraphicsItem.boundingRect(self)
            br = self.viewRect()
            if br is None:
                return QRectF()

            # get vertical pixel length
            self.pxv = self.pixelLength(direction=pg.Point(0, 1), ortho=False)
            if self.pxv is None:
                self.pxv = 0
            # get horizontal pixel length
            self.pxh = self.pixelLength(direction=pg.Point(1, 0), ortho=False)
            if self.pxh is None:
                self.pxh = 0

            br = br.normalized()
            self._boundingRect = br

        return self._boundingRect

    def paint(self, p, *args):
        p.setPen(self.currentPen)

        x = self.getXPos()
        y = self.getYPos()
        # print((x, y))

        h = self.cursorSize * self.pxv
        w = self.cursorSize * self.pxh

        p.drawLine(QPointF(x, y - h), QPointF(x, y + h))
        p.drawLine(QPointF(x - w, y), QPointF(x + w, y))
