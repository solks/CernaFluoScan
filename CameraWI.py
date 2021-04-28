from PyQt5.QtWidgets import (QWidget, QFrame, QSplitter, QSizePolicy, QTabWidget,
                             QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QRadioButton,
                             QSlider, QButtonGroup, QGroupBox, QTableWidget, QHeaderView, QTableWidgetItem,
                             QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QTextEdit, QProgressBar,
                             QAbstractItemView, QFileDialog)
from PyQt5.QtCore import Qt, QDir

from os import path, makedirs, listdir
import time
import datetime
import numpy as np
import re
import cv2
from WidgetsUI import PgGraphicsView


class CamWI(QFrame):

    active = False

    hFlip = False
    vFlip = False

    addPrimitives = False
    primitives = []

    saveFrame = False
    file_idx = None
    path = ''

    alpha = 0.4

    def __init__(self, cam, p_set, activate):
        super().__init__()

        self.paramSet = p_set

        self.active = activate

        self.ui_construct()

        self.cam = cam
        # self.camData = np.zeros((self.cam.imageHeight, self.cam.imageWidth, self.cam.imageChannel), np.ubyte)

        self.connect_events()
        self.set_wi_params()

    def connect_events(self):
        self.camSelect.currentIndexChanged.connect(self.device_select)

        self.cam.frameAcquired.connect(self.update_frame)
        self.cam.devStarted.connect(self.set_cam_controls)

        self.exposure.valueChanged.connect(self.exposure_change)
        self.gain.valueChanged.connect(self.gain_change)
        self.autoExposure.stateChanged.connect(self.auto_exp_change)
        self.flipH.stateChanged.connect(self.hflip_change)
        self.flipV.stateChanged.connect(self.vflip_change)

        self.chooseDst.clicked.connect(self.change_dst_path)
        self.saveImage.clicked.connect(self.save_image)

    def set_wi_params(self):
        cam_params = self.paramSet['cam']

        self.fill_cam_list(self.cam.capDevices, cam_params['device'])
        self.device_select(cam_params['device'])

        self.flipH.setChecked(cam_params['hFlip'])
        self.flipV.setChecked(cam_params['vFlip'])

        if cam_params['savePath'] != '':
            self.dstPath.setText(cam_params['savePath'])
        else:
            self.dstPath.setText(QDir.currentPath())

    def set_cam_controls(self):
        cam_params = self.paramSet['cam']

        self.autoExposure.setChecked(cam_params['autoExp'])
        self.exposure.setSliderPosition(cam_params['exposure'])
        self.gain.setSliderPosition(cam_params['gain'])

    def ui_construct(self):
        # Main layout
        self.camSelect = QComboBox(self)
        self.camSelect.setToolTip('Choose Camera...')

        self.camFrame = PgGraphicsView(self, aspect_locked=True)
        self.camFrame.setMinimumSize(512, 512)

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

    def fill_cam_list(self, device_list, current_index):
        self.camSelect.blockSignals(True)

        self.camSelect.clear()

        for i, device in enumerate(device_list):
            self.camSelect.addItem(device['name'] + ' [W ' + str(device['width']) + ' : H ' + str(device['height']) + ']')
        self.camSelect.setCurrentIndex(current_index)

        self.camSelect.blockSignals(False)

    def device_select(self, idx):
        if self.active:
            success, dev_number = self.cam.connect(idx)

            if success:
                self.paramSet['cam']['device'] = dev_number
                self.camFrame.vb.setLimits(xMin=0, xMax=self.cam.imageWidth, yMin=0, yMax=self.cam.imageHeight)

                self.cam.ctrl.start_streaming()
            else:
                if idx != 0:
                    self.paramSet['cam']['device'] = 0
                    self.camSelect.setCurrentIndex(0)
                else:
                    print('Device selection error')
        else:
            try:
                self.camFrame.vb.setLimits(xMin=0, xMax=self.cam.imageWidth, yMin=0, yMax=self.cam.imageHeight)
            except:
                pass

    def update_frame(self, frame):
        if self.active:
            if self.addPrimitives:
                frame = self.draw_primitives(frame)

            if self.cam.imageChannel == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            self.camFrame.image.setImage(self.frame_transform(frame, vInvert=True), autoLevels=False)

        if self.saveFrame:
            self.saveFrame = False
            filename = path.join(self.path, str(self.file_idx).zfill(4) + '.png')

            frame = self.frame_transform(frame, vInvert=False)
            if self.cam.imageChannel == 3:
                return cv2.imwrite(filename, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return cv2.imwrite(filename, frame)

    def draw_primitives(self, cv_img):
        overlay = cv_img.copy()
        return cv2.addWeighted(overlay, self.alpha, cv_img, 1 - self.alpha, 0, cv_img)

    def frame_transform(self, frame, vInvert=False):
        # PgGraphicsView inverted image:
        if vInvert:
            if self.hFlip and not self.vFlip:
                frame = cv2.flip(frame, -1)
            elif self.hFlip:
                frame = cv2.flip(frame, 1)
            elif not self.vFlip:
                frame = cv2.flip(frame, 0)
        # Default:
        else:
            if self.hFlip and self.vFlip:
                frame = cv2.flip(frame, -1)
            elif self.hFlip:
                frame = cv2.flip(frame, 1)
            elif self.vFlip:
                frame = cv2.flip(frame, 0)

        return frame

    def exposure_change(self, exposure):
        if self.active:
            self.paramSet['cam']['exposure'] = exposure
            self.cam.ctrl.set_exposure(exposure/100, auto_adjust=self.autoExposure.isChecked())

    def gain_change(self, gain):
        if self.active:
            self.paramSet['cam']['gain'] = gain
            self.cam.ctrl.set_gain(gain/100)

    def auto_exp_change(self, val):
        if self.active:
            self.paramSet['cam']['autoExp'] = val
            self.cam.ctrl.set_auto_exposure(val)

            if not val:
                exposure = self.paramSet['cam']['exposure']
                gain = self.paramSet['cam']['gain']
                self.cam.ctrl.set_exposure(exposure / 100, auto_adjust=self.autoExposure.isChecked())
                self.cam.ctrl.set_gain(gain / 100)

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
        if self.path == '':
            self.path = path.join(self.paramSet['cam']['savePath'], datetime.datetime.now().strftime('%d.%m.%Y'))
            if not path.exists(self.path):
                makedirs(self.path)

        if self.file_idx is None:
            file_list = listdir(self.path)
            if len(file_list) > 0:
                file_list.sort(key=lambda f: int(re.search(r'\d+', f).group()))
                self.file_idx = int(re.search(r'\d+', file_list[-1]).group()) + 1
            else:
                self.file_idx = 1
        else:
            self.file_idx += 1

        if self.cam.ctrl.streaming:
            self.saveFrame = True
        else:
            frame = self.cam.ctrl.get_frame()
            if frame:
                self.saveFrame = False

                frame = self.frame_transform(frame, vInvert=False)
                filename = path.join(self.path, str(self.file_idx).zfill(4) + '.png')

                if self.cam.imageChannel == 3:
                    return cv2.imwrite(filename, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                else:
                    return cv2.imwrite(filename, frame)

    def stop(self):
        if self.active:
            self.cam.disconnect()

    def shut_down(self):
        self.stop()
        time.sleep(0.5)
