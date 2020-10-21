from functools import partial
from math import ceil
import json

import numpy as np
import matplotlib.image as mpimg


class SpectraModuleActions(object):

    def __init__(self, ui, p_set, hardware, ccd):
        self.columns = np.arange(1024)
        self.rows = np.arange(255)

        # frame data array and coordinates, default coordinates as pixel number
        self.framedata = np.zeros((255, 1024), dtype=np.uint16)
        self.coordinates = self.columns.astype(dtype=np.float)
        self.n_factor = 1

        # self.framedata = np.random.randint(0, 50, (255, 1024), dtype=np.uint16)

        self.mainform = ui
        self.paramSet = p_set
        self.hardware = hardware
        self.ccd = ccd

        self.connect_events()

    def connect_events(self):
        mf = self.mainform

        mf.x_up.clicked.connect(partial(self.stage_move, 'X', 1))
        mf.x_down.clicked.connect(partial(self.stage_move, 'X', -1))
        mf.y_up.clicked.connect(partial(self.stage_move, 'Y', 1))
        mf.y_down.clicked.connect(partial(self.stage_move, 'Y', -1))
        mf.z_up.clicked.connect(partial(self.stage_move, 'Z', 1))
        mf.z_down.clicked.connect(partial(self.stage_move, 'Z', -1))
        mf.stop_move.clicked.connect(self.stage_stop)

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

        mf.XUnits.buttonClicked.connect(self.x_units_change)
        mf.YUnits.buttonClicked.connect(self.y_units_change)

        # Monochromator Actions
        mf.WLStart.editingFinished.connect(self.WL_start_change)
        mf.WLStart.editingFinished.connect(self.WL_end_change)
        mf.monoSetPos.clicked.connect(self.mono_move)
        mf.monoGridSelect.currentIndexChanged.connect(self.mono_grid_select)

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

    def x_units_change(self, button):
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

    def y_units_change(self, button):
        id = self.mainform.YUnits.id(button)
        self.paramSet['frameSet']['y-axis'] = id

        if id == 1:
            self.n_factor = 1 / self.mainform.exposureTime.value()
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

    def exposure_change(self):
        exp_time = self.mainform.exposureTime.value()
        self.paramSet['Andor']['exposure'] = exp_time
        # self.ccd.set_exposure(exp_time)

    def acq_mode_change(self, mode):
        self.paramSet['Andor']['AcqMode']['mode'] = mode
        self.mainform.mode_prm_enable(mode)
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

    def WL_start_change(self):
        val = self.mainform.WLStart.value()
        self.paramSet['MDR-3']['WL-start'] = val

    def WL_end_change(self):
        val = self.mainform.WLEnd.value()
        self.paramSet['MDR-3']['WL-end'] = val

    def mono_move(self):
        pos = self.mainform.monoGridPos.value()
        self.paramSet['MDR-3']['grating-pos'] = pos
        # move ...

    def mono_grid_select(self, grid_idx):
        self.paramSet['MDR-3']['grating-select'] = grid_idx

    def stepinfo_change(self, val):
        steps = int(val)
        self.paramSet['stagePos']['step'] = steps

        dst = "{0:.2f}".format(self.hardware.minStageStep * steps)
        self.mainform.distance_lbl.setText('Distance: ' + dst + 'um')

    def stage_move(self, axis, direction, checked=False):
        steps = int(self.mainform.step_val.currentText()) * direction

        self.hardware.move_relaive(axis, steps)
        new_pos = int(self.mainform.x_pos.text()) + steps
        self.paramSet['stagePos'][axis] = new_pos

        if axis == 'X':
            self.mainform.x_pos.setText(str(new_pos))
        elif axis == 'Y':
            self.mainform.y_pos.setText(str(new_pos))
        elif axis == 'Z':
            self.mainform.z_pos.setText(str(new_pos))

    def stage_stop(self):
        for axis in ('X', 'Y', 'Z'):
            self.hardware.mot_stop(axis)

        for axis in ('X', 'Y', 'Z'):
            pos = self.hardware.stage_pos(axis)
            self.paramSet['stagePos'][axis] = pos
            self.mainform.x_pos.setText(str(pos))

    def get_frame(self):
        # self.framedata = self.ccd.get_data()
        # self.framedata = np.random.randint(0, 150, (255, 1024), dtype=np.uint16)

        data = mpimg.imread('ccd-frame2_bw.png') * 65536
        self.framedata = np.dot(data[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint16)

        # gray_color_table = [qRgb(i, i, i) for i in range(256)]

    def acquire(self):
        self.get_frame()
        self.mainform.image.setImage(self.framedata)
        self.upd_spectrum()
        self.upd_frame_section()
