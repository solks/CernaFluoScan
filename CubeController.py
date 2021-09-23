from __future__ import print_function
from __future__ import division
import os
import sys
import time
import clr

clr.AddReference("System")
clr.AddReference("thorlabs/Thorlabs.MotionControl.DeviceManagerCLI")
clr.AddReference("thorlabs/Thorlabs.MotionControl.KCube.DCServoCLI")
clr.AddReference("thorlabs/Thorlabs.MotionControl.GenericMotorCLI")

from System import Decimal
from System import Enum
from System import UInt32
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceConfiguration
from Thorlabs.MotionControl.KCube.DCServoCLI import KCubeDCServo
from Thorlabs.MotionControl.GenericMotorCLI import MotorDirection


class CubeController:
    _kCubeDCServoMotor = None
    def __init__(self, serial_number_num):
        try:
            serial_number = str(serial_number_num)
            DeviceManagerCLI.BuildDeviceList()
            self._kCubeDCServoMotor = KCubeDCServo.CreateKCubeDCServo(serial_number)
            self._kCubeDCServoMotor.Connect(serial_number)
            self._kCubeDCServoMotor.WaitForSettingsInitialized(5000)
            self._kCubeDCServoMotor.LoadMotorConfiguration(self._kCubeDCServoMotor.DeviceID,
                                                           DeviceConfiguration.DeviceSettingsUseOptionType.UseFileSettings)

            print("Connected KCube#" + self._kCubeDCServoMotor.DeviceID)
        except:
            print("CubeController init error:", sys.exc_info()[0])

    def move_steps(self, distance):
        direction = "Forward" if distance >= 0 else "Backward"
        motor_dir_clr_type = clr.GetClrType(MotorDirection)
        direction_enum = Enum.Parse(motor_dir_clr_type, direction)
        self._kCubeDCServoMotor.MoveRelative_DeviceUnit(direction_enum, UInt32(abs(distance)), 0)

    def move_to(self, position):
        self._kCubeDCServoMotor.MoveTo(Decimal(position), 0)

    def home(self):
        self._kCubeDCServoMotor.Home(0)

    def get_position(self):
        return self._kCubeDCServoMotor.Position

    def stop(self):
        self._kCubeDCServoMotor.Stop(0)

    def shutdown(self):
        self._kCubeDCServoMotor.ShutDown()

    def get_status(self):
        return self._kCubeDCServoMotor.Status

    def get_is_jogging(self):
        return self.get_status().IsJogging

    def get_is_moving(self):
        return self.get_status().IsMoving

    position = property(get_position, None, None)
    is_jogging = property(get_is_jogging, None, None)
    is_moving = property(get_is_moving, None, None)
