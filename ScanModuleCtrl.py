from functools import partial
import threading
import time
import numpy as np

from Camera import Cam


class ScanModuleCtrl(object):

    _camThread = True

    _scanThread = False

    def __init__(self, ui, p_set, hardware, ccd):

        self.camCapture = False

        self.ui = ui
        self.paramSet = p_set
        self.hardware = hardware
        self.ccd = ccd

        self.cam = Cam()
        self.camData = np.zeros((self.cam.imageHeight, self.cam.imageWidth, self.cam.imageChannel), np.ubyte)

        if self.cam.camOpened:
            self.camCapture = True
            self.fill_cam_list(self.cam.capList)

            self.camData = self.cam.requestImage()
            self.ui.camImage.setImage(self.camData)
            self.ui.vCamFrame.getView().autoRange(padding=0)

        threading.Thread(target=self.run_camera).start()

        self.connect_events()

    def connect_events(self):
        self.ui.vcamExposure.valueChanged.connect(self.cam_exposure_change)
        self.ui.vcamGain.valueChanged.connect(self.cam_gain_change)
        self.ui.vcamFlipH.stateChanged.connect(self.cam_hflip_change)
        self.ui.vcamFlipV.stateChanged.connect(self.cam_vflip_change)

        for i, el in enumerate(self.ui.scanSetup):
            el['use'].stateChanged.connect(partial(self.scan_setup_change, idx=i, par_id=0))
            el['instrument'].currentIndexChanged.connect(partial(self.scan_setup_change, idx=i, par_id=1))
            el['count'].currentTextChanged.connect(partial(self.scan_setup_change, idx=i, par_id=2))
            el['step'].currentTextChanged.connect(partial(self.scan_setup_change, idx=i, par_id=3))

        for i, el in enumerate(self.ui.scanActions):
            el['use'].stateChanged.connect(partial(self.scan_actions_change, idx=i, par_id=0))
            el['action'].currentIndexChanged.connect(partial(self.scan_actions_change, idx=i, par_id=1))
            el['par1'].textChanged.connect(partial(self.scan_actions_change, idx=i, par_id=2))

        self.ui.scanStart.clicked.connect(self.run_scan)

    def fill_cam_list(self, device_list):
        for i, device in enumerate(device_list):
            self.ui.vcamSelect.addItem('Camera #'
                                       + str(device['name'] + 1)
                                       + ' (' + str(device['width'])
                                       + ':' + str(device['height']) + ')')

    def run_camera(self):
        while 1:
            if self.camCapture:
                self.camData = self.cam.requestImage()
                self.ui.camImage.setImage(self.camData)

            if not self._camThread:
                break

            time.sleep(0.04)

    def stop_threads(self):
        self._camThread = False
        self._scanThread = False

    def cam_exposure_change(self, exposure):
        self.paramSet['cam']['exposure'] = exposure
        self.cam.set_gain(exposure)

    def cam_gain_change(self, gain):
        self.paramSet['cam']['gain'] = gain
        self.cam.set_gain(gain)

    def cam_hflip_change(self, val):
        if val:
            self.paramSet['cam']['hFlip'] = True
            self.cam.hFlip = True
        else:
            self.paramSet['cam']['hFlip'] = False
            self.cam.hFlip = False

    def cam_vflip_change(self, val):
        if val:
            self.paramSet['cam']['vFlip'] = True
            self.cam.vFlip = True
        else:
            self.paramSet['cam']['vFlip'] = False
            self.cam.vFlip = False

    def scan_setup_change(self, val, idx=0, par_id=0):
        si = str(idx)
        if par_id == 0:
            self.paramSet['scanSet'][si]['use'] = val
        elif par_id == 1:
            self.paramSet['scanSet'][si]['id'] = val
        elif par_id == 2:
            self.paramSet['scanSet'][si]['count'] = int(val)
        elif par_id == 3:
            self.paramSet['scanSet'][si]['step'] = int(val)

    def scan_actions_change(self, val, idx=0, par_id=0):
        si = str(idx)
        if par_id == 0:
            self.paramSet['scanActions'][si]['use'] = val
        elif par_id == 1:
            self.paramSet['scanActions'][si]['id'] = val
        elif par_id == 2:
            self.paramSet['scanActions'][si]['par1'] = val

    def perform_actions(self, scan_actions):
        legend = ["X", "Y", "Z", "WL"]

        for action in scan_actions:
            if action['id'] == 1:
                print('Take frame')
    #           spectraModule.acquire()

    def dim_scan(self, scan_set, scan_actions, seq_num=0):
        legend = ["X", "Y", "Z", "WL"]

        start = 0
        stop = scan_set[seq_num]['count'] * scan_set[seq_num]['step']
        step = scan_set[seq_num]['step']
        for i in range(start, stop, step):
            print(legend[scan_set[seq_num]['id'] - 1] + ': ' + str(i))
            if seq_num < len(scan_set) - 1:
                self.dim_scan(scan_set, scan_actions, seq_num + 1)

            self.perform_actions(scan_actions)

    def run_scan(self):
        # print(self.paramSet['scanSet'])
        scan_set = []
        for i in range(len(self.paramSet['scanSet'])):
            if self.paramSet['scanSet'][str(i)]['use']:
                scan_set.insert(i, self.paramSet['scanSet'][str(i)])

        scan_actions = []
        for i in range(len(self.paramSet['scanActions'])):
            if self.paramSet['scanActions'][str(i)]['use']:
                scan_actions.insert(i, self.paramSet['scanActions'][str(i)])

        # print(scan_set)
        # for v in reversed(scan_set):
        #     print(v)

        self.dim_scan(scan_set, scan_actions)