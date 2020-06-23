import time
from thorpy.comm.discovery import discover_stages
from thorpy.message.motorcontrol import *


class HardWare(object):

    MOT_X = 0
    MOT_Y = 1
    MOT_Z = 2
    MOT_UP = 1
    MOT_DOWN = -1

    mot = {}

    def __init__(self, p):
        self.paramSet = p

        stages = list(discover_stages())
        for s in stages:
            if s._port.serial_number == self.paramSet["Thorlabs"]["stageX"]:
                self.mot.update({'X': s})
            elif s._port.serial_number == self.paramSet["Thorlabs"]["stageY"]:
                self.mot.update({'Y': s})
            elif s._port.serial_number == self.paramSet["Thorlabs"]["stageZ"]:
                self.mot.update({'Z': s})

        self.minStageStep = self.paramSet["Thorlabs"]["stageStep"]

    def stage_pos(self, axis='X', force=False):
        s = self.mot[axis]
        if force:
            return s.position()
        else:
            while s.status_in_motion_forward or s.status_in_motion_reverse or s.status_in_motion_jogging_forward or s.status_in_motion_jogging_reverse or s.status_in_motion_homing:
                time.sleep(1)
            return s.position()

    def stage_move(self, axis='X', dst=0):
        self.mot[axis]._port.send_message(
            MGMSG_MOT_MOVE_RELATIVE_long(chan_ident=self.mot[axis]._chan_ident, relative_distance=dst))

    def stage_goto(self, axis='X', pos=0):
        self.mot[axis]._port.send_message(
            MGMSG_MOT_MOVE_ABSOLUTE_long(chan_ident=self.mot[axis]._chan_ident, absolute_distance=pos))

    def stage_stop(self, axis='X'):
        self.mot[axis]._port.send_message(
            MGMSG_MOT_MOVE_STOP(chan_ident=self.mot[axis]._chan_ident, stop_mode=0x02))
