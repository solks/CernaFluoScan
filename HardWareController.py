import time
import re
import serial
import serial.tools.list_ports
import math
from CubeController import *

class HardWare(object):

    mot = {}

    mono = None
    monoStatus = False

    gratingIndex = 1

    cubes = {}


    def __init__(self, config):
        self.conf = config

        '''stages = list(discover_stages())
        for s in stages:
            if s._port.serial_number == self.conf["Thorlabs"]["stageX"]:
                self.mot.update({'X': s})
            elif s._port.serial_number == self.conf["Thorlabs"]["stageY"]:
                self.mot.update({'Y': s})
            elif s._port.serial_number == self.conf["Thorlabs"]["stageZ"]:
                 self.mot.update({'Z': s})
        '''

        axes = ['X', 'Y', 'Z']

        for axis in axes:
            self.cubes[axis] = CubeController(self.conf["Thorlabs"]["stage"+axis])

        self.minStageStep = self.conf["Thorlabs"]["stageStep"]

        self.monoStatus, self.mono = self.mono_connect()

    def mono_connect(self):
        connected = False
        dev = None

        ports = serial.tools.list_ports.comports()
        for p in ports:
            if re.search(r'USB-to-Serial', p.description):
                try:
                    # print(p.description)
                    dev = serial.Serial(p.name, 9600, timeout=1)
                    time.sleep(1)

                    msg = b"DM\n"
                    # msg = b"G+500"
                    dev.write(msg)
                    while dev.out_waiting > 0:
                        time.sleep(0.1)

                    time.sleep(1)
                    ans = dev.read(1)
                    while dev.in_waiting > 0:
                        ans += dev.read(1)

                    # print(ans.decode("utf-8"))
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

    def mono_toWLC(self, steps):
        return self.mono_toWL(steps, self.conf['Andor']['CCD-w'] // 2)

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
            while self.mono.out_waiting > 0:
                time.sleep(0.1)

            time.sleep(1)
            ans = self.mono.read(1)
            while self.mono.in_waiting > 0:
                ans += self.mono.read(1)

            ans_str = ans.decode("utf-8")
            ans_str = ans_str[: -2]
            if ans_str != 'ERROR' and not re.search(r'[^0-9]+?]', ans_str):
                steps = int(ans_str)
                return steps
            else:
                return False
        else:
            return False

    def mono_status(self):
        if self.monoStatus:
            msg = b"DS\n"

            self.mono.write(msg)
            while self.mono.out_waiting > 0:
                time.sleep(0.1)

            time.sleep(1)
            ans = self.mono.read(1)
            while self.mono.in_waiting > 0:
                ans += self.mono.read(1)

            ans_str = ans.decode("utf-8")
            return ans_str[: -2]
        else:
            return False

    def mono_goto(self, pos):
        if self.monoStatus:
            msg = "GA" + str(round(abs(pos))) + "\n"

            self.mono.write(msg.encode())
            while self.mono.out_waiting > 0:
                time.sleep(0.1)

            time.sleep(1)
            ans = self.mono.read(1)
            while self.mono.in_waiting > 0:
                ans += self.mono.read(1)

            ans_str = ans.decode("utf-8")
            return ans_str[: -2]
        else:
            return False

    def mono_move(self, dst):
        if self.monoStatus:
            if dst >= 0:
                msg = "G+" + str(round(dst)) + "\n"
            else:
                msg = "G-" + str(round(abs(dst))) + "\n"

            self.mono.write(msg.encode())
            while self.mono.out_waiting > 0:
                time.sleep(0.1)

            time.sleep(1)
            ans = self.mono.read(1)
            while self.mono.in_waiting > 0:
                ans += self.mono.read(1)

            ans_str = ans.decode("utf-8")
            return ans_str[: -2]
        else:
            return False

    def mono_move_start(self):
        if self.monoStatus:
            msg = b"G0\n"
            self.mono.write(msg)
            while self.mono.out_waiting > 0:
                time.sleep(0.1)

            time.sleep(1)
            ans = self.mono.read(1)
            while self.mono.in_waiting > 0:
                ans += self.mono.read(1)

            ans_str = ans.decode("utf-8")
            return ans_str[: -2]
        else:
            return False

    def get_stage_position(self, axis='X', force=False):
        #s = self.mot[axis]
        cube = self.cubes[axis]
        if force:
            return cube.position
        else:
            while cube.is_moving:
                time.sleep(1)
            return cube.position

    def stage_move(self, axis='X', dst=0):
        self.cubes[axis].move_steps(dst)
        #self.mot[axis]._port.send_message(
        #    MGMSG_MOT_MOVE_RELATIVE_long(chan_ident=self.mot[axis]._chan_ident, relative_distance=dst))

    def stage_goto(self, axis='X', pos=0):
        self.cubes[axis].move_to(pos)
        #self.mot[axis]._port.send_message(
        #    MGMSG_MOT_MOVE_ABSOLUTE_long(chan_ident=self.mot[axis]._chan_ident, absolute_distance=pos))

    def stage_stop(self, axis='X'):
        self.cubes[axis].stop()
        #self.mot[axis]._port.send_message(
        #    MGMSG_MOT_MOVE_STOP(chan_ident=self.mot[axis]._chan_ident, stop_mode=0x02))

    def shut_down(self):
        for cube in self.cubes:
            self.cubes[cube].shutdown()

        if self.mono:
            self.mono.close()
