import time
import re
import serial
import serial.tools.list_ports
import math
from thorpy.comm.discovery import discover_stages
from thorpy.message.motorcontrol import *


class HardWare(object):

    mot = {}

    mono = None
    monoStatus = False

    gratingIndex = 1

    def __init__(self, p):
        self.conf = p

        # stages = list(discover_stages())
        # for s in stages:
        #     if s._port.serial_number == self.conf["Thorlabs"]["stageX"]:
        #         self.mot.update({'X': s})
        #     elif s._port.serial_number == self.conf["Thorlabs"]["stageY"]:
        #         self.mot.update({'Y': s})
        #     elif s._port.serial_number == self.conf["Thorlabs"]["stageZ"]:
        #         self.mot.update({'Z': s})

        self.minStageStep = self.conf["Thorlabs"]["stageStep"]

        self.monoStatus, self.mono = self.mono_connect()

    def mono_connect(self):
        connected = False
        dev = None

        ports = serial.tools.list_ports.comports()
        for p in ports:
            if re.search(r'Serial', p.description):
                # print(p.description)
                try:
                    dev = serial.Serial(p.name, 9600, timeout=1)
                    time.sleep(1)

                    msg = b"DM\n"
                    dev.write(msg)
                    while dev.out_waiting() > 0:
                        time.sleep(0.1)

                    ans = dev.read(1)
                    while dev.inWaiting() > 0:
                        ans += dev.read(1)

                    if re.search(r'Monochromator controller', ans.decode("utf-8")):
                        connected = True
                        break
                    else:
                        dev.close()
                except serial.serialutil.SerialException:
                    pass

        return connected, dev

    def mono_toSteps(self, WL0):
        c = self.conf['MDR']['c']
        k = self.conf['MDR']['k']
        alpha_0 = self.conf['MDR']['alpha_0']

        steps = int((math.asin(WL0 / c) - alpha_0) / k)

        return steps

    def mono_toWL0(self, steps):
        c = self.conf['MDR']['c']
        k = self.conf['MDR']['k']
        alpha_0 = self.conf['MDR']['alpha_0']

        WL0 = math.sin(steps * k + alpha_0) * c
        return WL0

    def mono_toWL(self, steps, n):
        c = self.conf['MDR']['c']
        k = self.conf['MDR']['k']
        alpha_0 = self.conf['MDR']['alpha_0']
        phi_0 = self.conf['MDR']['phi_0']
        delta = self.conf['MDR']['DELTA']
        f = self.conf['MDR']['f']
        d = 1 / self.conf['MDR']['grating'][str(self.gratingIndex)]

        WL0 = math.sin(steps * k + alpha_0) * c
        WL = WL0 + 1E6 * d * n * delta * math.cos(phi_0 - steps * k + n * delta / f) / f

        return WL

    def mono_pos(self):
        if self.monoStatus:
            msg = b"GP\n"

            self.mono.write(msg)
            while self.mono.out_waiting() > 0:
                time.sleep(0.1)

            ans = self.mono.read(1)
            while self.mono.in_waiting() > 0:
                ans += self.mono.read(1)

            ans_str = ans.decode("utf-8")
            if ans_str != 'ERROR' and not re.search(r'[^0-9]+?]', ans_str):
                steps = int(ans_str)
                return steps
            else:
                return False
        else:
            return False

    def mono_status(self):
        if self.monoStatus:
            msg = b"GS\n"

            self.mono.write(msg)
            while self.mono.out_waiting() > 0:
                time.sleep(0.1)

            ans = self.mono.read(1)
            while self.mono.in_waiting() > 0:
                ans += self.mono.read(1)

            return ans.decode("utf-8")
        else:
            return False

    def mono_goto(self, pos):
        if self.monoStatus:
            msg = b"GA" + bytes(round(abs(pos))) + b"\n"

            self.mono.write(msg)
            while self.mono.out_waiting() > 0:
                time.sleep(0.1)

            ans = self.mono.read(1)
            while self.mono.in_waiting() > 0:
                ans += self.mono.read(1)

            return ans.decode("utf-8")
        else:
            return False

    def mono_move(self, dst):
        if self.monoStatus:
            if dst >= 0:
                msg = b"G+" + bytes(round(dst)) + b"\n"
            else:
                msg = b"G-" + bytes(round(abs(dst))) + b"\n"

            self.mono.write(msg)
            while self.mono.out_waiting() > 0:
                time.sleep(0.1)

            ans = self.mono.read(1)
            while self.mono.in_waiting() > 0:
                ans += self.mono.read(1)

            return ans.decode("utf-8")
        else:
            return False

    def mono_move_start(self):
        if self.monoStatus:
            msg = b"G0\n"
            self.mono.write(msg)
            while self.mono.out_waiting() > 0:
                time.sleep(0.1)

            ans = self.mono.read(1)
            while self.mono.in_waiting() > 0:
                ans += self.mono.read(1)

            return ans.decode("utf-8")
        else:
            return False

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
