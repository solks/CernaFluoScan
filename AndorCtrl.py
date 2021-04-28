from pyAndor.Camera.andor import *

from threading import Event
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, QObject

import numpy as np
import cv2
# import matplotlib.image as mpimg


class AndorCCD(QObject):
    # Values from Andor SDK documentation
    ACQ_MODE = (1, 2, 3, 1, 4)
    TRIG_MODE = (0, 1, 1, 6)
    READ_MODE = (4, 3, 1, 0)

    frameAcquired = pyqtSignal(np.ndarray)

    def __init__(self, config, params):
        super().__init__()

        self.conf = config

        # self.cam = Andor()
        #
        # self.set_exposure(params['exposure'])
        # self.set_acq_mode(params['AcqMode'])
        # self.set_trig_mode(params['trigMode'])
        # self.set_read_mode(params['readMode'])
        # self.cam.SetShutter(1, 1, 0, 0)
        # self.set_adc_rate(params['ADCRate'])
        # self.set_gain(params['gain'])
        # self.set_shift_speed(params['VSSpeed'])
        # self.set_vsa_volt(params['VSAVoltage'])
        #
        # self.cam.SetCoolerMode(params['cooler'])
        # self.cam.CoolerON()
        # self.set_temperature(params['temperature'])

        self.ccdData = np.zeros((1024, 256), dtype=np.uint8)

        self.cam = None

        self.frameProvider = FrameProvider(self.cam, self.ccdData, self.frameAcquired)
        self.frameProvider.start()

    def frame(self):
        # self.cam.StartAcquisition()
        # self.cam.GetAcquiredData(self.ccdData)
        # return self.ccdData

        self.frameProvider.acquire_frame()

    def get_data(self):
        return self.ccdData

    def set_temperature(self, t):
        self.cam.SetTemperature(t)
        return True

    def get_temperature(self):
        self.cam.GetTemperature()
        return self.cam.temperature

    def temperature_status(self):
        if self.cam.GetTemperature() == 'DRV_TEMP_STABILIZED':
            return 'STABILIZED'
        else:
            return 'NOT_STABILIZED'

    def set_exposure(self, exp_time):
        self.cam.SetExposureTime(exp_time)
        return True

    def set_acq_mode(self, acqParams):
        mode = self.ACQ_MODE[acqParams['mode']]
        self.cam.SetAcquisitionMode(mode)

        if mode == 2:
            self.set_accum_frames(acqParams['accumFrames'])
        elif mode == 3:
            self.set_accum_frames(acqParams['accumFrames'])
            self.set_accum_cycle(acqParams['accumCycle'])
            self.set_knt_series(acqParams['kSeries'])
            self.set_knt_cycle(acqParams['kCycle'])
        elif mode == 4:
            self.set_accum_cycle(acqParams['accumCycle'])
            self.set_knt_series(acqParams['kSeries'])

        return True

    def set_trig_mode(self, mode_idx):
        self.cam.SetTriggerMode(self.TRIG_MODE[mode_idx])
        return True

    def set_read_mode(self, idx):
        self.cam.SetReadMode(self.READ_MODE[idx])

        # if self.READ_MODE[idx] == 4:
        #     self.cam.SetImage()
        return True

    def set_accum_frames(self, n):
        self.cam.SetNumberAccumulations(n)
        return True

    def set_accum_cycle(self, cycle_time):
        self.cam.SetAccumulationCycleTime(cycle_time)
        return True

    def set_knt_series(self, n):
        self.cam.SetNumberKinetics(n)
        return True

    def set_knt_cycle(self, cycle_time):
        self.cam.SetKineticCycleTime(cycle_time)
        return True

    def set_adc_rate(self, adc_rate_idx):
        #self.cam.SetHSSpeed(1, adc_rate_idx)
        return True

    def set_gain(self, gain_idx):
        self.cam.SetPreAmpGain(gain_idx)
        return True

    def set_shift_speed(self, speed_idx):
        self.cam.SetVSSpeed(speed_idx)
        return True

    def set_vsa_volt(self, vsa_idx):
        # self.cam.SetVSAmplitude(vsa_idx)
        return True

    def shut_down(self):
        self.cam.ShutDown()


class FrameProvider(QThread):

    acquisition = Event()
    stop_event = Event()

    def __init__(self, cam, frame_data, frame_acquired):
        super().__init__()

        self.cam = cam
        self.frameData = frame_data

        self.frameAcquired = frame_acquired

    def acquire_frame(self):
        self.acquisition.set()

    def stop(self):
        self.stop_event.set()

    def frame_template(self):
        # data = mpimg.imread('ccd-frame2_bw.png') * 65536
        data = cv2.imread('ccd-frame2_bw.png')

        # return data = np.random.randint(0, 150, (255, 1024), dtype=np.uint16)
        # gray_color_table = [qRgb(i, i, i) for i in range(256)

        return np.dot(data[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint16)

    def run(self):
        while not self.stop_event.is_set():
            if self.acquisition.wait(0.5):
                self.acquisition.clear()
                # err = self.cam.StartAcquisition()
                err = None
                if err is None:
                    # self.cam.GetAcquiredData(self.frameData)
                    self.frameData = self.frame_template()
                    self.frameAcquired.emit(self.frameData)
                else:
                    pass
        return
