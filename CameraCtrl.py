import time
import cv2
import numpy as np

from threading import Thread, Event
from vimba import *


class Cam(object):
    connStatus = False
    streaming = False

    capDevices = []
    dev_number = 0

    provider = 'opencv'

    imageWidth = 100
    imageHeight = 100
    imageChannel = 1

    def __init__(self, callback, dev=0):

        self.cap = None

        self.updWiImage = callback

        self.capDevices = self.test_devices()
        self.camImg = np.zeros((self.imageHeight, self.imageWidth, self.imageChannel), np.ubyte)

        self.stop_event = Event()
        self.camThread = Thread()

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
                for cam in cams[0]:
                    img = cam.get_frame().as_opencv_image()
                    height, width, channel = img.shape
                    devices.append({
                        'deviceID': cam.get_id(),
                        'provider': 'vimba',
                        'name': cam.get_name,
                        'width': width,
                        'height': height,
                        'channel': channel
                    })

        return devices

    def connect(self, dev):
        if self.connStatus:
            self.disconnect()

        status = False
        if len(self.capDevices) > 0:
            if dev > len(self.capDevices)-1:
                dev = 0

            dev_id = self.capDevices[dev]['deviceID']
            provider = self.capDevices[dev]['provider']

            if provider == 'opencv':
                self.cap = cv2.VideoCapture(dev_id)
                if self.cap.isOpened():
                    status = True
                    # print(cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.5))
                    # print(cap.get(cv2.CAP_PROP_AUTO_EXPOSURE))
            elif provider == 'vimba':
                with Vimba.get_instance() as vimba:
                    status = True
                    try:
                        self.cap = vimba.get_camera_by_id(dev_id)
                    except VimbaCameraError:
                        print('Failed to access Camera. Abort.')
                        status = False

                    if status:
                        # Try to adjust GeV packet size for GigE camera.
                        try:
                            self.cap.GVSPAdjustPacketSize.run()

                            while not self.cap.GVSPAdjustPacketSize.is_done():
                                pass
                        except (AttributeError, VimbaFeatureError):
                            print('Failed to adjust GeV packet size.')

                        # Get pixel formats available in the camera
                        # print(cap.get_pixel_formats())

                        cv_fmts = intersect_pixel_formats(cap.get_pixel_formats(), OPENCV_PIXEL_FORMATS)
                        color_fmts = intersect_pixel_formats(cv_fmts, COLOR_PIXEL_FORMATS)
                        self.cap.set_pixel_format(color_fmts[0])
            else:
                self.cap = None

            if status:
                self.connStatus = status
                self.dev_number = dev
                self.provider = self.capDevices[self.dev_number]['provider']
                self.imageWidth = self.capDevices[self.dev_number]['width']
                self.imageHeight = self.capDevices[self.dev_number]['height']
                self.imageChannel = self.capDevices[self.dev_number]['channel']

        return status, self.dev_number

    def disconnect(self):
        if self.streaming:
            self.stop_stream()

        if self.provider == 'opencv':
            if self.cap.isOpened():
                self.cap.release()

        self.connStatus = False

    def start_stream(self):
        if self.provider == 'opencv':
            self.stop_event.clear()
            if not self.camThread.is_alive():
                self.camThread = Thread(target=self.opencv_capture)
            try:
                self.camThread.start()
                self.streaming = True
            except:
                pass
        elif self.provider == 'vimba':
            try:
                self.cap.start_streaming(handler=self.vmb_frame_handler, buffer_count=5)
                self.streaming = True
            except:
                pass

    def stop_stream(self):
        if self.provider == 'opencv':
            self.stop_event.set()
            self.camThread.join()
            self.streaming = False
        elif self.provider == 'vimba':
            try:
                self.cap.stop_streaming()
                self.streaming = False
            except:
                pass

    def vmb_frame_handler(self, cam, frame):
        cam.queue_frame(frame)
        self.updWiImage(frame.as_opencv_image())

    def opencv_capture(self):
        while not self.stop_event.is_set():
            capture_success, self.camImg = self.cap.read()
            self.updWiImage(self.camImg)
            time.sleep(0.05)

    def get_frame(self):
        frame = None
        streaming_state = self.streaming

        if self.connStatus:
            if streaming_state:
                self.stop_stream()

            if self.provider == 'opencv':
                capture_success, self.camImg = self.cap.read()
                if capture_success:
                    frame = self.camImg
            elif self.provider == 'vimba':
                try:
                    frame = self.cap.get_frame().as_opencv_image()
                except:
                    pass

            if streaming_state:
                self.start_stream()

        return frame

    def set_exposure(self, exposure, auto_adjust=False):
        # exposure: float, range 0..1
        # auto_adjust: True if brightness auto adjusting activated

        default_min_exposure = 1  # in ms
        default_DR = 4
        makoG234_min_exposure = 73.544  # in useconds
        makoG234_DR = 6
        default_auto_range = 1
        makoG234_auto_range = 100

        if self.connStatus:
            if self.provider == 'opencv':
                if auto_adjust:
                    target_val = exposure * default_auto_range  # float 0..1
                    return self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, target_val)
                else:
                    exp_val = round(default_min_exposure * pow(10, exposure * default_DR))  # in ms
                    return self.cap.set(cv2.CAP_PROP_EXPOSURE, exp_val)
            elif self.provider == 'vimba':
                if auto_adjust:
                    target_val = round(exposure * makoG234_auto_range)  # integer 0..100
                    try:
                        return self.cap.ExposureAutoTarget.set(target_val)
                    except:
                        return False
                else:
                    exp_val = round(makoG234_min_exposure * pow(10, exposure * makoG234_DR))  # in us
                    try:
                        return self.cap.ExposureTimeAbs.set(exp_val)
                    except:
                        return False
            else:
                return False
        else:
            return False

    def set_gain(self, gain):
        # gain: float, range 0..1
        default_max_gain = 5
        makoG234_max_gain = 40
        if self.connStatus:
            if self.provider == 'opencv':
                g_val = round(gain * default_max_gain)
                return self.cap.set(cv2.CAP_PROP_GAIN, g_val)
            elif self.provider == 'vimba':
                g_val = round(gain * makoG234_max_gain, 1)
                try:
                    return self.cap.Gain.set(g_val)
                except:
                    return False
            else:
                return False
        else:
            return False

    def set_auto_exposure(self, set_auto=False):
        if self.connStatus:
            if self.provider == 'opencv':
                return self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.5)
            elif self.provider == 'vimba':
                if set_auto:
                    try:
                        return self.cap.ExposureAuto.set('Continuous')
                    except:
                        return False
                else:
                    try:
                        return self.cap.ExposureAuto.set('Off')
                    except:
                        return False
        else:
            return False
