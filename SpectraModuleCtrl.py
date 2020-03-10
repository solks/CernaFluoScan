from functools import partial
from math import ceil
import json

import numpy as np
import matplotlib.image as mpimg

from HardWare import *
from AndorCCD import *


class SpectraModuleCtrl(object):

    MOT_X = 0
    MOT_Y = 1
    MOT_Z = 2

    MOT_UP = 1
    MOT_DOWN = -1

    def __init__(self, w):
        self.columns = np.arange(1024)
        self.rows = np.arange(255)

        # frame data array and coordinates, default coordinates as pixel number
        self.framedata = np.zeros((255, 1024), dtype=np.uint16)
        self.coordinates = self.columns.astype(dtype=np.float)
        self.n_factor = 1

        # self.framedata = np.random.randint(0, 50, (255, 1024), dtype=np.uint16)

        self.mainform = w

        self.paramSet = []
        self.storeParameters = True
        self.init_parameters()

        self.connect_events()

        self.hardware = HardWare()
        #self.ccd = AndorCCD(self.paramSet['Andor'])

    def init_parameters(self):
        if self.storeParameters:
            # read parameters from json
            with open('current-params.json', 'r') as f:
                self.paramSet = json.load(f)

        else:
            # default
            with open('default-params.json', 'r') as f:
                self.paramSet = json.load(f)

        mf = self.mainform
        frame_p = self.paramSet['frameSet']
        stage_p = self.paramSet['stagePos']
        andor_p = self.paramSet['Andor']

        # Frame parameter set
        mf.frameRowSelect.setValue(frame_p['row'])
        mf.frameColSelect.setValue(frame_p['column'])
        mf.vLine.setPos(frame_p['row'])
        mf.hLine.setPos(frame_p['column'])

        mf.rowBinning.setValue(frame_p['binning'])
        if frame_p['binningAvg']:
            mf.avgBinning.setChecked(True)

        mf.XUnits.button(frame_p['x-axis']).setChecked(True)
        self.x_units_changed(mf.XUnits.button(frame_p['x-axis']))

        mf.YUnits.button(frame_p['y-axis']).setChecked(True)
        self.y_units_changed(mf.YUnits.button(frame_p['y-axis']))

        # Hardware parameter set
        mf.x_pos.setText(str(stage_p['x']))
        mf.y_pos.setText(str(stage_p['y']))
        mf.z_pos.setText(str(stage_p['z']))
        mf.step_val.setCurrentText(str(stage_p['step']))

        mf.laserSelect.setCurrentIndex(self.paramSet['Laser']['source-id'])

        # Andor parameter set
        acq_mode = andor_p['AcqMode']['mode']
        mf.exposureTime.setValue(andor_p['exposure'])
        mf.acquisitionMode.setCurrentIndex(andor_p['AcqMode']['mode'])
        self.mode_prm_enable(andor_p['AcqMode']['mode'])
        mf.accumulationFrames.setValue(andor_p['AcqMode']['accumFrames'])
        mf.accumulationCycle.setValue(andor_p['AcqMode']['accumCycle'])
        mf.kineticSeries.setValue(andor_p['AcqMode']['kSeries'])
        mf.kineticCycle.setValue(andor_p['AcqMode']['kCycle'])
        mf.triggeringMode.setCurrentIndex(andor_p['trigMode'])
        mf.readoutMode.setCurrentIndex(andor_p['readMode'])
        mf.VSSpeed.setCurrentIndex(andor_p['VSSpeed'])
        mf.VSAVoltage.setCurrentIndex(andor_p['VSAVoltage'])
        mf.readoutRate.setCurrentIndex(andor_p['ADCRate'])
        mf.preAmpGain.setCurrentIndex(andor_p['gain'])


    def connect_events(self):
        mf = self.mainform

        mf.x_up.clicked.connect(partial(self.stage_move, self.MOT_X, self.MOT_UP))
        mf.x_down.clicked.connect(partial(self.stage_move, self.MOT_X, self.MOT_DOWN))
        mf.y_up.clicked.connect(partial(self.stage_move, self.MOT_Y, self.MOT_UP))
        mf.y_down.clicked.connect(partial(self.stage_move, self.MOT_Y, self.MOT_DOWN))
        mf.z_up.clicked.connect(partial(self.stage_move, self.MOT_Z, self.MOT_UP))
        mf.z_down.clicked.connect(partial(self.stage_move, self.MOT_Z, self.MOT_DOWN))
        # self.widget.stop_move.clicked.connect(self.hardware.mot_stop)

        mf.acquire_btn.clicked.connect(self.acquire)

        mf.step_val.currentTextChanged.connect(self.stepinfo_change)

        mf.vLine.sigPositionChanged.connect(self.ccd_vline_pos)
        mf.hLine.sigPositionChanged.connect(self.ccd_hline_pos)
        mf.frameColSelect.valueChanged.connect(self.ccd_col_select)
        mf.frameRowSelect.valueChanged.connect(self.ccd_row_select)

        mf.spectrum.scene().sigMouseMoved.connect(self.spectrum_cursor_pos)
        # mf.spectrum.scene().sigMouseClicked.connect(self.spectrum_mouse_click)

        mf.rowBinning.valueChanged.connect(self.ccd_row_binning)
        mf.avgBinning.stateChanged.connect(self.ccd_row_binning)

        mf.XUnits.buttonClicked.connect(self.x_units_changed)
        mf.YUnits.buttonClicked.connect(self.y_units_changed)

        # Andor actions
        mf.exposureTime.editingFinished.connect(self.exposure_change)
        mf.acquisitionMode.currentIndexChanged.connect(self.acq_mode_change)
        mf.triggeringMode.currentIndexChanged.connect(self.trig_mode_change)
        mf.readoutMode.currentIndexChanged.connect(self.read_mode_change)
        mf.accumulationFrames.editingFinished.connect(self.accum_frames_change)
        mf.accumulationCycle.editingFinished.connect(self.accum_cycle_change)
        mf.kineticSeries.editingFinished.connect(self.knt_series_change)
        mf.kineticCycle.editingFinished.connect(self.knt_cycle_change)
        mf.readoutRate.currentIndexChanged.connect(self.adc_rate_change)
        mf.preAmpGain.currentIndexChanged.connect(self.gain_change)
        mf.VSSpeed.currentIndexChanged.connect(self.shift_speed_change)
        mf.VSAVoltage.currentIndexChanged.connect(self.shift_speed_change)

    def ccd_vline_pos(self, e):
        column = ceil(e.getXPos())
        self.paramSet['frameSet']['column'] = column
        self.upd_frame_section(column - 1)
        self.mainform.frameColSelect.setValue(column)

    def ccd_hline_pos(self, e):
        row = ceil(e.getYPos())
        self.paramSet['frameSet']['row'] = row
        self.upd_spectrum(row - 1)
        self.mainform.frameRowSelect.setValue(row)

    def ccd_col_select(self, val):
        self.paramSet['frameSet']['column'] = val
        self.upd_frame_section(val)
        self.mainform.vLine.setPos([val, 0])

    def ccd_row_select(self, val):
        self.paramSet['frameSet']['row'] = val
        self.upd_spectrum(val)
        self.mainform.hLine.setPos([0, val])

    def spectrum_cursor_pos(self, e):
        # pos = (e.x(), e.y())
        pos = e
        if self.mainform.spectrum.sceneBoundingRect().contains(pos):
            mouse_point = self.mainform.spectrum.plotItem.vb.mapSceneToView(pos)
            self.mainform.cursorPosLbl.setText("X = %0.1f, Y = %0.1f"
                                               % (mouse_point.x(), mouse_point.y()))
            self.mainform.spectrumCursor.setPos((mouse_point.x()/2.0, mouse_point.y()/2.0))

    # def spectra_mouse_click(self, e):
    #     if e.button() == Qt.RightButton:
    #         self.mainform.spectrum.autoRange()

    def ccd_row_binning(self, val):
        self.paramSet['frameSet']['binning'] = val
        self.upd_spectrum()

    def x_units_changed(self, button):
        id = self.mainform.XUnits.id(button)
        self.paramSet['frameSet']['x-axis'] = id

        if id == 0:
            # nm
            central_WL = self.paramSet['MDR-3']['grating-pos']
            WL_range  = 250
            for i in self.columns:
                self.coordinates[i] = central_WL + (i - 512) * WL_range / 1024.0

            self.mainform.spectrum.setLabels(bottom='Wavelength (nm)')

        elif id == 1:
            # eV
            central_WL = self.paramSet['MDR-3']['grating-pos']
            WL_range = 250
            for i in self.columns:
                self.coordinates[i] = 1239.84193 / (central_WL + (i - 512) * WL_range / 1024.0)

            self.mainform.spectrum.setLabels(bottom='Energy (eV)')

        else:
            # pixel number
            self.coordinates = self.columns.astype(dtype=np.float)
            self.mainform.spectrum.setLabels(bottom='Pixel number')

        self.upd_spectrum()

        vb = self.mainform.spectrumCurve.getViewBox()
        if self.coordinates[0] < self.coordinates[1023]:
            vb.setXRange(self.coordinates[0], self.coordinates[1023], padding=0)
            vb.setLimits(xMin=self.coordinates[0], xMax=self.coordinates[1023])
        else:
            vb.setXRange(self.coordinates[1023], self.coordinates[0], padding=0)
            vb.setLimits(xMin=self.coordinates[1023], xMax=self.coordinates[0])

    def y_units_changed(self, button):
        id = self.mainform.YUnits.id(button)
        self.paramSet['frameSet']['y-axis'] = id

        if id == 1:
            self.n_factor = 1 / float(self.mainform.exposureTime.currentText())
        else:
            self.n_factor = 1

        self.upd_spectrum()

    def upd_spectrum(self, row=-1):
        if row == -1:
            row = self.mainform.frameRowSelect.value() - 1

        num_rows = self.mainform.rowBinning.value()

        if num_rows > 1:
            min_row = ceil(row - num_rows / 2)
            max_row = ceil(row + num_rows / 2)

            if self.mainform.avgBinning.isChecked():
                self.mainform.spectrumCurve.setData(
                    x=self.coordinates,
                    y=np.average(self.framedata[min_row:max_row, :], axis=0) * self.n_factor
                )
            else:
                self.mainform.spectrumCurve.setData(
                    x=self.coordinates,
                    y=np.sum(self.framedata[min_row:max_row, :], axis=0) * self.n_factor
                )
        else:
            self.mainform.spectrumCurve.setData(x=self.coordinates, y=self.framedata[row, :] * self.n_factor)

    def upd_frame_section(self, column=-1):
        if column == -1:
            column = self.mainform.frameColSelect.value() - 1

        self.mainform.frameSectionCurve.setData(x=self.framedata[:, column], y=self.rows)

    def mode_prm_enable(self, acq_mode):
        if acq_mode == 0:
            self.mainform.accumulationFrames.setEnabled(False)
            self.mainform.accumulationCycle.setEnabled(False)
            self.mainform.kineticSeries.setEnabled(False)
            self.mainform.kineticCycle.setEnabled(False)
        elif acq_mode == 1:
            self.mainform.accumulationFrames.setEnabled(True)
            self.mainform.accumulationCycle.setEnabled(True)
            self.mainform.kineticSeries.setEnabled(False)
            self.mainform.kineticCycle.setEnabled(False)
        elif acq_mode == 2:
            self.mainform.accumulationFrames.setEnabled(True)
            self.mainform.accumulationCycle.setEnabled(True)
            self.mainform.kineticSeries.setEnabled(True)
            self.mainform.kineticCycle.setEnabled(True)
        elif acq_mode == 4:
            self.mainform.accumulationFrames.setEnabled(False)
            self.mainform.accumulationCycle.setEnabled(True)
            self.mainform.kineticSeries.setEnabled(True)
            self.mainform.kineticCycle.setEnabled(False)

    def exposure_change(self):
        exp_time = self.mainform.exposureTime.value()
        self.paramSet['Andor']['exposure'] = exp_time
        # self.ccd.set_exposure(exp_time)

    def acq_mode_change(self, mode):
        self.paramSet['Andor']['AcqMode']['mode'] = mode
        self.mode_prm_enable(mode)
        # self.ccd.set_acq_mode(mode)

    def trig_mode_change(self, mode):
        self.paramSet['Andor']['trigMode'] = mode
        # self.ccd.set_trig_mode(mode)

    def read_mode_change(self, mode):
        self.paramSet['Andor']['readMode'] = mode
        # self.ccd.set_read_mode(mode)

    def accum_frames_change(self):
        n = self.mainform.accumulationFrames.value()
        self.paramSet['Andor']['AcqMode']['accumFrames'] = n
        # self.ccd.set_accum_frames(n)

    def accum_cycle_change(self):
        cycle_time = self.mainform.accumulationCycle.value()
        self.paramSet['Andor']['AcqMode']['accumCycle'] = cycle_time
        # self.ccd.set_accum_cycle(cycle_time)

    def knt_series_change(self):
        n = self.mainform.kineticSeries.value()
        self.paramSet['Andor']['AcqMode']['kSeries'] = n
        # self.ccd.set_knt_series(n)

    def knt_cycle_change(self):
        cycle_time = self.mainform.kineticCycle.value()
        self.paramSet['Andor']['AcqMode']['kCycle'] = cycle_time
        # self.ccd.set_knt_cycle(cycle_time)

    def adc_rate_change(self, rate_idx):
        self.paramSet['Andor']['ADCRate'] = rate_idx
        # self.ccd.set_adc_rate(rate_idx)

    def gain_change(self, gain_idx):
        self.paramSet['Andor']['gain'] = gain_idx
        # self.ccd.set_gain(gain_idx)

    def shift_speed_change(self, speed_idx):
        self.paramSet['Andor']['VSSpeed'] = speed_idx
        # self.ccd.set_shift_speed(speed_idx)

    def vsa_volt_change(self, vsa_idx):
        self.paramSet['Andor']['VSAVoltage'] = vsa_idx
        # self.ccd.set_vsa_volt(vsa_idx)

    def stepinfo_change(self, val):
        steps = int(val)
        self.paramSet['stagePos']['step'] = steps

        dst = "{0:.2f}".format(self.hardware.STAGE_STEP_DST * steps)
        self.mainform.distance_lbl.setText('Distance: ' + dst + 'um')

    def stage_move(self, stage_id, direction, checked=False):
        steps = int(self.mainform.step_val.currentText())

        if direction == self.MOT_DOWN:
            steps = -steps

        if stage_id == self.MOT_X:
            self.hardware.move_x(steps)
            new_pos = int(self.mainform.x_pos.text()) + steps
            self.paramSet['stagePos']['x'] = new_pos
            self.mainform.x_pos.setText(str(new_pos))

        elif stage_id == self.MOT_Y:
            self.hardware.move_y(steps)
            new_pos = int(self.mainform.y_pos.text()) + steps
            self.paramSet['stagePos']['y'] = new_pos
            self.mainform.y_pos.setText(str(new_pos))

        elif stage_id == self.MOT_Z:
            self.hardware.move_z(steps)
            new_pos = int(self.mainform.z_pos.text()) + steps
            self.paramSet['stagePos']['z'] = new_pos
            self.mainform.z_pos.setText(str(new_pos))

    def get_frame(self):
        # self.framedata = self.ccd.get_data()
        # self.framedata = np.random.randint(0, 150, (255, 1024), dtype=np.uint16)

        data = mpimg.imread('ccd-frame2_bw.png') * 65536
        self.framedata = np.dot(data[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint16)

        # gray_color_table = [qRgb(i, i, i) for i in range(256)]

    def acquire(self):
        self.get_frame()
        self.mainform.CCDFrame.getImageItem().setImage(self.framedata)
        self.upd_spectrum()
        self.upd_frame_section()

    def shut_down(self):
        print('Shutting down the camera...')
        # self.ccd.shut_down()

        print('Save parameters...')
        with open('current-params.json', 'w') as f:
            json.dump(self.paramSet, f, indent=4)
