from functools import partial

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

        self.mainform.step_val.activated.connect(self.stepinfo_change)

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
        framedata = self.ccd.get_data()
        # gray_color_table = [qRgb(i, i, i) for i in range(256)]
        # qim = QImage(framedata, framedata.shape[1], framedata.shape[0], framedata.strides[0], QImage.Format_RGB888)
        # qim.setColorTable(gray_color_table)

    def shut_down(self):
        print('Shutting down the camera...')
        self.ccd.shut_down()
