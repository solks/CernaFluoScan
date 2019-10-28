from functools import partial
from math import ceil

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
        self.wavelength = np.arange(1024)
        self.rows = np.arange(255)
        self.framedata = np.zeros((255, 1024), dtype=np.uint16)
        # self.framedata = np.random.randint(0, 50, (255, 1024), dtype=np.uint16)

        self.mainform = w

        self.connect_events()

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

        self.mainform.vLine.sigPositionChanged.connect(self.ccd_cursor_col)
        self.mainform.hLine.sigPositionChanged.connect(self.ccd_cursor_row)
        self.mainform.CCDRow.scene().sigMouseMoved.connect(self.spectra_cursor_pos)
        # self.mainform.CCDRow.scene().sigMouseClicked.connect(self.spectra_mouse_click)

    def ccd_cursor_col(self, e):
        col = ceil(e.getXPos())
        self.upd_col_graph(col-1)

    def ccd_cursor_row(self, e):
        row = ceil(e.getYPos())
        self.upd_row_graph(row-1)

    def spectra_cursor_pos(self, e):
        # pos = (e.x(), e.y())
        pos = e
        if self.mainform.CCDRow.sceneBoundingRect().contains(pos):
            mouse_point = self.mainform.CCDRow.plotItem.vb.mapSceneToView(pos)
            self.mainform.cursorPosLbl.setText("X = %0.1f, Y = %0.1f"
                                               % (mouse_point.x(), mouse_point.y()))
            self.mainform.rowGraphCursor.setPos((mouse_point.x()/2.0, mouse_point.y()/2.0))

    # def spectra_mouse_click(self, e):
    #     if e.button() == Qt.RightButton:
    #         self.mainform.CCDRow.autoRange()

    def upd_row_graph(self, row):
        self.mainform.rowCurve.setData(x=self.wavelength, y=self.framedata[row, :])

    def upd_col_graph(self, col):
        self.mainform.colCurve.setData(x=self.framedata[:, col], y=self.rows)

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
        elif stage_id == self.MOT_Y:
            self.hardware.move_y(steps)
        elif stage_id == self.MOT_Z:
            self.hardware.move_z(steps)

    def get_frame(self):
        # self.framedata = self.ccd.get_data()
        # self.framedata = np.random.randint(0, 150, (255, 1024), dtype=np.uint16)

        data = mpimg.imread('ccd-frame2_bw.png') * 65536
        self.framedata = np.dot(data[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint16)

        # gray_color_table = [qRgb(i, i, i) for i in range(256)]

    def acquire(self):
        self.get_frame()
        self.mainform.CCDFrame.getImageItem().setImage(self.framedata)


    def shut_down(self):
        print('Shutting down the camera...')
        self.ccd.shut_down()
