from PyQt5.QtWidgets import (QWidget, QFrame, QSplitter, QSizePolicy,
                             QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QRadioButton,
                             QSlider, QButtonGroup, QGroupBox, QTableWidget, QTableWidgetItem, QVBoxLayout,
                             QHBoxLayout, QGridLayout)
from PyQt5.QtCore import Qt, QRectF, QLineF, QPointF
from PyQt5.QtGui import QIntValidator

import pyqtgraph as pg

from WidgetsUI import CrossCursor


class SpectraModuleUI(QWidget):

    def __init__(self):
        super().__init__()

        self.ui_construct()

    def ui_construct(self):
        # Main splitters
        topleft_frame = QFrame(self)
        topleft_frame.setFrameShape(QFrame.StyledPanel)

        topright_frame = QFrame(self)
        topright_frame.setFrameShape(QFrame.StyledPanel)

        bottom_frame = QFrame(self)
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

        main_lay = QVBoxLayout(self)
        main_lay.addWidget(splitter2)

        # --- Controls frame ---

        self.monoGridPos = QDoubleSpinBox(self)
        self.monoGridPos.setRange(2000.0, 10000.0)
        self.monoGridPos.setSingleStep(0.1)
        self.monoGridPos.setDecimals(1)
        self.monoSetPos = QPushButton('Set')
        self.monoSetPos.setMinimumSize(80, 30)
        self.monoCurrentPos = QLabel('5000 Å')
        mono_pos_lbl = QLabel('Grating position: ')

        self.laserSelect = QComboBox(self)
        self.laserSelect.addItems(['Laser 405 nm', 'Laser 450 nm', 'LED 370 nm', 'LED 430 nm'])
        self.laserOn = QPushButton('Connect')
        self.laserOff = QPushButton('Disconnect')
        self.laserOn.setMinimumSize(110, 30)
        self.laserOff.setMinimumSize(110, 30)
        self.laserConn = QLabel('Off', self)
        self.laserStat = QLabel('0 mW', self)
        self.laserPower = QSlider(Qt.Vertical)
        laser_select_lbl = QLabel('Source: ', self)
        laser_conn_lbl = QLabel('Connection: ', self)
        laser_stat_lbl = QLabel('Power: ', self)

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
        self.step_val.setValidator(QIntValidator(1, 10000))
        step_lbl = QLabel('Step size: ', self)
        self.distance_lbl = QLabel('Distance: 0.05um', self)
        self.x_up.setMinimumSize(78, 30)
        self.x_down.setMinimumSize(78, 30)
        self.x_down.setMinimumSize(78, 30)
        self.y_up.setMinimumSize(78, 30)
        self.y_down.setMinimumSize(78, 30)
        self.z_up.setMinimumSize(78, 30)
        self.z_down.setMinimumSize(78, 30)
        self.stop_move.setMinimumSize(78, 30)

        self.x_pos = QTableWidgetItem()
        self.x_pos.setTextAlignment(Qt.AlignCenter)
        self.y_pos = QTableWidgetItem()
        self.y_pos.setTextAlignment(Qt.AlignCenter)
        self.z_pos = QTableWidgetItem()
        self.z_pos.setTextAlignment(Qt.AlignCenter)

        self.acquire_btn = QPushButton('Acquire')
        self.acquire_btn.setFixedSize(120, 60)

        stage_coordinates = QTableWidget(3, 1)
        stage_coordinates.setMaximumWidth(118)
        stage_coordinates.setMaximumHeight(119)
        stage_coordinates.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        stage_coordinates.setStyleSheet("border: 0")
        stage_coordinates.setHorizontalHeaderLabels(['Position'])
        stage_coordinates.setVerticalHeaderLabels(['X', 'Y', 'Z'])
        stage_coordinates.setItem(0, 0, self.x_pos)
        stage_coordinates.setItem(1, 0, self.y_pos)
        stage_coordinates.setItem(2, 0, self.z_pos)

        mono_control_group = QGroupBox('Monochromator')
        mono_control_group.setAlignment(Qt.AlignCenter)
        mono_control_lay = QGridLayout(mono_control_group)
        mono_control_lay.addWidget(self.monoGridPos, 1, 0)
        mono_control_lay.addWidget(self.monoSetPos, 1, 1)
        mono_control_lay.addWidget(mono_pos_lbl, 2, 0)
        mono_control_lay.addWidget(self.monoCurrentPos, 2, 1)
        mono_control_lay.setRowMinimumHeight(0, 30)

        light_source_group = QGroupBox('Light source')
        light_source_group.setAlignment(Qt.AlignCenter)
        light_source_lay = QGridLayout(light_source_group)
        light_source_lay.addWidget(laser_select_lbl, 0, 0)
        light_source_lay.addWidget(self.laserSelect, 0, 1)
        light_source_lay.addWidget(self.laserOn, 1, 0)
        light_source_lay.addWidget(self.laserOff, 1, 1)
        light_source_lay.addWidget(laser_conn_lbl, 2, 0)
        light_source_lay.addWidget(self.laserConn, 2, 1)
        light_source_lay.addWidget(laser_stat_lbl, 3, 0)
        light_source_lay.addWidget(self.laserStat, 3, 1)
        light_source_lay.addWidget(self.laserPower, 0, 2, 4, 1, Qt.AlignRight)
        light_source_lay.setColumnMinimumWidth(2, 30)

        stage_pos_group = QGroupBox('Stage position')
        stage_pos_group.setAlignment(Qt.AlignCenter)
        stage_pos_lay = QGridLayout()
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
        stage_pos_lay.setColumnMinimumWidth(4, 20)
        stage_pos_lay.addWidget(stage_coordinates, 0, 5, 4, 1)
        stage_pos_group.setLayout(stage_pos_lay)

        action_btns_lay = QHBoxLayout(bottom_frame)
        action_btns_lay.setSpacing(50)
        action_btns_lay.addStretch(1)
        action_btns_lay.addWidget(mono_control_group, 0, Qt.AlignLeft)
        action_btns_lay.addWidget(light_source_group, 0, Qt.AlignLeft)
        action_btns_lay.addWidget(stage_pos_group, 0, Qt.AlignLeft)
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

        self.spectrum = self.ccd_graph_widget(w='row')
        self.spectrumCurve = self.spectrum.plot(pen='y')
        self.spectrumCursor = self.cross_cursor()
        self.cursorPosLbl = pg.TextItem(text="X = 0, Y = 0", anchor=(-5, -1), color=pg.mkColor("#99999988"))
        self.cursorPosLbl.setParentItem(self.spectrum.plotItem)
        self.spectrum.addItem(self.spectrumCursor)

        self.frameSection = self.ccd_graph_widget(w='col')
        self.frameSectionCurve = self.frameSection.plot(pen='y')
        self.frameSectionCursor = self.cross_cursor()
        self.frameSection.addItem(self.frameSectionCursor)

        self.frameRowSelect = QSpinBox(self)
        self.frameRowSelect.setRange(1, 255)
        self.frameColSelect = QSpinBox(self)
        self.frameColSelect.setRange(1, 1024)

        y_radio0 = QRadioButton('Counts')
        y_radio0.setChecked(True)
        y_radio1 = QRadioButton('Counts norm.')
        self.YUnits = QButtonGroup(self)
        self.YUnits.addButton(y_radio0, id=0)
        self.YUnits.addButton(y_radio1, id=1)

        x_radio0 = QRadioButton('nm')
        x_radio0.setChecked(True)
        x_radio1 = QRadioButton('eV')
        x_radio2 = QRadioButton('pixel number')
        self.XUnits = QButtonGroup(self)
        self.XUnits.addButton(x_radio0, id=0)
        self.XUnits.addButton(x_radio1, id=1)
        self.XUnits.addButton(x_radio2, id=2)
        self.XUnits.button(0).setChecked(True)

        self.rowBinning = QSpinBox(self)
        self.rowBinning.setRange(1, 255)
        self.avgBinning = QCheckBox('Average value')
        row_binning_lbl = QLabel('Binning', self)

        row_select_group = QGroupBox('Row/Column')
        row_select_group.setAlignment(Qt.AlignCenter)
        row_select_lay = QHBoxLayout(row_select_group)
        row_select_lay.addWidget(self.frameRowSelect)
        row_select_lay.addWidget(self.frameColSelect)

        y_units_group = QGroupBox("Y-axis")
        y_units_group.setAlignment(Qt.AlignCenter)
        y_units_lay = QVBoxLayout(y_units_group)
        y_units_lay.addWidget(y_radio0)
        y_units_lay.addWidget(y_radio1)

        x_units_group = QGroupBox("X-axis")
        x_units_group.setAlignment(Qt.AlignCenter)
        x_units_lay = QVBoxLayout(x_units_group)
        x_units_lay.addWidget(x_radio0)
        x_units_lay.addWidget(x_radio1)
        x_units_lay.addWidget(x_radio2)

        row_binning_group = QGroupBox()
        row_binning_group.setAlignment(Qt.AlignCenter)
        row_binning_lay = QGridLayout(row_binning_group)
        row_binning_lay.addWidget(row_binning_lbl, 0, 0)
        row_binning_lay.addWidget(self.rowBinning, 0, 1)
        row_binning_lay.addWidget(self.avgBinning, 1, 0, 1, 2)

        frame_param = QFrame()
        frame_param_lay = QVBoxLayout(frame_param)
        frame_param_lay.setSpacing(0)
        frame_param_lay.addWidget(row_select_group)
        frame_param_lay.addWidget(y_units_group)
        frame_param_lay.addWidget(x_units_group)
        frame_param_lay.addWidget(row_binning_group)

        ccd_lay = QGridLayout(topright_frame)
        ccd_lay.setRowStretch(0, 2)
        ccd_lay.setRowStretch(1, 3)
        ccd_lay.setColumnStretch(0, 1)
        ccd_lay.setColumnStretch(1, 6)
        ccd_lay.addWidget(self.CCDFrame, 0, 1)
        ccd_lay.addWidget(self.spectrum, 1, 1)
        ccd_lay.addWidget(self.frameSection, 0, 0)
        ccd_lay.addWidget(frame_param, 1, 0)

        # --- Andor Camera Settings ---

        self.exposureTime = QDoubleSpinBox(self)
        self.exposureTime.setRange(0.01, 1000.0)
        self.exposureTime.setDecimals(2)
        # self.exposureTime.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
        exp_time_lbl = QLabel('Exposure time (sec)')

        self.acquisitionMode = QComboBox(self)
        self.acquisitionMode.addItems(['Single', 'Accumulate', 'Kinetic', 'Photon Count', 'Fast Kinetic'])
        self.acquisitionMode.model().item(3).setEnabled(False)
        self.accumulationFrames = QSpinBox(self)
        self.accumulationFrames.setRange(1, 50)
        self.accumulationCycle = QDoubleSpinBox(self)
        self.accumulationCycle.setRange(0.01, 1000.0)
        self.accumulationCycle.setSingleStep(1)
        self.accumulationCycle.setDecimals(2)
        self.kineticSeries = QSpinBox(self)
        self.kineticSeries.setRange(1, 50)
        self.kineticCycle = QDoubleSpinBox(self)
        self.kineticCycle.setRange(0.01, 1000.0)
        self.kineticCycle.setSingleStep(1)
        self.kineticCycle.setDecimals(2)
        acq_mode_lbl = QLabel('Acquisition Mode', self)
        accum_frames_lbl = QLabel('Accumulation Frames')
        accum_cycle_lbl = QLabel('Accumulation Cycle')
        kinetic_series_lbl = QLabel('Kinetic Series')
        kinetic_cycle_lbl = QLabel('Kinetic Cycle Time')

        self.triggeringMode = QComboBox(self)
        self.triggeringMode.addItems(['Internal', 'External', 'Fast External', 'External Start'])
        self.triggeringMode.model().item(2).setEnabled(False)
        self.readoutMode = QComboBox(self)
        self.readoutMode.addItems(['Image', 'Single-Track', 'Multi-Track', 'FVB'])
        self.readoutMode.model().item(1).setEnabled(False)
        self.readoutMode.model().item(2).setEnabled(False)
        self.readoutMode.model().item(3).setEnabled(False)
        trig_mode_lbl = QLabel('Triggering Mode', self)
        read_mode_lbl = QLabel('Readout Mode', self)

        self.readoutRate = QComboBox(self)
        self.readoutRate.addItems(['50kHz at 16-bit', '1MHz at 16-bit', '3MHz at 16-bit'])
        self.preAmpGain = QComboBox(self)
        self.preAmpGain.addItems(['1x', '2x', '4x'])
        readout_rate_lbl = QLabel('Readout Rate')
        preamp_gain_lbl = QLabel('Pre-Amp Gain')

        self.VSSpeed = QComboBox(self)
        self.VSSpeed.addItems(['12.9', '25.7', '51.3', '76.9', '102.5', '128.1', '153.7', '179.3'])
        self.VSAVoltage = QComboBox(self)
        self.VSAVoltage.addItems(['Normal', '+1'])
        self.VSAVoltage.model().item(1).setEnabled(False)
        vs_speed_lbl = QLabel('VShift speed (usec)')
        vsa_voltage_lbl = QLabel('VShift Amp Voltage')

        cam_settings_lay = QVBoxLayout(topleft_frame)
        cam_settings_lay.setSpacing(10)

        cam_exposure_group = QGroupBox("Exposition")
        cam_exposure_lay = QGridLayout(cam_exposure_group)
        cam_exposure_lay.addWidget(exp_time_lbl, 0, 0)
        cam_exposure_lay.addWidget(self.exposureTime, 0, 1)

        cam_timing_group = QGroupBox("Acquisition timings")
        cam_timing_lay = QGridLayout(cam_timing_group)
        cam_timing_lay.addWidget(acq_mode_lbl, 0, 0)
        cam_timing_lay.addWidget(self.acquisitionMode, 0, 1)
        cam_timing_lay.addWidget(accum_frames_lbl, 1, 0)
        cam_timing_lay.addWidget(self.accumulationFrames, 1, 1)
        cam_timing_lay.addWidget(accum_cycle_lbl, 2, 0)
        cam_timing_lay.addWidget(self.accumulationCycle, 2, 1)
        cam_timing_lay.addWidget(kinetic_series_lbl, 3, 0)
        cam_timing_lay.addWidget(self.kineticSeries, 3, 1)
        cam_timing_lay.addWidget(kinetic_cycle_lbl, 4, 0)
        cam_timing_lay.addWidget(self.kineticCycle, 4, 1)

        cam_mode_group = QGroupBox("Mode")
        cam_mode_lay = QGridLayout(cam_mode_group)
        cam_mode_lay.addWidget(trig_mode_lbl, 0, 0)
        cam_mode_lay.addWidget(self.triggeringMode, 0, 1)
        cam_mode_lay.addWidget(read_mode_lbl, 1, 0)
        cam_mode_lay.addWidget(self.readoutMode, 1, 1)

        cam_readout_group = QGroupBox("Readout")
        cam_readout_lay = QGridLayout(cam_readout_group)
        cam_readout_lay.addWidget(readout_rate_lbl, 0, 0)
        cam_readout_lay.addWidget(self.readoutRate, 0, 1)
        cam_readout_lay.addWidget(preamp_gain_lbl, 1, 0)
        cam_readout_lay.addWidget(self.preAmpGain, 1, 1)
        cam_readout_lay.addWidget(vs_speed_lbl, 2, 0)
        cam_readout_lay.addWidget(self.VSSpeed, 2, 1)
        cam_readout_lay.addWidget(vsa_voltage_lbl, 3, 0)
        cam_readout_lay.addWidget(self.VSAVoltage, 3, 1)

        cam_settings_lay.addWidget(cam_exposure_group)
        cam_settings_lay.addWidget(cam_timing_group)
        cam_settings_lay.addWidget(cam_mode_group)
        cam_settings_lay.addWidget(cam_readout_group)

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
            graph.setLabels(left='Intensity')
            graph.setYRange(0, 40000)
            graph.plotItem.setContentsMargins(0, 20, 20, 0)
            graph.plotItem.showAxis('top', True)
            graph.plotItem.showAxis('right', True)
            graph.plotItem.getAxis('top').setStyle(showValues=False)
            graph.plotItem.getAxis('right').setStyle(showValues=False)

        else:
            # graph.setLabels(right='Row')
            graph.setYRange(0, 255)
            graph.setLimits(yMin=0, yMax=255)
            graph.plotItem.setContentsMargins(10, 8, 0, 10)
            graph.plotItem.showAxis('top', True)
            graph.plotItem.showAxis('right', True)
            graph.plotItem.getAxis('top').setStyle(showValues=False)
            graph.plotItem.getAxis('left').setStyle(showValues=False)
            graph.plotItem.getAxis('bottom').setStyle(showValues=False)
            graph.plotItem.getViewBox().invertX(True)

        return graph

    def cross_hair(self, a='h'):
        # cross hair
        pen = pg.mkPen(color=pg.mkColor('#C8C86466'), width=1)
        hover_pen = pg.mkPen(color=pg.mkColor('#FF000077'), width=1)
        if a == 'h':
            line = pg.InfiniteLine(angle=0, pen=pen, hoverPen=hover_pen, movable=True, bounds=(0.5, 254.5))
        else:
            line = pg.InfiniteLine(angle=90, pen=pen, hoverPen=hover_pen, movable=True, bounds=(0.5, 1234.5))

        return line

    def cross_cursor(self):
        pen_color = pg.mkColor('#C8C86477')
        c_pen = pg.mkPen(color=pen_color, width=1)
        cursor_obj = CrossCursor(pen=c_pen)

        return cursor_obj
