import cv2
import numpy as np

from vimba import *


class Cam(object):

    primitives = []

    alpha = 0.4

    def __init__(self):

        self.camOpened = False
        self.addPrimitives = False
        self.hFlip = False
        self.vFlip = False

        self.capList = self.test_device()
        if len(self.capList) > 0:
            self.cap = cv2.VideoCapture(self.capList[0]['deviceID'])
            self.imageWidth = self.capList[0]['width']
            self.imageHeight = self.capList[0]['height']
            self.imageChannel = self.capList[0]['channel']

            if self.cap.isOpened():
                self.camOpened = True

    def test_device(self):
        caps = []

        # attempt to connect to devices via opencv
        for id in range(3):
            cap = cv2.VideoCapture(id)
            if not (cap is None) and cap.isOpened():
                flag, img = cap.read()
                height, width, channel = img.shape
                caps.append({
                    'deviceID': id,
                    'provider': 'opencv',
                    'name': 'Camera #' + str(id),
                    'width': width,
                    'height': height,
                    'channel': channel
                })
                cap.release()

        # attempt to connect to AlliedVision camera via vimba
        with Vimba.get_instance() as vimba:
            cams = vimba.get_all_cameras()
            for cam in cams[0]:
                img = cam.get_frame().as_opencv_image()
                height, width, channel = img.shape
                caps.append({
                    'deviceID': cam.get_id(),
                    'provider': 'vimba',
                    'name': cam.get_name,
                    'width': width,
                    'height': height,
                    'channel': channel
                })

        return caps

    def get_frame(self):
        if not self.cap.isOpened():
            success = self.cap.open(0)
            if not success:
                return False

        flag, image = self.cap.read()

        if flag:
            return image
        else:
            return False

    def requestImage(self):
        self.cvImage = self.get_frame()

        if self.addPrimitives:
            self.draw_primitives()

        self.cvImage = cv2.cvtColor(self.cvImage, cv2.COLOR_BGR2RGB)

        if self.hFlip and self.vFlip:
            self.cvImage = cv2.flip(self.cvImage, -1)
        elif self.hFlip:
            self.cvImage = cv2.flip(self.cvImage, 1)
        elif self.vFlip:
            self.cvImage = cv2.flip(self.cvImage, 0)

        # bytes_per_line = self.imageChannel * self.imageWidth
        # q_image = QImage(self.cvImage.data, self.imageWidth, self.imageHeight, bytes_per_line, QImage.Format_RGB888)

        return self.cvImage

    def draw_primitives(self):
        overlay = self.cvImage.copy()
        cv2.addWeighted(overlay, self.alpha, self.cvImage, 1 - self.alpha, 0, self.cvImage)

    def set_gain(self, gain):
        self.cap.set(cv2.CAP_PROP_GAIN, gain)