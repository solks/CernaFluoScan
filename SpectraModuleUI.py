from PyQt5.QtWidgets import (QWidget, QMainWindow, QFrame, QSplitter, QSizePolicy,
                             QPushButton, QToolButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
                             QRadioButton, QLineEdit, QSlider, QButtonGroup, QGroupBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QTabWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QLineF, QPointF
from PyQt5.QtGui import QIntValidator
import qdarkstyle

import pyqtgraph as pg

from WidgetsUI import PgGraphicsView, PgPlotWidget, CrossLine, CrossCursor


class SpectraModuleUI(QWidget):

    monoStartup = pyqtSignal()

    def __init__(self, cam_wi, status_bar, hardware_conf):
        super().__init__()

        self.CameraWI = cam_wi
        self.statusBar = status_bar

        self.ui_construct(hardware_conf)

    def init_parameters(self, param_set):
        frame = param_set['frameSet']
        stage = param_set['stagePos']
        laser = param_set['Laser']
        mono = param_set['MDR-3']
        andor = param_set['Andor']

        # Hardware parameter set
        self.x_pos.setText(str(stage['x']))
        self.y_pos.setText(str(stage['y']))
        self.z_pos.setText(str(stage['z']))
        self.step_val.setCurrentText(str(stage['step']))

        self.WLStart.setValue(mono['WL-start'])
        self.monoGridPos.setValue(mono['WL-pos'])
        self.monoCurrentPos.setText(str(mono['WL-pos']) + ' nm')
        self.monoGridSelect.setCurrentIndex(mono['grating-select'])
        self.monoStartup.emit()

        self.laserSelect.setCurrentIndex(laser['source-id'])

        # Frame parameter set
        self.frameRowSelect.setValue(frame['row'])
        self.frameColSelect.setValue(frame['column'])
        self.frameColSelect.setValue(frame['column'])

        self.rowBinning.setValue(frame['binning'])
        if frame['binningAvg']:
            self.avgBinning.setChecked(True)

        # self.XUnits.button(frame['x-axis']).setChecked(True)
        self.XUnits.button(frame['x-axis']).click()

        # self.YUnits.button(frame['y-axis']).setChecked(True)
        self.YUnits.button(frame['y-axis']).click()

        # Andor parameter set
        self.exposureTime.setValue(andor['exposure'])
        self.acquisitionMode.setCurrentIndex(andor['AcqMode']['mode'])
        self.mode_prm_enable(andor['AcqMode']['mode'])
        self.accumulationFrames.setValue(andor['AcqMode']['accumFrames'])
        self.accumulationCycle.setValue(andor['AcqMode']['accumCycle'])
        self.kineticSeries.setValue(andor['AcqMode']['kSeries'])
        self.kineticCycle.setValue(andor['AcqMode']['kCycle'])
        self.triggeringMode.setCurrentIndex(andor['trigMode'])
        self.readoutMode.setCurrentIndex(andor['readMode'])
        self.VSSpeed.setCurrentIndex(andor['VSSpeed'])
        self.VSAVoltage.setCurrentIndex(andor['VSAVoltage'])
        self.readoutRate.setCurrentIndex(andor['ADCRate'])
        self.preAmpGain.setCurrentIndex(andor['gain'])

    def mode_prm_enable(self, acq_mode):
        if acq_mode == 0:
            self.accumulationFrames.setEnabled(False)
            self.accumulationCycle.setEnabled(False)
            self.kineticSeries.setEnabled(False)
            self.kineticCycle.setEnabled(False)
        elif acq_mode == 1:
            self.accumulationFrames.setEnabled(True)
            self.accumulationCycle.setEnabled(True)
            self.kineticSeries.setEnabled(False)
            self.kineticCycle.setEnabled(False)
        elif acq_mode == 2:
            self.accumulationFrames.setEnabled(True)
            self.accumulationCycle.setEnabled(True)
            self.kineticSeries.setEnabled(True)
            self.kineticCycle.setEnabled(True)
        elif acq_mode == 3:
            self.accumulationFrames.setEnabled(False)
            self.accumulationCycle.setEnabled(True)
            self.kineticSeries.setEnabled(True)
            self.kineticCycle.setEnabled(False)
        elif acq_mode == 4:
            self.accumulationFrames.setEnabled(False)
            self.accumulationCycle.setEnabled(False)
            self.kineticSeries.setEnabled(False)
            self.kineticCycle.setEnabled(True)

    def ui_construct(self, conf):
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

        view_area = QTabWidget(self)
        view_area.setTabPosition(QTabWidget.West)
        ccd = QFrame(self)
        view_area.addTab(ccd, "Spectra acquisition")
        view_area.addTab(self.CameraWI, "Camera")

        view_area_lay = QVBoxLayout(topright_frame)
        view_area_lay.addWidget(view_area)

        # --- Controls frame ---

        self.monoGridPos = QDoubleSpinBox(self)
        self.monoGridPos.setRange(200.0, 1000.0)
        self.monoGridPos.setSingleStep(0.1)
        self.monoGridPos.setDecimals(1)
        self.monoSetPos = QPushButton('Set')
        self.monoSetPos.setMinimumSize(90, 30)
        self.monoCalibrate = QPushButton('Calibration')
        self.monoCalibrate.setMinimumSize(90, 30)
        self.monoStop = QPushButton('Stop')
        self.monoStop.setMinimumSize(90, 30)
        self.monoCurrentPos = QLabel('500.00 nm')
        mono_pos_lbl = QLabel('Current position: ')
        self.monoGridSelect = QComboBox(self)
        self.monoGridSelect.addItems(['300 g/mm', '600 g/mm'])
        mono_grid_lbl = QLabel('Grating: ')

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
        self.x_up.setMinimumSize(85, 30)
        self.x_down.setMinimumSize(85, 30)
        self.x_down.setMinimumSize(85, 30)
        self.y_up.setMinimumSize(85, 30)
        self.y_down.setMinimumSize(85, 30)
        self.z_up.setMinimumSize(85, 30)
        self.z_down.setMinimumSize(85, 30)
        self.stop_move.setMinimumSize(85, 30)

        self.x_pos = QTableWidgetItem()
        self.x_pos.setTextAlignment(Qt.AlignCenter)
        self.y_pos = QTableWidgetItem()
        self.y_pos.setTextAlignment(Qt.AlignCenter)
        self.z_pos = QTableWidgetItem()
        self.z_pos.setTextAlignment(Qt.AlignCenter)

        self.acquire_btn = QPushButton('Acquire')
        self.acquire_btn.setFixedSize(120, 60)

        stage_coordinates = QTableWidget(3, 1)
        stage_coordinates.setEditTriggers(QAbstractItemView.NoEditTriggers)
        stage_coordinates.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        stage_coordinates.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        stage_coordinates.setStyleSheet("border: 0")
        stage_coordinates.setHorizontalHeaderLabels(['Position'])
        stage_coordinates.setVerticalHeaderLabels(['X', 'Y', 'Z'])
        stage_coordinates.setItem(0, 0, self.x_pos)
        stage_coordinates.setItem(1, 0, self.y_pos)
        stage_coordinates.setItem(2, 0, self.z_pos)

        mono_control_group = QGroupBox('Monochromator')
        mono_control_group.setAlignment(Qt.AlignCenter)
        mono_control_lay = QGridLayout(mono_control_group)
        mono_control_lay.addWidget(self.monoGridPos, 0, 0)
        mono_control_lay.addWidget(self.monoSetPos, 0, 1)
        mono_control_lay.addWidget(self.monoCalibrate, 1, 0)
        mono_control_lay.addWidget(self.monoStop, 1, 1)
        mono_control_lay.addWidget(mono_pos_lbl, 2, 0)
        mono_control_lay.addWidget(self.monoCurrentPos, 2, 1)
        mono_control_lay.addWidget(mono_grid_lbl, 3, 0)
        mono_control_lay.addWidget(self.monoGridSelect, 3, 1)

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
        light_source_lay.addWidget(self.laserPower, 0, 3, 4, 1)
        light_source_lay.setColumnMinimumWidth(2, 20)

        stage_pos_group = QGroupBox('Stage position')
        stage_pos_group.setAlignment(Qt.AlignCenter)
        stage_pos_lay = QGridLayout(stage_pos_group)
        stage_pos_lay.addWidget(self.x_up, 1, 2)
        stage_pos_lay.addWidget(self.x_down, 1, 0)
        stage_pos_lay.addWidget(self.y_up, 0, 1)
        stage_pos_lay.addWidget(self.y_down, 2, 1)
        stage_pos_lay.addWidget(self.z_up, 0, 3)
        stage_pos_lay.addWidget(self.z_down, 2, 3)
        stage_pos_lay.addWidget(self.stop_move, 1, 1)
        stage_pos_lay.addWidget(step_lbl, 3, 0)
        stage_pos_lay.addWidget(self.step_val, 3, 1)
        stage_pos_lay.addWidget(self.distance_lbl, 3, 2, 1, 2)
        stage_pos_lay.setColumnMinimumWidth(4, 20)
        stage_pos_lay.addWidget(stage_coordinates, 0, 5, 4, 1)

        acquire_btns_group = QFrame(self)
        acquire_btns_lay = QHBoxLayout(acquire_btns_group)
        acquire_btns_lay.addWidget(self.acquire_btn)

        action_btns_lay = QHBoxLayout(bottom_frame)
        action_btns_lay.addWidget(mono_control_group, 3)
        action_btns_lay.addWidget(light_source_group, 3)
        action_btns_lay.addWidget(stage_pos_group, 6)
        action_btns_lay.addWidget(acquire_btns_group, 3)
        action_btns_lay.setSpacing(20)

        # --- CCD Frame Layout ---

        self.CCDFrame = PgGraphicsView(self, aspect_locked=False)
        self.CCDFrame.setMinimumSize(512, 128)
        self.CCDFrame.vb.setLimits(xMin=0, xMax=conf['CCD-w']-1, yMin=0, yMax=conf['CCD-h']-1)
        self.vLine = CrossLine(angle=90, bounds=(0.5, 1023.5))
        self.hLine = CrossLine(angle=0, bounds=(0.5, 255.5))
        self.CCDFrame.vb.addItem(self.vLine)
        self.CCDFrame.vb.addItem(self.hLine)

        self.spectrum = PgPlotWidget(self, w='row')
        self.spectrum.plotItem.setLabels(left='Intensity')
        self.spectrum.vb.setYRange(0, 40000)
        self.spectrumCursor = CrossCursor()
        self.cursorPosLbl = pg.TextItem(text="X = 0, Y = 0", anchor=(-5, -1), color=pg.mkColor("#99999988"))
        self.cursorPosLbl.setParentItem(self.spectrum.vb)
        self.spectrum.vb.addItem(self.spectrumCursor)

        self.frameSection = PgPlotWidget(self, w='col')
        # self.frameSection.setLabels(right='Row')
        self.frameSection.vb.setYRange(0, conf['CCD-h']-1)
        self.frameSection.vb.setLimits(yMin=0, yMax=conf['CCD-h']-1)
        # self.frameSectionCurve = self.frameSection.plot(pen='y')
        self.frameSectionCursor = CrossCursor()
        self.frameSection.addItem(self.frameSectionCursor)

        self.frameRowSelect = QSpinBox(self)
        self.frameRowSelect.setRange(1, conf['CCD-h'])
        self.frameColSelect = QSpinBox(self)
        self.frameColSelect.setRange(1, conf['CCD-w'])

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

        ccd_lay = QGridLayout(ccd)
        ccd_lay.setRowStretch(0, 2)
        ccd_lay.setRowStretch(1, 3)
        ccd_lay.setColumnStretch(0, 1)
        ccd_lay.setColumnStretch(1, 6)
        ccd_lay.addWidget(self.CCDFrame, 0, 1)
        ccd_lay.addWidget(self.spectrum, 1, 1)
        ccd_lay.addWidget(self.frameSection, 0, 0)
        ccd_lay.addWidget(frame_param, 1, 0)

        # --- Experiment Details, Andor Camera Settings ---

        self.WLStart = QDoubleSpinBox(self)
        self.WLStart.setRange(200.0, 1000.0)
        self.WLStart.setSingleStep(0.1)
        self.WLStart.setDecimals(1)
        self.WLEnd = QLineEdit(self)
        self.WLEnd.setReadOnly(True)
        self.WLEnd_dec = QPushButton('<')
        self.WLEnd_inc = QPushButton('>')
        self.WLEnd_dec.setStyleSheet('QPushButton {min-width: 20px;}')
        self.WLEnd_inc.setStyleSheet('QPushButton {min-width: 20px;}')
        WL_range_lbl = QLabel('—')

        WL_range_group = QGroupBox("Wavelength range")
        WL_range_lay = QHBoxLayout(WL_range_group)
        WL_range_lay.addWidget(self.WLStart, 5)
        WL_range_lay.addWidget(WL_range_lbl, 1)
        WL_range_lay.addWidget(self.WLEnd, 5)
        WL_range_lay.addWidget(self.WLEnd_dec, 1)
        WL_range_lay.addWidget(self.WLEnd_inc, 1)

        self.exposureTime = QDoubleSpinBox(self)
        self.exposureTime.setRange(0.01, 1000.0)
        self.exposureTime.setDecimals(2)
        # self.exposureTime.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
        exp_time_lbl = QLabel('Exposure time (sec)')

        temperature_lbl = QLabel('Temperature (°C):')
        self.tCurrent = QLabel('--')
        self.tCurrent.setStyleSheet("font-weight: bold; color: yellow")
        self.tSet = QPushButton('Set')
        self.tSet.setStyleSheet('QPushButton {min-width: 45px;}')

        self.acquisitionMode = QComboBox(self)
        self.acquisitionMode.addItems(['Single', 'Accumulate', 'Kinetic', 'Fast Kinetic', 'Continuous'])
        # self.acquisitionMode.model().item(4).setEnabled(False)
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
        self.readoutRate.addItems(['3MHz at 16-bit', '1MHz at 16-bit', '50kHz at 16-bit'])
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

        cam_temperature_group = QGroupBox("CCD temperature")
        cam_temperature_lay = QGridLayout(cam_temperature_group)
        cam_temperature_lay.addWidget(temperature_lbl, 0, 0)
        cam_temperature_lay.addWidget(self.tCurrent, 0, 1)
        cam_temperature_lay.addWidget(self.tSet, 0, 2)

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

        cam_settings_lay.addWidget(WL_range_group)
        cam_settings_lay.addWidget(cam_exposure_group)
        cam_settings_lay.addWidget(cam_temperature_group)
        cam_settings_lay.addWidget(cam_timing_group)
        cam_settings_lay.addWidget(cam_mode_group)
        cam_settings_lay.addWidget(cam_readout_group)


class SetTemperatureWindow(QMainWindow):
    def __init__(self, ccd):
        super().__init__()

        self.setup_ui()

        self.ccd = ccd

        rng = self.ccd.get_temperature_range()
        sr = "{1} to {0}"
        self.tTarget.setMinimum(rng[0])
        self.tTarget.setMaximum(rng[1])
        self.tRange.setText(sr.format(*rng))

        self.tSet.clicked.connect(self.set_temperature)
        self.cooler.buttonClicked.connect(self.set_cooler)

        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    def setup_ui(self):
        temperature_group = QFrame(self)
        self.tTarget = QSpinBox(self)
        self.tSet = QPushButton('Set temperature')
        self.tCurrent = QLabel('--')
        self.tCurrent.setStyleSheet("font-weight: bold")
        self.tRange = QLabel()
        self.tRange.setStyleSheet("color: grey")
        temperature_lbl = QLabel('Current temperature: ')
        range_lbl = QLabel('Temperature range: ')
        range_lbl.setStyleSheet("color: grey")
        temperature_lay = QGridLayout(temperature_group)
        temperature_lay.addWidget(temperature_lbl, 0, 0)
        temperature_lay.addWidget(self.tCurrent, 0, 1)
        temperature_lay.addWidget(self.tTarget, 1, 0)
        temperature_lay.addWidget(self.tSet, 1, 1)
        temperature_lay.addWidget(range_lbl, 2, 0)
        temperature_lay.addWidget(self.tRange, 2, 1)

        cooler_group = QFrame(self)
        cooler_radio0 = QRadioButton('On')
        cooler_radio1 = QRadioButton('Off')
        cooler_radio1.setChecked(True)
        self.cooler = QButtonGroup(self)
        self.cooler.addButton(cooler_radio0, id=0)
        self.cooler.addButton(cooler_radio1, id=1)
        cooler_lbl = QLabel('Cooler: ')
        cooler_lay = QHBoxLayout(cooler_group)
        cooler_lay.addWidget(cooler_lbl)
        cooler_lay.addWidget(cooler_radio0)
        cooler_lay.addWidget(cooler_radio1)

        cooling_settings = QGroupBox("CCD Cooling settings")
        cooling_settings_lay = QVBoxLayout(cooling_settings)
        cooling_settings_lay.addWidget(temperature_group)
        cooling_settings_lay.addWidget(cooler_group)

        # confirmation_group = QFrame(self)
        # self.confirmButton = QPushButton('Close')
        # confirmation_lay = QHBoxLayout(confirmation_group)
        # confirmation_lay.addStretch()
        # confirmation_lay.addWidget(self.confirmButton)
        # confirmation_lay.addStretch()

        main_widget = QFrame(self)
        main_lay = QVBoxLayout(main_widget)
        main_lay.addWidget(cooling_settings)
        # main_lay.addWidget(confirmation_group)

        self.setCentralWidget(main_widget)

    def set_cooler(self):
        if self.cooler.button(0).isChecked():
            self.ccd.set_cooler(True)
        else:
            self.ccd.set_temperature(-10)

    def set_temperature(self):
        t = self.tTarget.value()
        self.ccd.set_temperature(t)

        if not self.cooler.button(0).isChecked():
            self.cooler.button(0).setChecked(True)

    def open(self):
        self.show()
