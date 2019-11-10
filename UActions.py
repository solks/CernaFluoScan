from functools import partial
from math import ceil
import json

import numpy as np
import matplotlib.image as mpimg

from PyQt5.QtCore import Qt

from HardWare import *
from AndorCCD import *


class UActions(object):

    MOT_X = 0
    MOT_Y = 1
    MOT_Z = 2

    MOT_UP = 1
    MOT_DOWN = -1

    def __init__(self, w):
        self.hardware = HardWare()
        #self.ccd = AndorCCD()

        self.columns = np.arange(1024)
        self.rows = np.arange(255)

        # frame data array and coordinates, default coordinates as pixel number
        self.framedata = np.zeros((255, 1024), dtype=np.uint16)
        self.coordinates = self.columns.astype(dtype=np.float)

        # self.framedata = np.random.randint(0, 50, (255, 1024), dtype=np.uint16)

        self.mainform = w

        self.paramSet = []
        self.storeParameters = True
        self.init_parameters()

        self.connect_events()

    def init_parameters(self):
        if self.storeParameters:
            # read parameters from json
            with open('current-params.json', 'r') as f:
                self.paramSet = json.load(f)

        else:
            # default
            with open('default-params.json', 'r') as f:
                self.paramSet = json.load(f)

        # Frame parameter set
        self.mainform.frameRowSelect.setValue(self.paramSet['frameSet']['row'])
        self.mainform.frameColSelect.setValue(self.paramSet['frameSet']['column'])
        self.mainform.vLine.setPos(self.paramSet['frameSet']['row'])
        self.mainform.hLine.setPos(self.paramSet['frameSet']['column'])

        self.mainform.rowBinning.setValue(self.paramSet['frameSet']['binning'])
        if self.paramSet['frameSet']['binningAvg']:
            self.mainform.avgBinning.setChecked(True)

        self.mainform.XUnits.button(self.paramSet['frameSet']['x-axis']).setChecked(True)
        self.x_units_changed(self.mainform.XUnits.button(self.paramSet['frameSet']['x-axis']))

        self.mainform.YUnits.button(self.paramSet['frameSet']['y-axis']).setChecked(True)
        self.y_units_changed(self.mainform.YUnits.button(self.paramSet['frameSet']['y-axis']))

        # Hardware parameter set
        self.mainform.x_pos.setText(str(self.paramSet['stagePos']['x']))
        self.mainform.y_pos.setText(str(self.paramSet['stagePos']['y']))
        self.mainform.z_pos.setText(str(self.paramSet['stagePos']['z']))

        # Andor parameter set
        self.mainform.exposureTime.setCurrentIndex(self.paramSet['Andor']['exposure'])
        self.mainform.framesPerImage.setCurrentIndex(self.paramSet['Andor']['FPI'])
        self.mainform.kineticLength.setCurrentIndex(self.paramSet['Andor']['kLength'])
        self.mainform.kineticTime.setCurrentIndex(self.paramSet['Andor']['kTime'])
        self.mainform.acquisitionMode.setCurrentIndex(self.paramSet['Andor']['acqMode'])
        self.mainform.triggeringMode.setCurrentIndex(self.paramSet['Andor']['trigMode'])
        self.mainform.readoutMode.setCurrentIndex(self.paramSet['Andor']['readMode'])
        self.mainform.vShiftSpeed.setCurrentIndex(self.paramSet['Andor']['vSpeed'])
        self.mainform.vClkVoltage.setCurrentIndex(self.paramSet['Andor']['clkVoltage'])
        self.mainform.readoutRate.setCurrentIndex(self.paramSet['Andor']['ADCRate'])
        self.mainform.preAmpGain.setCurrentIndex(self.paramSet['Andor']['gain'])

    def connect_events(self):
        self.mainform.x_up.clicked.connect(partial(self.stage_move, self.MOT_X, self.MOT_UP))
        self.mainform.x_down.clicked.connect(partial(self.stage_move, self.MOT_X, self.MOT_DOWN))
        self.mainform.y_up.clicked.connect(partial(self.stage_move, self.MOT_Y, self.MOT_UP))
        self.mainform.y_down.clicked.connect(partial(self.stage_move, self.MOT_Y, self.MOT_DOWN))
        self.mainform.z_up.clicked.connect(partial(self.stage_move, self.MOT_Z, self.MOT_UP))
        self.mainform.z_down.clicked.connect(partial(self.stage_move, self.MOT_Z, self.MOT_DOWN))
        # self.widget.stop_move.clicked.connect(self.hardware.mot_stop)

        self.mainform.acquire_btn.clicked.connect(self.acquire)

        self.mainform.step_val.activated.connect(self.stepinfo_change)

        self.mainform.vLine.sigPositionChanged.connect(self.ccd_vline_pos)
        self.mainform.hLine.sigPositionChanged.connect(self.ccd_hline_pos)
        self.mainform.frameColSelect.valueChanged.connect(self.ccd_col_select)
        self.mainform.frameRowSelect.valueChanged.connect(self.ccd_row_select)

        self.mainform.spectrum.scene().sigMouseMoved.connect(self.spectrum_cursor_pos)
        # self.mainform.spectrum.scene().sigMouseClicked.connect(self.spectrum_mouse_click)

        self.mainform.rowBinning.valueChanged.connect(self.ccd_row_binning)
        self.mainform.avgBinning.stateChanged.connect(self.ccd_row_binning)

        self.mainform.XUnits.buttonClicked.connect(self.x_units_changed)

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
                    y=np.average(self.framedata[min_row:max_row, :], axis=0)
                )
            else:
                self.mainform.spectrumCurve.setData(
                    x=self.coordinates,
                    y=np.sum(self.framedata[min_row:max_row, :], axis=0)
                )
        else:
            self.mainform.spectrumCurve.setData(x=self.coordinates, y=self.framedata[row, :])

    def upd_frame_section(self, column=-1):
        if column == -1:
            column = self.mainform.frameColSelect.value() - 1

        self.mainform.frameSectionCurve.setData(x=self.framedata[:, column], y=self.rows)

    def stepinfo_change(self):
        steps = int(self.mainform.step_val.currentText())
        dst = str(self.hardware.STAGE_STEP_DST * steps)
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
