import time
from functools import partial
from math import ceil
from threading import Thread, Event
from PyQt5.QtCore import QThread, QRunnable, QThreadPool, pyqtSignal, pyqtSlot, QObject

import numpy as np


class SpectraModuleActions(QObject):

    spectraOverlap = 80

    spectraFinished = pyqtSignal()

    def __init__(self, ui, p_set, hardware, ccd):
        super().__init__()

        self.mainform = ui
        self.paramSet = p_set
        self.hardware = hardware
        self.ccd = ccd

        self.ccdWidth = self.ccd.conf['CCD-w']
        self.ccdHeight = self.ccd.conf['CCD-h']

        self.spWidth = self.ccdWidth

        # frame data array and coordinates, default coordinates as pixel number
        self.spData = np.zeros((self.ccdHeight, self.ccdWidth), dtype=np.uint16)
        self.coordinates = np.arange(self.spWidth, dtype=np.float)
        self.n_factor = 1

        self.monoRoutine = Thread()
        self.mono_positions = [None]*self.paramSet['MDR-3']['WL-inc']

        self.spCmp = SpectrumCompilation(self.ccd, self.hardware, self.spectraFinished)
        self.spCmp.set_frame_size(self.spData, self.ccdWidth, self.spectraOverlap)
        self.spCmp.start()

        self.monoChkState = MonoChkState(self.hardware, self.mainform, self.paramSet['MDR-3'])
        self.monoChkState.setAutoDelete(False)

        # self.framedata = np.zeros((255, 2048), dtype=np.uint16)
        # self.spectrumAcquisition.setArr()
        # print(self.framedata[1,1])

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
        self.spectraFinished.connect(self.show_spectrum)

        mf.step_val.currentTextChanged.connect(self.stepinfo_change)

        # Monochromator Actions
        mf.WLStart.editingFinished.connect(self.WL_start_change)
        mf.WLEnd_dec.clicked.connect(self.WL_end_dec)
        mf.WLEnd_inc.clicked.connect(self.WL_end_inc)
        mf.monoSetPos.clicked.connect(self.mono_centralWL_set)
        mf.monoGridSelect.currentIndexChanged.connect(self.mono_grid_select)
        mf.monoStartup.connect(self.startup)

        # Spectrum Actions
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
        self.upd_frame_section(val - 1)
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

    def x_units_change(self):
        units_id = self.mainform.XUnits.checkedId()
        self.paramSet['frameSet']['x-axis'] = units_id

        strip_size = self.ccdWidth - self.spectraOverlap
        if units_id == 0:
            # nm
            for i, p in enumerate(self.mono_positions):
                offset_idx = i*strip_size
                for n in range(strip_size):
                    self.coordinates[offset_idx + n] = self.hardware.mono_toWL(p, n)
            for n in range(strip_size, self.ccdWidth):
                self.coordinates[offset_idx + n] = self.hardware.mono_toWL(p, n)

            self.mainform.spectrum.plotItem.setLabels(bottom='Wavelength (nm)')

        elif units_id == 1:
            # eV
            for i, p in enumerate(self.mono_positions):
                offset_idx = i*strip_size
                for n in range(strip_size):
                    self.coordinates[offset_idx + n] = 1239.84193 / self.hardware.mono_toWL(p, n)
            for n in range(strip_size, self.ccdWidth):
                self.coordinates[offset_idx + n] = 1239.84193 / self.hardware.mono_toWL(p, n)

            self.mainform.spectrum.plotItem.setLabels(bottom='Energy (eV)')

        else:
            # pixel number
            self.coordinates = np.arange(self.spWidth, dtype=np.float)
            self.mainform.spectrum.plotItem.setLabels(bottom='Pixel number')

        self.upd_spectrum()

        spectrum_vb = self.mainform.spectrum.vb
        if self.coordinates[0] < self.coordinates[self.spWidth-1]:
            spectrum_vb.setXRange(self.coordinates[0], self.coordinates[self.spWidth-1], padding=0.02)
            # spectrum_vb.setLimits(xMin=self.coordinates[0], xMax=self.coordinates[self.spWidth-1])
        else:
            spectrum_vb.setXRange(self.coordinates[self.spWidth-1], self.coordinates[0], padding=0.02)
            # spectrum_vb.setLimits(xMin=self.coordinates[self.spWidth-1], xMax=self.coordinates[0])

    def y_units_change(self):
        units_id = self.mainform.YUnits.checkedId()
        self.paramSet['frameSet']['y-axis'] = units_id

        if units_id == 1:
            self.n_factor = 1 / self.mainform.exposureTime.value()
        else:
            self.n_factor = 1

        self.upd_spectrum()

    def upd_spectrum(self, row=-1):
        if row == -1:
            row = self.mainform.frameRowSelect.value() - 1

        bin_rows = self.mainform.rowBinning.value()

        if bin_rows > 1:
            min_row = ceil(row - bin_rows / 2)
            max_row = ceil(row + bin_rows / 2)

            if self.mainform.avgBinning.isChecked():
                self.mainform.spectrum.curve.setData(
                    x=self.coordinates,
                    y=np.average(self.spData[min_row:max_row, :], axis=0) * self.n_factor
                )
            else:
                self.mainform.spectrum.curve.setData(
                    x=self.coordinates,
                    y=np.sum(self.spData[min_row:max_row, :], axis=0) * self.n_factor
                )
        else:
            self.mainform.spectrum.curve.setData(
                x=self.coordinates,
                y=self.spData[row, :] * self.n_factor
            )

    def upd_frame_section(self, column=-1):
        if column == -1:
            column = self.mainform.frameColSelect.value() - 1

        self.mainform.frameSection.curve.setData(x=self.spData[:, column], y=np.arange(self.ccdHeight))

    def resize_spectrum(self, pcs, keep_previous=False):
        # resizing spectrum data array
        self.spWidth = (self.ccdWidth - self.spectraOverlap) * pcs + self.spectraOverlap

        previous_data = self.spData
        previous_data_width = self.spData.shape[1]
        self.spData = np.zeros((self.ccdHeight, self.spWidth), dtype=np.uint16)
        if keep_previous:
            if previous_data_width < self.spData.shape[1]:
                self.spData[:, 0:previous_data_width] = previous_data
            else:
                data_width = self.spData.shape[1]
                self.spData = previous_data[:, 0:data_width]

        self.spCmp.set_frame_size(self.spData, self.ccdWidth, self.spectraOverlap)
        self.coordinates = np.arange(self.spWidth, dtype=np.float)
        self.x_units_change()

        # updating all widget sizes
        self.mainform.CCDFrame.vb.setLimits(xMin=0, xMax=self.spWidth-1, yMin=0, yMax=self.ccdHeight-1)
        self.mainform.vLine.setBounds((0.5, self.spWidth-0.5))
        self.mainform.frameColSelect.setRange(1, self.spWidth)

    def WL_start_change(self):
        WL_start = self.mainform.WLStart.value()
        self.paramSet['MDR-3']['WL-start'] = WL_start

        # updating monochromator positions
        self.mono_positions[0] = self.hardware.mono_toSteps(WL_start)
        if self.paramSet['MDR-3']['WL-inc'] > 1:
            for i in range(1, self.paramSet['MDR-3']['WL-inc']):
                WL_next = self.hardware.mono_toWL(self.mono_positions[i-1], self.ccdWidth - self.spectraOverlap)
                steps_next = self.hardware.mono_toSteps(WL_next)
                self.mono_positions[i] = steps_next
        WL_end = self.hardware.mono_toWL(self.mono_positions[-1], self.ccdWidth)
        self.mainform.WLEnd.setText("{0:.2f}".format(WL_end))

        self.resize_spectrum(self.paramSet['MDR-3']['WL-inc'], False)
        self.spCmp.set_range_points(self.mono_positions)

    def WL_end_inc(self):
        WL_inc = self.hardware.mono_toWL(self.mono_positions[-1], self.ccdWidth - self.spectraOverlap)
        steps_inc = self.hardware.mono_toSteps(WL_inc)
        self.mono_positions.append(steps_inc)
        self.paramSet['MDR-3']['WL-inc'] += 1

        WL_end = self.hardware.mono_toWL(steps_inc, self.ccdWidth)
        self.mainform.WLEnd.setText("{0:.2f}".format(WL_end))

        self.resize_spectrum(self.paramSet['MDR-3']['WL-inc'], True)
        self.spCmp.set_range_points(self.mono_positions)

    def WL_end_dec(self):
        if self.paramSet['MDR-3']['WL-inc'] > 1:
            self.mono_positions.pop()
            self.paramSet['MDR-3']['WL-inc'] -= 1

            WL_end = self.hardware.mono_toWL(self.mono_positions[-1], self.ccdWidth)
            self.mainform.WLEnd.setText("{0:.2f}".format(WL_end))

            self.resize_spectrum(self.paramSet['MDR-3']['WL-inc'], True)
            self.spCmp.set_range_points(self.mono_positions)

    def mono_centralWL_set(self):
        # Position (in steps) is calculated according to the first pixel, WL - to the center pixel
        WL_set = self.mainform.monoGridPos.value()
        pos_cp = self.hardware.mono_toSteps(WL_set)
        WL_fp = WL_set - (self.hardware.mono_toWLC(pos_cp) - WL_set)
        pos_set = self.hardware.mono_toSteps(WL_fp)
        ret = self.hardware.mono_goto(pos_set)
        if ret == 'OK':
            # self.monoRoutine = Thread(target=self.upd_mono_pos)
            # self.monoRoutine.start()
            # self.monoChkState.run()
            QThreadPool.globalInstance().start(self.monoChkState)

    def startup(self):
        self.WL_start_change()
        self.resize_spectrum(self.paramSet['MDR-3']['WL-inc'])

        # Check current monochromator position
        current_pos = self.hardware.mono_pos()
        if current_pos is not False:
            current_WL = self.hardware.mono_toWLC(current_pos)
            self.paramSet['MDR-3']['WL-pos'] = current_WL
            self.mainform.monoCurrentPos.setText("{0:.2f}".format(current_WL) + ' nm')
        else:
            self.mainform.monoCurrentPos.setText(" -- ")
            self.mainform.statusBar.showMessage('Monochromator position error...')

    def mono_calibration(self):
        ans = self.hardware.mono_move_start()
        if ans == 'OK':
            # self.monoRoutine = Thread(target=self.upd_mono_pos)
            # self.monoRoutine.start()
            QThreadPool.globalInstance().start(self.monoChkState)
        elif ans == 'BUSY':
            self.mainform.statusBar.showMessage('Monochromator is busy. Please try again later.')
        else:
            self.mainform.statusBar.showMessage('Monochromator connection error...')

    def mono_grid_select(self, grid_idx):
        self.paramSet['MDR-3']['grating-select'] = grid_idx

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

    def show_spectrum(self):
        self.mainform.CCDFrame.image.setImage(self.spData)
        self.upd_spectrum()
        self.upd_frame_section()

    def acquire(self):
        self.spCmp.acquisition.set()
        # QThreadPool.globalInstance().start(self.monoChkState)

    def stop_threads(self):
        self.spCmp.stop()
        self.monoChkState.stop()


class MonoChkState(QRunnable):

    stop_event = Event()

    def __init__(self, hardware, mainform, p_set):
        super().__init__()

        self.hardware = hardware
        self.monoPosLbl = mainform.monoCurrentPos
        self.statusBar = mainform.statusBar
        self.paramSet = p_set

    def stop(self):
        if not self.stop_event.is_set():
            self.stop_event.set()

    def run(self):
        while not self.stop_event.is_set():
            time.sleep(0.5)
            current_pos = self.hardware.mono_pos()
            if current_pos is not False:
                current_WL = self.hardware.mono_toWLC(current_pos)
                self.paramSet['WL-pos'] = current_WL
                self.monoPosLbl.setText("{0:.2f}".format(current_WL) + ' nm')
            else:
                self.monoPosLbl.setText(" -- ")

            status = self.hardware.mono_status()
            if status == 'OK':
                break
            elif status == 'ERROR':
                self.statusBar.showMessage('Monochromator position check error...')
                break

        return


class SpectrumCompilation(QThread):

    acquisition = Event()
    frame_parsed = Event()
    stop_event = Event()

    mono_positions = []

    dataArray = []
    sp_size = 1024
    sp_overlap = 80

    frame_index = 0

    def __init__(self, ccd, hardware, finished):
        super().__init__()

        self.ccd = ccd
        self.hardware = hardware
        self.finished = finished

        self.ccd.frameAcquired.connect(self.framedata_handler)

    def set_range_points(self, p):
        self.mono_positions = p

    # def setArr(self):
    #     self.dataArray[1,1] = 5

    def set_frame_size(self, data_array, strip_size, overlap):
        self.dataArray = data_array
        self.sp_size = strip_size
        self.sp_overlap = overlap

    def framedata_handler(self, data):
        idx1 = self.frame_index * (self.sp_size - self.sp_overlap)
        idx2 = self.frame_index * (self.sp_size - self.sp_overlap) + self.sp_size
        self.dataArray[:, idx1:idx2] = data
        self.frame_index += 1

        self.frame_parsed.set()

    def stop(self):
        if not self.stop_event.is_set():
            self.stop_event.set()

    def run(self):
        while not self.stop_event.is_set():
            if self.acquisition.wait(0.2):
                for pos in self.mono_positions:
                    self.hardware.mono_goto(pos)

                    while self.hardware.mono_status() != 'OK':
                        time.sleep(0.5)

                    self.ccd.frame()
                    self.frame_parsed.wait()
                    self.frame_parsed.clear()

                self.acquisition.clear()
                self.frame_index = 0

                self.finished.emit()

        return
