from pylablib.devices import Andor

from threading import Event
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, QObject

import numpy as np
import cv2


class AndorCCD(QObject):
    # Values from Andor SDK documentation
    ACQ_MODE = ('single', 'accum', 'kinetic', 'fast_kinetic', 'cont')
    TRIG_MODE = ('int', 'ext', 'fast_ext', 'ext_start')
    READ_MODE = ('image', 'single_track', 'multi_track', 'fvb')

    frameAcquired = pyqtSignal(np.ndarray)

    def __init__(self, config, params):
        super().__init__()

        self.conf = config

        try:
            self.cam = Andor.AndorSDK2Camera(temperature='off')
            # print(self.cam.get_device_info())

            # self.frameProvider = FrameProvider(self.cam, self.ccdData, self.frameAcquired)
            self.frameProvider = FrameProvider(self.cam, self.frameAcquired)
            self.frameProvider.start()

            self.set_exposure(params['exposure'])
            self.cam.setup_shutter('auto')
            self.set_acq_mode(params['AcqMode'])
            self.set_trig_mode(params['trigMode'])
            self.set_read_mode(params['readMode'])
            self.set_adc_rate(params['ADCRate'])
            self.set_preamp(params['gain'])
            self.set_shift_speed(params['VSSpeed'])
            self.set_vsa_volt(params['VSAVoltage'])
        except:
            if hasattr(self, 'cam') and self.cam.is_opened():
                self.cam.close()

    def frame(self):
        self.frameProvider.acquire_frame()

    def set_temperature(self, t):
        self.cam.set_temperature(t)
        return self.cam.get_temperature_setpoint()

    def get_temperature(self):
        return self.cam.get_temperature()

    def get_temperature_range(self):
        return self.cam.get_temperature_range()

    def temperature_status(self):
        return self.cam.get_temperature_status()

    def set_cooler(self, on=True):
        self.cam.set_cooler(on)

    def set_exposure(self, exp_time):
        self.frameProvider.set_timeout(exp_time, self.cam.get_hsspeed_frequency())
        return self.cam.set_exposure(exp_time)

    def set_acq_mode(self, acqParams):
        mode = self.ACQ_MODE[acqParams['mode']]

        if mode == 'single':
            return self.cam.set_acquisition_mode(mode, setup_params=False)
        elif mode == 'accum':
            return self.cam.setup_accum_mode(mode, acqParams['accumCycle'])
        elif mode == 'kinetic':
            return self.cam.setup_kinetic_mode(acqParams['kSeries'], acqParams['kCycle'], acqParams['accumFrames'], acqParams['accumCycle'])
        elif mode == 'fast_kinetic':
            return self.cam.setup_fast_kinetic_mode(acqParams['kSeries'], acqParams['accumCycle'])
        elif mode == 'cont':
            return self.cam.setup_cont_mode(acqParams['kCycle'])

    def set_trig_mode(self, mode_idx):
        if self.TRIG_MODE[mode_idx] == 'fast_ext':
            # self.cam.lib.SetFastExtTrigger(1)
            return True
        else:
            return self.cam.set_trigger_mode(self.TRIG_MODE[mode_idx])

    def set_read_mode(self, idx):
        return self.cam.set_read_mode(self.READ_MODE[idx])

    def set_adc_rate(self, adc_rate_idx):
        self.frameProvider.set_timeout(self.cam.get_exposure(), self.cam.get_hsspeed_frequency())
        return self.cam.set_amp_mode(hsspeed=adc_rate_idx)

    def set_preamp(self, gain_idx):
        return self.cam.set_amp_mode(preamp=gain_idx)

    def set_shift_speed(self, speed_idx):
        return self.cam.set_vsspeed(speed_idx)

    def set_vsa_volt(self, vsa_idx):
        # self.cam.lib.SetVSAmplitude(vsa_idx)
        return True

    def shut_down(self):
        self.cam.close()


class FrameProvider(QThread):

    timeout = 5.0

    acquisition = Event()
    stop_event = Event()

    def __init__(self, cam, frame_acquired):
        super().__init__()

        self.cam = cam
        # self.frameData = frame_data

        self.frameAcquired = frame_acquired

    def set_timeout(self, exp_time, frequency):
        # 261120 - number of pixels
        # 0.8 sec - data transfer time
        self.timeout = exp_time + 1.2 * 261120 / frequency + 0.8

    def acquire_frame(self):
        self.acquisition.set()

    def stop(self):
        self.stop_event.set()

    def frame_template(self):
        data = cv2.imread('ccd-frame2_bw.png')

        # return data = np.random.randint(0, 150, (255, 1024), dtype=np.uint16)
        # gray_color_table = [qRgb(i, i, i) for i in range(255)

        return np.dot(data[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint16)

    def run(self):
        while not self.stop_event.is_set():
            if self.acquisition.wait(0.5):
                self.acquisition.clear()
                # frameData = self.frame_template()
                try:
                    frameData = self.cam.snap(timeout=self.timeout)
                    self.frameAcquired.emit(frameData)
                except self.cam.Error:
                    print('CCD frame acquisition error')
        return
