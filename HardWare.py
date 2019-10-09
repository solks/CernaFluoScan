from thorpy.comm.discovery import discover_stages
from thorpy.message import *


class HardWare(object):

    STAGE_STEP_DST = 0.05  # in um

    def __init__(self):
        stages = list(discover_stages())
        # self.motX = stages[0]
        for s in stages:
            if s._port._serial_number == 27504545:
                self.motX = s
            elif s._port._serial_number == 27504531:
                self.motY = s
            elif s._port._serial_number == 27504608:
                self.motZ = s

    def move_x(self, dst):
        try:
            self.motX._port.send_message(
                MGMSG_MOT_MOVE_RELATIVE_long(chan_ident=self.motX._chan_ident, relative_distance=dst))
        except Exception:
            pass

    def move_y(self, dst):
        try:
            self.motY._port.send_message(
                MGMSG_MOT_MOVE_RELATIVE_long(chan_ident=self.motY._chan_ident, relative_distance=dst))
        except Exception:
            pass

    def move_z(self, dst):
        try:
            self.motZ._port.send_message(
                MGMSG_MOT_MOVE_RELATIVE_long(chan_ident=self.motZ._chan_ident, relative_distance=dst))
        except Exception:
            pass
