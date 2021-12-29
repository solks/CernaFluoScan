import time
from functools import partial
from math import ceil
from threading import Thread, Event

from PyQt5.QtCore import Qt, QThread, QRunnable, QThreadPool, QMutex, QEventLoop, QTimer, pyqtSignal, pyqtSlot, QObject

from SpectraModuleUI import SpectraModuleUI, SetTemperatureWindow

import numpy as np


class SpectraModule(SpectraModuleUI):

    spectraOverlap = 80

    spectrumAcquired = pyqtSignal()

    statusDataUpdated = pyqtSignal(dict)

    def __init__(self, cam_wi, ccd, hardware, hardware_conf, p_set, status_bar):
        super().__init__(cam_wi, hardware_conf)

        self.statusBar = status_bar
        self.paramSet = p_set
        self.hardware = hardware
        self.ccd = ccd

        self.tSettings = SetTemperatureWindow(self.ccd)

        self.ccdWidth = self.ccd.conf['CCD-w']
        self.ccdHeight = self.ccd.conf['CCD-h']

        self.spWidth = self.ccdWidth

        # frame data array and coordinates, default coordinates as pixel number
        self.spData = np.zeros((self.ccdHeight, self.ccdWidth), dtype=np.uint16)
        self.coordinates = np.arange(self.spWidth, dtype=np.float)
        self.n_factor = 1

        self.mono_positions = [None]*self.paramSet['MDR-3']['WL-inc']

        self.thread_pool = QThreadPool()
        self.mutex = QMutex()
        # self.thread_pool.setMaxThreadCount(3)

        self.spectrumCmp = SpectrumCompilation(self)
        self.spectrumCmp.set_frame_size(self.spData, self.ccdWidth, self.spectraOverlap)
        self.spectrumCmp.setAutoDelete(False)

        self.monoChkState = MonoChkState(self)
        self.monoChkState.setAutoDelete(False)

        self.statusUpdateThread = StatusUpdate(self)
        self.statusUpdateThread.start()

        # self.framedata = np.zeros((255, 2048), dtype=np.uint16)
        # self.spectrumAcquisition.setArr()
        # print(self.framedata[1,1])

        self.connect_events()
        self.init_parameters(self.paramSet)

    def connect_events(self):
        self.x_up.clicked.connect(partial(self.stage_move, 'X', 1))
        self.x_down.clicked.connect(partial(self.stage_move, 'X', -1))
        self.y_up.clicked.connect(partial(self.stage_move, 'Y', 1))
        self.y_down.clicked.connect(partial(self.stage_move, 'Y', -1))
        self.z_up.clicked.connect(partial(self.stage_move, 'Z', 1))
        self.z_down.clicked.connect(partial(self.stage_move, 'Z', -1))
        self.stop_move.clicked.connect(self.stage_stop)

        self.acquire_btn.clicked.connect(self.acquire)
        self.spectrumAcquired.connect(self.show_spectrum)

        self.step_val.currentTextChanged.connect(self.stepinfo_change)

        # Monochromator Actions
        self.WLStart.editingFinished.connect(self.WL_start_change)
        self.WLEnd_dec.clicked.connect(self.WL_end_dec)
        self.WLEnd_inc.clicked.connect(self.WL_end_inc)
        self.monoSetPos.clicked.connect(self.mono_centralWL_set)
        self.monoGridSelect.currentIndexChanged.connect(self.mono_grid_select)
        self.monoStartup.connect(self.startup)

        # Spectrum Actions
        self.vLine.sigPositionChanged.connect(self.ccd_vline_pos)
        self.hLine.sigPositionChanged.connect(self.ccd_hline_pos)
        self.frameColSelect.valueChanged.connect(self.ccd_col_select)
        self.frameRowSelect.valueChanged.connect(self.ccd_row_select)

        self.spectrum.scene().sigMouseMoved.connect(self.spectrum_cursor_pos)
        # mf.spectrum.scene().sigMouseClicked.connect(self.spectrum_mouse_click)

        self.rowBinning.valueChanged.connect(self.ccd_row_binning)
        self.avgBinning.toggled.connect(self.ccd_binning_avg)

        self.XUnits.buttonClicked.connect(self.x_units_change)
        self.YUnits.buttonClicked.connect(self.y_units_change)

        # Andor actions
        self.exposureTime.editingFinished.connect(self.exposure_change)
        self.acquisitionMode.currentIndexChanged.connect(self.acq_mode_change)
        self.triggeringMode.currentIndexChanged.connect(self.trig_mode_change)
        self.readoutMode.currentIndexChanged.connect(self.read_mode_change)
        self.accumulationFrames.editingFinished.connect(self.accum_frames_change)
        self.accumulationCycle.editingFinished.connect(self.accum_cycle_change)
        self.kineticSeries.editingFinished.connect(self.knt_series_change)
        self.kineticCycle.editingFinished.connect(self.knt_cycle_change)
        self.readoutRate.currentIndexChanged.connect(self.adc_rate_change)
        self.preAmpGain.currentIndexChanged.connect(self.gain_change)
        self.VSSpeed.currentIndexChanged.connect(self.shift_speed_change)
        self.VSAVoltage.currentIndexChanged.connect(self.shift_speed_change)
        self.tSet.clicked.connect(self.show_tsettings)

        self.statusDataUpdated.connect(self.update_satatus_data)

    def ccd_vline_pos(self, e):
        column = ceil(e.getXPos())
        self.paramSet['frameSet']['column'] = column
        self.upd_frame_section(column - 1)
        self.frameColSelect.setValue(column)

    def ccd_hline_pos(self, e):
        row = ceil(e.getYPos())
        self.paramSet['frameSet']['row'] = row
        self.upd_spectrum(row - 1)
        self.frameRowSelect.setValue(row)

    def ccd_col_select(self, val):
        self.paramSet['frameSet']['column'] = val
        self.upd_frame_section(val - 1)
        self.vLine.setPos([val, 0])

    def ccd_row_select(self, val):
        self.paramSet['frameSet']['row'] = val
        self.upd_spectrum(val)
        self.hLine.setPos([0, val])

    def spectrum_cursor_pos(self, e):
        # pos = (e.x(), e.y())
        pos = e
        if self.spectrum.sceneBoundingRect().contains(pos):
            mouse_point = self.spectrum.plotItem.vb.mapSceneToView(pos)
            self.cursorPosLbl.setText("X = %0.1f, Y = %0.1f"
                                               % (mouse_point.x(), mouse_point.y()))
            self.spectrumCursor.setPos((mouse_point.x()/2.0, mouse_point.y()/2.0))

    # def spectra_mouse_click(self, e):
    #     if e.button() == Qt.RightButton:
    #         self.spectrum.autoRange()

    def ccd_row_binning(self, val):
        self.paramSet['frameSet']['binning'] = val
        self.upd_spectrum()

    def ccd_binning_avg(self, is_checked):
        self.paramSet['frameSet']['binningAvg'] = is_checked
        self.upd_spectrum()

    def x_units_change(self):
        units_id = self.XUnits.checkedId()
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

            self.spectrum.plotItem.setLabels(bottom='Wavelength (nm)')

        elif units_id == 1:
            # eV
            for i, p in enumerate(self.mono_positions):
                offset_idx = i*strip_size
                for n in range(strip_size):
                    self.coordinates[offset_idx + n] = 1239.84193 / self.hardware.mono_toWL(p, n)
            for n in range(strip_size, self.ccdWidth):
                self.coordinates[offset_idx + n] = 1239.84193 / self.hardware.mono_toWL(p, n)

            self.spectrum.plotItem.setLabels(bottom='Energy (eV)')

        else:
            # pixel number
            self.coordinates = np.arange(self.spWidth, dtype=np.float)
            self.spectrum.plotItem.setLabels(bottom='Pixel number')

        self.upd_spectrum()

        spectrum_vb = self.spectrum.vb
        if self.coordinates[0] < self.coordinates[self.spWidth-1]:
            spectrum_vb.setXRange(self.coordinates[0], self.coordinates[self.spWidth-1], padding=0.02)
            # spectrum_vb.setLimits(xMin=self.coordinates[0], xMax=self.coordinates[self.spWidth-1])
        else:
            spectrum_vb.setXRange(self.coordinates[self.spWidth-1], self.coordinates[0], padding=0.02)
            # spectrum_vb.setLimits(xMin=self.coordinates[self.spWidth-1], xMax=self.coordinates[0])

    def y_units_change(self):
        units_id = self.YUnits.checkedId()
        self.paramSet['frameSet']['y-axis'] = units_id

        if units_id == 1:
            self.n_factor = 1 / self.paramSet['Andor']['exposure']
        else:
            self.n_factor = 1

        self.upd_spectrum()

    def upd_spectrum(self, row=-1):
        if row == -1:
            row = self.paramSet['frameSet']['row'] - 1

        bin_rows = self.paramSet['frameSet']['binning']

        if bin_rows > 1:
            min_row = ceil(row - bin_rows / 2)
            max_row = ceil(row + bin_rows / 2)

            if self.paramSet['frameSet']['binningAvg']:
                self.spectrum.curve.setData(
                    x=self.coordinates,
                    y=np.average(self.spData[min_row:max_row, :], axis=0) * self.n_factor
                )
            else:
                self.spectrum.curve.setData(
                    x=self.coordinates,
                    y=np.sum(self.spData[min_row:max_row, :], axis=0) * self.n_factor
                )
        else:
            self.spectrum.curve.setData(
                x=self.coordinates,
                y=self.spData[row, :] * self.n_factor
            )

    def upd_frame_section(self, column=-1):
        if column == -1:
            column = self.frameColSelect.value() - 1

        self.frameSection.curve.setData(x=self.spData[:, column], y=np.arange(self.ccdHeight))

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

        self.spectrumCmp.set_frame_size(self.spData, self.ccdWidth, self.spectraOverlap)
        self.coordinates = np.arange(self.spWidth, dtype=np.float)
        self.x_units_change()

        # updating all widget sizes
        self.CCDFrame.vb.setLimits(xMin=0, xMax=self.spWidth-1, yMin=0, yMax=self.ccdHeight-1)
        self.vLine.setBounds((0.5, self.spWidth-0.5))
        self.frameColSelect.setRange(1, self.spWidth)

    def WL_start_change(self):
        WL_start = self.WLStart.value()
        self.paramSet['MDR-3']['WL-start'] = WL_start

        # updating monochromator positions
        self.mono_positions[0] = self.hardware.mono_toSteps(WL_start)
        if self.paramSet['MDR-3']['WL-inc'] > 1:
            for i in range(1, self.paramSet['MDR-3']['WL-inc']):
                WL_next = self.hardware.mono_toWL(self.mono_positions[i-1], self.ccdWidth - self.spectraOverlap)
                steps_next = self.hardware.mono_toSteps(WL_next)
                self.mono_positions[i] = steps_next
        WL_end = self.hardware.mono_toWL(self.mono_positions[-1], self.ccdWidth)
        self.WLEnd.setText("{0:.2f}".format(WL_end))

        self.resize_spectrum(self.paramSet['MDR-3']['WL-inc'], False)
        self.spectrumCmp.set_range_points(self.mono_positions)

    def WL_end_inc(self):
        WL_inc = self.hardware.mono_toWL(self.mono_positions[-1], self.ccdWidth - self.spectraOverlap)
        steps_inc = self.hardware.mono_toSteps(WL_inc)
        self.mono_positions.append(steps_inc)
        self.paramSet['MDR-3']['WL-inc'] += 1

        WL_end = self.hardware.mono_toWL(steps_inc, self.ccdWidth)
        self.WLEnd.setText("{0:.2f}".format(WL_end))

        self.resize_spectrum(self.paramSet['MDR-3']['WL-inc'], True)
        self.spectrumCmp.set_range_points(self.mono_positions)

    def WL_end_dec(self):
        if self.paramSet['MDR-3']['WL-inc'] > 1:
            self.mono_positions.pop()
            self.paramSet['MDR-3']['WL-inc'] -= 1

            WL_end = self.hardware.mono_toWL(self.mono_positions[-1], self.ccdWidth)
            self.WLEnd.setText("{0:.2f}".format(WL_end))

            self.resize_spectrum(self.paramSet['MDR-3']['WL-inc'], True)
            self.spectrumCmp.set_range_points(self.mono_positions)

    def mono_centralWL_set(self):
        # Position (in steps) is calculated according to the first pixel, WL - to the center pixel
        WL_set = self.monoGridPos.value()
        pos_cp = self.hardware.mono_toSteps(WL_set)
        WL_fp = WL_set - (self.hardware.mono_toWLC(pos_cp) - WL_set)
        pos_set = self.hardware.mono_toSteps(WL_fp)
        ret = self.hardware.mono_goto(pos_set)
        if ret == 'OK':
            self.thread_pool.start(self.monoChkState)

    def startup(self):
        self.WL_start_change()
        self.resize_spectrum(self.paramSet['MDR-3']['WL-inc'])

        # Check current monochromator position
        current_pos = self.hardware.mono_pos()
        if current_pos is not False:
            current_WL = self.hardware.mono_toWLC(current_pos)
            self.paramSet['MDR-3']['WL-pos'] = current_WL
            self.monoCurrentPos.setText("{0:.2f}".format(current_WL) + ' nm')
        else:
            self.monoCurrentPos.setText(" -- ")
            self.statusBar.showMessage('Monochromator position error...')

    def mono_calibration(self):
        ans = self.hardware.mono_move_start()
        if ans == 'OK':
            self.thread_pool.start(self.monoChkState)
        elif ans == 'BUSY':
            self.statusBar.showMessage('Monochromator is busy. Please try again later.')
        else:
            self.statusBar.showMessage('Monochromator connection error...')

    def mono_grid_select(self, grid_idx):
        self.paramSet['MDR-3']['grating-select'] = grid_idx

    def exposure_change(self):
        exp_time = self.exposureTime.value()
        self.paramSet['Andor']['exposure'] = exp_time
        self.ccd.set_exposure(exp_time)

    def acq_mode_change(self, mode):
        self.paramSet['Andor']['AcqMode']['mode'] = mode
        self.mode_prm_enable(mode)
        self.ccd.set_acq_mode(self.paramSet['Andor']['AcqMode'])

    def trig_mode_change(self, mode):
        self.paramSet['Andor']['trigMode'] = mode
        self.ccd.set_trig_mode(mode)

    def read_mode_change(self, mode):
        self.paramSet['Andor']['readMode'] = mode
        self.ccd.set_read_mode(mode)

    def accum_frames_change(self):
        n = self.accumulationFrames.value()
        self.paramSet['Andor']['AcqMode']['accumFrames'] = n
        self.ccd.set_acq_mode(self.paramSet['Andor']['AcqMode'])

    def accum_cycle_change(self):
        cycle_time = self.accumulationCycle.value()
        self.paramSet['Andor']['AcqMode']['accumCycle'] = cycle_time
        self.ccd.set_acq_mode(self.paramSet['Andor']['AcqMode'])

    def knt_series_change(self):
        n = self.kineticSeries.value()
        self.paramSet['Andor']['AcqMode']['kSeries'] = n
        self.ccd.set_acq_mode(self.paramSet['Andor']['AcqMode'])

    def knt_cycle_change(self):
        cycle_time = self.kineticCycle.value()
        self.paramSet['Andor']['AcqMode']['kCycle'] = cycle_time
        self.ccd.set_acq_mode(self.paramSet['Andor']['AcqMode'])

    def adc_rate_change(self, rate_idx):
        self.paramSet['Andor']['ADCRate'] = rate_idx
        self.ccd.set_adc_rate(rate_idx)

    def gain_change(self, gain_idx):
        self.paramSet['Andor']['gain'] = gain_idx
        self.ccd.set_preamp(gain_idx)

    def shift_speed_change(self, speed_idx):
        self.paramSet['Andor']['VSSpeed'] = speed_idx
        self.ccd.set_shift_speed(speed_idx)

    def vsa_volt_change(self, vsa_idx):
        self.paramSet['Andor']['VSAVoltage'] = vsa_idx
        self.ccd.set_vsa_volt(vsa_idx)

    def show_tsettings(self):
        if self.tSettings.isVisible():
            self.tSettings.activateWindow()
        else:
            self.tSettings.open()

    def stepinfo_change(self, val):
        steps = int(val)
        self.paramSet['stagePos']['step'] = steps

        dst = "{0:.2f}".format(self.hardware.minStageStep * steps)
        self.distance_lbl.setText('Distance: ' + dst + 'um')

    def stage_move(self, axis, direction, checked=False):
        steps = int(self.step_val.currentText()) * direction

        self.hardware.stage_move(axis, steps)
        new_pos = int(self.x_pos.text()) + steps
        self.paramSet['stagePos'][axis] = new_pos

        if axis == 'X':
            self.x_pos.setText(str(new_pos))
        elif axis == 'Y':
            self.y_pos.setText(str(new_pos))
        elif axis == 'Z':
            self.z_pos.setText(str(new_pos))

    def stage_stop(self):
        for axis in ('X', 'Y', 'Z'):
            self.hardware.stage_stop(axis)

        for axis in ('X', 'Y', 'Z'):
            pos = self.hardware.get_stage_position(axis)
            self.paramSet['stagePos'][axis] = pos
            self.x_pos.setText(str(pos))

    def show_spectrum(self):
        self.CCDFrame.image.setImage(self.spData)
        self.upd_spectrum()
        self.upd_frame_section()

    def acquire(self):
        self.thread_pool.start(self.spectrumCmp)

    def update_satatus_data(self, statuses):
        # CCD cooling status
        if statuses['ccd_cooling'] in ['not_reached', 'not_stabilized']:
            self.tCurrent.setStyleSheet("color: red")
        elif statuses['ccd_cooling'] == 'stabilized':
            self.tCurrent.setStyleSheet("color: green")
        elif statuses['ccd_cooling'] == 'drifted':
            self.tCurrent.setStyleSheet("color: yellow")
        else:
            self.tCurrent.setStyleSheet("color: grey")

        # Current temperature
        self.tSettings.tCurrent.setText(str(statuses['ccd_temperature']))
        self.tCurrent.setText(str(statuses['ccd_temperature']))

    def tSafe_stabilization(self, progress):
        t_target = -10
        t = self.ccd.get_temperature()
        self.ccd.set_temperature(t_target)
        t_prev = t

        while self.ccd.temperature_status() != 'stabilized':
            loop = QEventLoop()
            QTimer.singleShot(500, loop.quit)
            loop.exec_()

            t_current = self.ccd.get_temperature()
            if (t_current > t_prev) and (t_current < t_target):
                progress.setValue(int(100 * (1 - (t_target - t_current) / (t_target - t))))
                t_prev = t_current

        progress.setValue(100)
        return True

    def stop_threads(self):
        self.spectrumCmp.stop()
        self.monoChkState.stop()

        if self.ccd.get_temperature() < -10:
            self.camShutdownProgress.setWindowModality(Qt.WindowModal)
            self.camShutdownProgress.show()
            self.camShutdownProgress.setValue(0)

            self.tSafe_stabilization(self.camShutdownProgress)
            self.camShutdownProgress.setValue(100)
            self.camShutdownProgress.close()

        self.ccd.set_cooler(False)

        self.statusUpdateThread.stop()

        if self.tSettings.isVisible():
            self.tSettings.close()


class StatusUpdate (QThread):

    stop_event = Event()

    statuses = {'ccd_temperature': 0, 'ccd_cooling': 'off'}

    def __init__(self, sp_module):
        super().__init__()
        self.spModule = sp_module

    def stop(self):
        if not self.stop_event.is_set():
            self.stop_event.set()

    def run(self):
        while not self.stop_event.is_set():
            # CCD cooling
            if self.spModule.ccd.connStatus:
                self.statuses['ccd_temperature'] = round(self.spModule.ccd.get_temperature(), 1)
                self.statuses['ccd_cooling'] = self.spModule.ccd.temperature_status()

                self.spModule.statusDataUpdated.emit(self.statuses)

            time.sleep(0.5)


class MonoChkState(QRunnable):

    stop_event = Event()

    def __init__(self, spectra_module):
        super().__init__()

        self.spModule = spectra_module

    def stop(self):
        if not self.stop_event.is_set():
            self.stop_event.set()

    def run(self):
        while not self.stop_event.is_set():
            time.sleep(0.5)
            self.spModule.mutex.lock()
            current_pos = self.spModule.hardware.mono_pos()
            if current_pos is not False:
                current_WL = self.spModule.hardware.mono_toWLC(current_pos)
                self.spModule.paramSet['MDR-3']['WL-pos'] = current_WL
                self.spModule.mainform.monoCurrentPos.setText("{0:.2f}".format(current_WL) + ' nm')
            else:
                self.spModule.mainform.monoCurrentPos.setText(" -- ")

            status = self.spModule.hardware.mono_status()
            self.spModule.mutex.unlock()
            if status == 'OK':
                break
            elif status == 'ERROR':
                self.spModule.mainform.statusBar.showMessage('Monochromator position check error...')
                break

        return


class SpectrumCompilation(QRunnable):

    frame_parsed = Event()
    stop_event = Event()

    mono_positions = []

    dataArray = []
    sp_size = 1024
    sp_overlap = 80

    frame_index = 0

    def __init__(self, spectra_module):
        super().__init__()

        self.spModule = spectra_module

        self.spModule.ccd.frameAcquired.connect(self.framedata_handler)

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
            for pos in self.mono_positions:
                # self.spModule.mutex.lock()
                # self.spModule.hardware.mono_goto(pos)
                # self.spModule.thread_pool.start(self.spModule.monoChkState)
                # self.spModule.mutex.unlock()
                #
                # while True:
                #     self.spModule.mutex.lock()
                #     status = self.spModule.hardware.mono_status()
                #     self.spModule.mutex.unlock()
                #     if status == 'OK':
                #         break
                #
                #     time.sleep(0.5)

                self.spModule.ccd.frame()
                self.frame_parsed.wait()
                self.frame_parsed.clear()

            self.frame_index = 0

            self.spModule.spectrumAcquired.emit()

            return

        return
