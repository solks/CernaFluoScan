import time
from threading import Event
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, QObject

import cv2
import numpy as np

from vimba import *


class Cam(QObject):

    ctrl = None

    capDevices = []

    imageWidth = 100
    imageHeight = 100
    imageChannel = 1

    frameAcquired = pyqtSignal(np.ndarray)
    devStarted = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.capDevices = self.test_devices()
        # self.camImg = np.zeros((self.imageHeight, self.imageWidth, self.imageChannel), np.ubyte)

    def test_devices(self):
        devices = []

        # attempt to connect to cameras via opencv
        for id in range(3):
            cap = cv2.VideoCapture(id)
            if not (cap is None) and cap.isOpened():
                flag, img = cap.read()
                height, width, channel = img.shape
                devices.append({
                    'deviceID': id,
                    'provider': 'opencv',
                    'name': 'Camera #' + str(id + 1),
                    'width': width,
                    'height': height,
                    'channel': channel
                })
                cap.release()

        # attempt to connect to AlliedVision camera via vimba
        with Vimba.get_instance() as vimba:
            cams = vimba.get_all_cameras()
            if cams:
                for i in range(len(cams)):
                    with cams[i] as cam:
                        # self.vmb_pixel_format(cam)
                        devices.append({
                            'deviceID': cam.get_id(),
                            'provider': 'vimba',
                            'name': cam.get_feature_by_name('DeviceModelName').get(),
                            'width': cam.get_feature_by_name('WidthMax').get(),
                            'height': cam.get_feature_by_name('HeightMax').get(),
                            'channel': 1  # ToDo: channel count by pixel format
                        })

        return devices

    def connect(self, dev):
        if len(self.capDevices) > 0:
            if dev > len(self.capDevices)-1:
                dev = 0

            dev_id = self.capDevices[dev]['deviceID']
            provider = self.capDevices[dev]['provider']

            if provider == 'vimba':
                self.ctrl = VimbaCam(dev_id, self.frameAcquired, self.devStarted)
            elif provider == 'opencv':
                self.ctrl = OpencvCam(dev_id, self.frameAcquired, self.devStarted)
            else:
                return False, dev

            if self.ctrl.connStatus:
                self.imageWidth = self.capDevices[dev]['width']
                self.imageHeight = self.capDevices[dev]['height']
                self.imageChannel = self.capDevices[dev]['channel']

            return self.ctrl.connStatus, dev
        else:
            return False, dev

    def disconnect(self):
        if self.ctrl is not None:
            self.ctrl.disconnect()


class VimbaCam(QObject):

    connStatus = False
    streaming = False

    def __init__(self, dev_id, frame_acquired, dev_started):
        super().__init__()

        self.frameAcquiredSig = frame_acquired
        self.devStartedSig = dev_started

        with Vimba.get_instance() as vimba:
            try:
                self.cap = vimba.get_camera_by_id(dev_id)
                self.connStatus = True
            except VimbaCameraError:
                print('Failed to access Camera. Abort.')

            if self.connStatus:
                self.camThread = VimbaStream(self.cap, self.frameAcquiredSig, self.devStartedSig)

                # Setup camera.
                self.setup_camera(self.cap)
                # Set pixel format
                self.pixel_format(self.cap)

    def setup_camera(self, cam: Camera):
        with cam:
            # Try to adjust GeV packet size for GigE camera.
            try:
                cam.GVSPAdjustPacketSize.run()

                while not cam.GVSPAdjustPacketSize.is_done():
                    pass

            except (AttributeError, VimbaFeatureError):
                pass

    def pixel_format(self, cam):
        with cam:
            # print(cam.get_pixel_formats())
            cv_fmts = intersect_pixel_formats(cam.get_pixel_formats(), OPENCV_PIXEL_FORMATS)
            color_fmts = intersect_pixel_formats(cv_fmts, COLOR_PIXEL_FORMATS)

            if color_fmts:
                cam.set_pixel_format(color_fmts[0])
            else:
                mono_fmts = intersect_pixel_formats(cv_fmts, MONO_PIXEL_FORMATS)
                if mono_fmts:
                    cam.set_pixel_format(mono_fmts[0])
                else:
                    print('Camera does not support a OpenCV compatible image formats')

    def get_frame(self):
        if self.connStatus:
            if not self.streaming:
                with self.cap:
                    try:
                        return self.cap.get_frame().as_opencv_image()
                    except:
                        return False
            else:
                return False

    def set_exposure(self, exposure, auto_adjust=False):
        # exposure: float, range 0..1
        # auto_adjust: True if brightness auto adjusting activated

        makoG234_min_exposure = 73.544  # in useconds
        makoG234_DR = 6
        makoG234_auto_range = 100

        if self.connStatus:
            if auto_adjust:
                target_val = round(exposure * makoG234_auto_range)  # integer 0..100
                with self.cap:
                    try:
                        return self.cap.ExposureAutoTarget.set(target_val)
                    except:
                        return False
            else:
                exp_val = round(makoG234_min_exposure * pow(10, exposure * makoG234_DR))  # in us
                with self.cap:
                    try:
                        return self.cap.ExposureTimeAbs.set(exp_val)
                    except:
                        return False
        else:
            return False

    def set_gain(self, gain):
        # gain: float, range 0..1

        makoG234_max_gain = 40

        if self.connStatus:
            g_val = round(gain * makoG234_max_gain, 1)
            with self.cap:
                try:
                    return self.cap.Gain.set(g_val)
                except:
                    return False
        else:
            return False

    def set_auto_exposure(self, set_auto=False):
        if self.connStatus:
            with self.cap:
                try:
                    if set_auto:
                        return self.cap.ExposureAuto.set('Continuous')
                    else:
                        return self.cap.ExposureAuto.set('Off')
                except:
                    return False
        else:
            return False

    def start_streaming(self):
        if self.connStatus:
            self.camThread.start()
            self.streaming = True

        return self.streaming

    def stop_streaming(self):
        if self.connStatus:
            self.camThread.stop_event.set()
            self.streaming = False

        return self.streaming

    def disconnect(self):
        if self.streaming:
            self.stop_streaming()

        self.connStatus = False


class VimbaStream(QThread):

    stop_event = Event()

    def __init__(self, cap, frame_acquired, stream_started):
        super().__init__()
        self.cap = cap
        self.frameAcquired = frame_acquired
        self.streamStarted = stream_started

    def frame_handler(self, cam: Camera, frame: Frame):
        if frame.get_status() == FrameStatus.Complete:
            self.frameAcquired.emit(frame.as_opencv_image())

        cam.queue_frame(frame)

    def run(self):
        with Vimba.get_instance():
            with self.cap:
                try:
                    self.cap.start_streaming(self.frame_handler, buffer_count=5)
                    self.streamStarted.emit()
                    self.stop_event.wait()
                    return
                except:
                    print('Vimba streaming error')
                finally:
                    self.cap.stop_streaming()


class OpencvCam(QObject):

    connStatus = False
    streaming = False

    def __init__(self, dev_id, frame_acquired, dev_started):
        super().__init__()

        self.frameAcquiredSig = frame_acquired
        self.devStartedSig = dev_started

        self.cap = cv2.VideoCapture(dev_id)
        if self.cap.isOpened():
            self.connStatus = True

        if self.connStatus:
            self.camThread = OpencvStream(self.cap, self.frameAcquiredSig, self.devStartedSig)

    def get_frame(self):
        if self.connStatus:
            if not self.streaming:
                with self.cap:
                    try:
                        capture_success, frame = self.cap.read()
                        return frame
                    except:
                        return False
            else:
                return False

    def set_exposure(self, exposure, auto_adjust=False):
        # exposure: float, range 0..1
        # auto_adjust: True if brightness auto adjusting activated

        default_min_exposure = 1  # in ms
        default_DR = 4
        default_auto_range = 1

        if self.connStatus:
            if auto_adjust:
                target_val = exposure * default_auto_range  # float 0..1
                return self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, target_val)
            else:
                exp_val = round(default_min_exposure * pow(10, exposure * default_DR))  # in ms
                return self.cap.set(cv2.CAP_PROP_EXPOSURE, exp_val)
        else:
            return False

    def set_gain(self, gain):
        # gain: float, range 0..1

        default_max_gain = 5

        if self.connStatus:
            g_val = round(gain * default_max_gain)
            return self.cap.set(cv2.CAP_PROP_GAIN, g_val)
        else:
            return False

    def set_auto_exposure(self, set_auto=False):
        if self.connStatus:
            if set_auto:
                return self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.5)
            else:
                pass
        else:
            return False

    def start_streaming(self):
        if self.connStatus:
            self.camThread.start()
            self.streaming = True

        return self.streaming

    def stop_streaming(self):
        if self.connStatus:
            self.camThread.stop_event.set()
            self.streaming = False

        return self.streaming

    def disconnect(self):
        if self.streaming:
            self.stop_streaming()

        self.cap.release()

        self.connStatus = False


class OpencvStream(QThread):

    stop_event = Event()

    def __init__(self, cap, frame_acquired, stream_started):
        super().__init__()

        self.cap = cap

        self.frameAcquired = frame_acquired
        self.streamStarted = stream_started

    def run(self):
        self.streamStarted.emit()
        while not self.stop_event.is_set():
            status, frame = self.cap.read()
            if status:
                self.frameAcquired.emit(frame)
            time.sleep(0.05)
        return
