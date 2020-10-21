from functools import partial
import threading
import time


class ScanModuleActions(object):

    _scanThread = False

    def __init__(self, ui, p_set, hardware, ccd):

        self.ui = ui
        self.paramSet = p_set
        self.hardware = hardware
        self.ccd = ccd

        self.connect_events()

    def connect_events(self):

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

    def stop_threads(self):
        self._scanThread = False

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