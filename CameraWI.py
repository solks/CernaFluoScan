from PyQt5.QtWidgets import (QWidget, QFrame, QSplitter, QSizePolicy, QTabWidget,
                             QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QRadioButton,
                             QSlider, QButtonGroup, QGroupBox, QTableWidget, QHeaderView, QTableWidgetItem,
                             QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QTextEdit, QProgressBar,
                             QAbstractItemView, QFileDialog)
from PyQt5.QtCore import Qt, QDir

from os import path, makedirs, listdir
import threading
import time
import datetime
import numpy as np
import re
import cv2
from pyqtgraph import ImageItem
from WidgetsUI import PgImageView

from CameraCtrl import Cam


class CamWI(QFrame):

    capture = False

    hFlip = False
    vFlip = False

    addPrimitives = False
    primitives = []

    alpha = 0.4

    def __init__(self, p_set):
        super().__init__()

        self.paramSet = p_set

        self.ui_construct()

        self.cam = Cam(self.update_image, self.paramSet['cam']['device'])
        # self.camData = np.zeros((self.cam.imageHeight, self.cam.imageWidth, self.cam.imageChannel), np.ubyte)

        self.fill_cam_list(self.cam.capDevices, self.paramSet['cam']['device'])

        self.connect_events()
        self.init_parameters()

    def init_parameters(self):
        cam_params = self.paramSet['cam']

        self.autoExposure.setChecked(cam_params['autoExp'])
        self.exposure.setSliderPosition(cam_params['exposure'])
        self.gain.setSliderPosition(cam_params['gain'])
        self.flipH.setChecked(cam_params['hFlip'])
        self.flipV.setChecked(cam_params['vFlip'])

        if cam_params['savePath'] != '':
            self.dstPath.setText(cam_params['savePath'])
        else:
            self.dstPath.setText(QDir.currentPath())

    def connect_events(self):
        self.camSelect.currentIndexChanged.connect(self.device_select)

        self.exposure.valueChanged.connect(self.exposure_change)
        self.gain.valueChanged.connect(self.gain_change)
        self.autoExposure.stateChanged.connect(self.auto_exp_change)
        self.flipH.stateChanged.connect(self.hflip_change)
        self.flipV.stateChanged.connect(self.vflip_change)

        self.chooseDst.clicked.connect(self.change_dst_path)
        self.saveImage.clicked.connect(self.save_image)

    def ui_construct(self):
        # Main layout
        self.camSelect = QComboBox(self)
        self.camSelect.setToolTip('Choose Camera...')

        self.camFrame = PgImageView()
        self.camFrame.getView().setAspectLocked()
        self.camFrame.getView().enableAutoRange()
        self.camImage = ImageItem()
        self.camFrame.addItem(self.camImage)

        self.exposure = QSlider(Qt.Vertical)
        self.gain = QSlider(Qt.Vertical)
        self.autoExposure = QCheckBox('Auto exposition')
        exposure_lbl = QLabel('Exposition', self)
        gain_lbl = QLabel('Gain', self)

        self.flipH = QCheckBox('Flip Horizontal')
        self.flipV = QCheckBox('Flip Vertical')

        self.dstPath = QLineEdit(self)
        self.dstPath.setReadOnly(True)
        self.chooseDst = QPushButton('Choose Dir')
        self.saveImage = QPushButton('Save')
        self.chooseDst.setMinimumSize(90, 30)
        self.saveImage.setMinimumSize(90, 30)
        # dst_path_lbl = QLabel('Path:', self)

        exposure_group = QGroupBox('Exposition')
        exposure_group.setAlignment(Qt.AlignCenter)
        exposure_lay = QGridLayout(exposure_group)
        exposure_lay.addWidget(self.exposure, 0, 0, Qt.AlignCenter)
        exposure_lay.addWidget(self.gain, 0, 1, Qt.AlignCenter)
        exposure_lay.addWidget(exposure_lbl, 1, 0)
        exposure_lay.addWidget(gain_lbl, 1, 1)
        exposure_lay.addWidget(self.autoExposure, 2, 0, 1, 2)

        flip_group = QGroupBox('Flip image')
        flip_group.setAlignment(Qt.AlignCenter)
        flip_lay = QVBoxLayout(flip_group)
        flip_lay.addWidget(self.flipH)
        flip_lay.addWidget(self.flipV)

        # file_path = QFrame(self)
        # file_path_lay = QHBoxLayout(cam_file_path)
        # file_path_lay.addWidget(cam_dst_path_lbl)
        # file_path_lay.addWidget(self.camDstPath)

        file_group = QGroupBox('Save image')
        file_group.setAlignment(Qt.AlignCenter)
        file_lay = QGridLayout(file_group)
        # file_lay.addWidget(dst_path_lbl, 0, 0)
        file_lay.addWidget(self.dstPath, 1, 0, 1, 2)
        file_lay.addWidget(self.chooseDst, 2, 0)
        file_lay.addWidget(self.saveImage, 2, 1)

        cam_controls = QFrame(self)
        cam_param_lay = QVBoxLayout(cam_controls)
        cam_param_lay.addWidget(self.camSelect)
        cam_param_lay.addWidget(exposure_group)
        cam_param_lay.addWidget(flip_group)
        cam_param_lay.addWidget(file_group)

        cam_lay = QGridLayout(self)
        cam_lay.setColumnStretch(0, 1)
        cam_lay.setColumnStretch(1, 5)
        cam_lay.addWidget(cam_controls, 0, 0)
        cam_lay.addWidget(self.camFrame, 0, 1)

    def run(self):
        if not self.capture:
            success, dev_number = self.cam.connect(self.paramSet['cam']['device'])
            self.camSelect.setCurrentIndex(dev_number)
            self.camFrame.getView().setLimits(xMin=0, xMax=self.cam.imageWidth, yMin=0, yMax=self.cam.imageHeight)

            if success:
                self.cam.start_stream()
                self.capture = True

    def stop(self):
        if self.capture:
            self.cam.disconnect()
            self.capture = False

    def fill_cam_list(self, device_list, current_index):
        for i, device in enumerate(device_list):
            self.camSelect.addItem(device['name'] + ' [W ' + str(device['width']) + ' : H ' + str(device['height']) + ']')

        self.camSelect.setCurrentIndex(current_index)

    def update_image(self, frame):
        if self.capture:
            if self.addPrimitives:
                frame = self.draw_primitives(frame)

            if self.cam.imageChannel == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            if self.hFlip and self.vFlip:
                frame = cv2.flip(frame, -1)
            elif self.hFlip:
                frame = cv2.flip(frame, 1)
            elif self.vFlip:
                frame = cv2.flip(frame, 0)

            # bytes_per_line = self.imageChannel * self.imageWidth
            # q_image = QImage(self.cvImage.data, self.imageWidth, self.imageHeight, bytes_per_line, QImage.Format_RGB888)

            self.camImage.setImage(frame)

    def draw_primitives(self, cv_img):
        overlay = cv_img.copy()
        return cv2.addWeighted(overlay, self.alpha, cv_img, 1 - self.alpha, 0, cv_img)

    def device_select(self, idx):
        success, dev_number = self.cam.connect(idx)
        if success:
            self.paramSet['cam']['device'] = dev_number
            self.camSelect.setCurrentIndex(dev_number)

        if self.capture:
            self.cam.start_stream()

    def exposure_change(self, exposure):
        self.paramSet['cam']['exposure'] = exposure
        self.cam.set_exposure(exposure/100, auto_adjust=self.autoExposure.isChecked())

    def gain_change(self, gain):
        self.paramSet['cam']['gain'] = gain
        self.cam.set_gain(gain/100)

    def auto_exp_change(self, val):
        self.paramSet['cam']['autoExp'] = val
        self.cam.set_auto_exposure(val)

    def hflip_change(self, val):
        if val:
            self.paramSet['cam']['hFlip'] = True
            self.hFlip = True
        else:
            self.paramSet['cam']['hFlip'] = False
            self.hFlip = False

    def vflip_change(self, val):
        if val:
            self.paramSet['cam']['vFlip'] = True
            self.vFlip = True
        else:
            self.paramSet['cam']['vFlip'] = False
            self.vFlip = False

    def change_dst_path(self):
        dst = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.paramSet['cam']['savePath'] = dst
        self.dstPath.setText(dst)

    def save_image(self):
        file_list = []
        dst_path = path.join(self.paramSet['cam']['savePath'], datetime.datetime.now().strftime('%d.%m.%Y'))
        if not path.exists(dst_path):
            makedirs(dst_path)

        file_list = listdir(dst_path)
        if len(file_list) > 0:
            file_list.sort(key=lambda f: int(re.search(r'\d+', f).group()))
            name_id = int(re.search(r'\d+', file_list[-1]).group())
        else:
            name_id = 0

        filename = path.join(dst_path, str(name_id + 1).zfill(4) + '.png')

        frame = self.cam.get_frame()
        if frame is not None:
            if self.cam.imageChannel == 3:
                return cv2.imwrite(filename, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return cv2.imwrite(filename, frame)
        else:
            return False

    def shut_down(self):
        self.stop()
        time.sleep(0.2)
