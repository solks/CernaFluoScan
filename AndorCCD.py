from pyAndor.Camera.andor import *
import signal
import numpy as np
import matplotlib.image as mpimg


class AndorCCD(object):

    def __init__(self):
        self.tset = -20
        self.EMCCDGain = 0
        self.preAmpGain = 0

        self.cam = Andor()
        self.cam.SetSingleScan()
        self.cam.SetTriggerMode(7)
        self.cam.SetShutter(1, 1, 0, 0)
        self.cam.SetPreAmpGain(self.preAmpGain)
        self.cam.SetEMCCDGain(self.EMCCDGain)
        self.cam.SetExposureTime(0.01)
        self.cam.SetCoolerMode(1)

        self.set_temperature(self.tset)
        self.cam.CoolerON()

        self.ccdData = np.zeros((1024, 255), dtype=np.uint8)

    def frame(self):
        # self.ccdData = mpimg.imread('ccd-frame2_bw.png')
        # self.ccdData = self.ccdData * 255
        # self.ccdData = self.ccdData.astype(np.uint8)

        self.cam.StartAcquisition()
        self.cam.GetAcquiredData(self.ccdData)
        return self.ccdData

    def get_data(self):
        return self.ccdData

    def set_exposure(self, exp_time):
        self.cam.SetExposureTime(exp_time)
        return True

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

    def shut_down(self):
        self.cam.ShutDown()
