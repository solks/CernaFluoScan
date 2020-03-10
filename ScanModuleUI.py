from PyQt5.QtWidgets import (QWidget, QFrame, QSplitter, QSizePolicy, QTabWidget,
                             QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QRadioButton,
                             QSlider, QButtonGroup, QGroupBox, QTableWidget, QTableWidgetItem, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QLineEdit)
from PyQt5.QtCore import Qt, QDir, QRectF, QLineF, QPointF
from PyQt5.QtGui import QIntValidator
from WidgetsUI import CTabBar

import pyqtgraph as pg


class ScanModuleUI(QWidget):

    def __init__(self):
        super().__init__()

        self.ui_construct()

    def ui_construct(self):
        # Main splitters
        topleft_frame = QFrame(self)
        topleft_frame.setFrameShape(QFrame.StyledPanel)

        topright_frame = QFrame(self)
        topright_frame.setFrameShape(QFrame.StyledPanel)

        bottom_frame = QFrame(self)
        bottom_frame.setFrameShape(QFrame.StyledPanel)

        splitter1 = QSplitter(Qt.Horizontal)
        splitter1.addWidget(topleft_frame)
        splitter1.addWidget(topright_frame)
        splitter1.setSizes((300, 100))
        splitter1.setStretchFactor(0, 0)
        splitter1.setStretchFactor(1, 1)

        splitter2 = QSplitter(Qt.Vertical)
        splitter2.addWidget(splitter1)
        splitter2.addWidget(bottom_frame)
        splitter2.setSizes((100, 250))
        splitter2.setStretchFactor(0, 1)
        splitter2.setStretchFactor(1, 0)

        main_lay = QVBoxLayout(self)
        main_lay.addWidget(splitter2)

        view_area = QTabWidget(self)
        vcam = QFrame(self)
        scan_map = QFrame(self)
        view_area.addTab(vcam, "Camera")
        view_area.addTab(scan_map, "Scan Map")

        view_area_lay = QVBoxLayout(topright_frame)
        view_area_lay.addWidget(view_area)

        # Camera layout

        self.vcamSelect = QComboBox(self)
        self.vcamSelect.setToolTip('Choose Camera...')

        self.vCamFrame = self.image_frame_widget()
        self.camImage = pg.ImageItem()
        self.vCamFrame.addItem(self.camImage)

        self.vcamExposure = QSlider(Qt.Vertical)
        self.vcamGain = QSlider(Qt.Vertical)
        vcam_exposure_lbl = QLabel('Exposition', self)
        vcam_gain_lbl = QLabel('Gain', self)

        self.vcamFlipH = QCheckBox('Flip Horizontal')
        self.vcamFlipV = QCheckBox('Flip Vertical')

        self.vcamShowScan = QCheckBox('Show Scan Area')

        self.vcamDstPath = QLineEdit(QDir.currentPath(), self)
        self.vcamChooseDst = QPushButton('Choose Dir')
        self.vcamSaveImage = QPushButton('Save')
        # vcam_dst_path_lbl = QLabel('Path:', self)

        vcam_exposure_group = QGroupBox('Exposition')
        vcam_exposure_group.setAlignment(Qt.AlignCenter)
        vcam_exposure_lay = QGridLayout(vcam_exposure_group)
        vcam_exposure_lay.addWidget(self.vcamExposure, 0, 0, Qt.AlignCenter)
        vcam_exposure_lay.addWidget(self.vcamGain, 0, 1, Qt.AlignCenter)
        vcam_exposure_lay.addWidget(vcam_exposure_lbl, 1, 0)
        vcam_exposure_lay.addWidget(vcam_gain_lbl, 1, 1)

        vcam_flip_group = QGroupBox('Flip image')
        vcam_flip_group.setAlignment(Qt.AlignCenter)
        vcam_flip_lay = QVBoxLayout(vcam_flip_group)
        vcam_flip_lay.addWidget(self.vcamFlipH)
        vcam_flip_lay.addWidget(self.vcamFlipV)

        vcam_scan_area_group = QGroupBox('Scan Area')
        vcam_scan_area_group.setAlignment(Qt.AlignCenter)
        vcam_scan_area_lay = QVBoxLayout(vcam_scan_area_group)
        vcam_scan_area_lay.addWidget(self.vcamShowScan)

        # vcam_file_path = QFrame(self)
        # vcam_file_path_lay = QHBoxLayout(vcam_file_path)
        # vcam_file_path_lay.addWidget(vcam_dst_path_lbl)
        # vcam_file_path_lay.addWidget(self.vcamDstPath)

        vcam_file_group = QGroupBox('Save image')
        vcam_file_group.setAlignment(Qt.AlignCenter)
        vcam_file_lay = QGridLayout(vcam_file_group)
        # vcam_file_lay.addWidget(vcam_dst_path_lbl, 0, 0)
        vcam_file_lay.addWidget(self.vcamDstPath, 1, 0, 1, 2)
        vcam_file_lay.addWidget(self.vcamChooseDst, 2, 0)
        vcam_file_lay.addWidget(self.vcamSaveImage, 2, 1)

        vcam_param = QFrame(self)
        vcam_param_lay = QVBoxLayout(vcam_param)
        vcam_param_lay.addWidget(self.vcamSelect)
        vcam_param_lay.addWidget(vcam_exposure_group)
        vcam_param_lay.addWidget(vcam_flip_group)
        vcam_param_lay.addWidget(vcam_scan_area_group)
        vcam_param_lay.addWidget(vcam_file_group)

        vcam_lay = QGridLayout(vcam)
        vcam_lay.setColumnStretch(0, 1)
        vcam_lay.setColumnStretch(1, 5)
        vcam_lay.addWidget(vcam_param, 0, 0)
        vcam_lay.addWidget(self.vCamFrame, 0, 1)

        # Scan map layout

        self.scanMapFrame = self.image_frame_widget()
        self.scanMap = pg.ImageItem()
        self.scanMapFrame.addItem(self.scanMap)

        scan_map_lay = QGridLayout(scan_map)
        scan_map_lay.addWidget(self.scanMapFrame)

        # Scan parameters, save data

        self.x1_dim = QTableWidgetItem('Mot X')
        self.x1_min = QTableWidgetItem()
        self.x1_max = QTableWidgetItem()
        self.x2_dim = QTableWidgetItem('Mot Y')
        self.x2_min = QTableWidgetItem()
        self.x2_max = QTableWidgetItem()
        self.x3_dim = QTableWidgetItem('Mot Z')
        self.x3_min = QTableWidgetItem()
        self.x3_max = QTableWidgetItem()
        self.x4_dim = QTableWidgetItem('Wavelength')
        self.x4_min = QTableWidgetItem()
        self.x4_max = QTableWidgetItem()

        scan_parameters = QTableWidget(4, 3)
        scan_parameters.setMaximumWidth(200)
        # scan_parameters.setMaximumHeight(119)
        scan_parameters.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        scan_parameters.setStyleSheet("border: 0")
        scan_parameters.setHorizontalHeaderLabels(['Dim.', 'Min val.', 'Max val.'])
        scan_parameters.setVerticalHeaderLabels(['X1', 'X2', 'X3'])
        scan_parameters.setItem(0, 0, self.x1_dim)
        scan_parameters.setItem(0, 1, self.x1_min)
        scan_parameters.setItem(0, 2, self.x1_max)
        scan_parameters.setItem(1, 0, self.x2_dim)
        scan_parameters.setItem(1, 1, self.x2_min)
        scan_parameters.setItem(1, 2, self.x2_max)
        scan_parameters.setItem(2, 0, self.x3_dim)
        scan_parameters.setItem(2, 1, self.x3_min)
        scan_parameters.setItem(2, 2, self.x3_max)
        scan_parameters.setItem(3, 0, self.x4_dim)
        scan_parameters.setItem(3, 1, self.x4_min)
        scan_parameters.setItem(3, 2, self.x4_max)

        scan_param_lay = QVBoxLayout(topleft_frame)
        scan_param_lay.addWidget(scan_parameters)

    def image_frame_widget(self):
        bg_color = pg.mkColor('#29353D')
        pg.setConfigOptions(background=bg_color)
        pg.setConfigOptions(imageAxisOrder='row-major')

        frame = pg.ImageView()
        frame.getView().setLimits(xMin=0, xMax=1025, yMin=0, yMax=256)

        size_policy = QSizePolicy()
        size_policy.setHorizontalPolicy(QSizePolicy.Expanding)
        size_policy.setVerticalPolicy(QSizePolicy.Expanding)
        frame.setSizePolicy(size_policy)
        frame.setMinimumSize(512, 512)
        frame.ui.histogram.hide()
        frame.ui.roiBtn.hide()
        frame.ui.menuBtn.hide()

        return frame
