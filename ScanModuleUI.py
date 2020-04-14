from PyQt5.QtWidgets import (QWidget, QFrame, QSplitter, QSizePolicy, QTabWidget,
                             QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QRadioButton,
                             QSlider, QButtonGroup, QGroupBox, QTableWidget, QHeaderView, QTableWidgetItem,
                             QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QTextEdit, QProgressBar)
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
        smap = QFrame(self)
        view_area.addTab(vcam, "Camera")
        view_area.addTab(smap, "Scan Map")

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
        self.vcamChooseDst.setMinimumSize(90, 30)
        self.vcamSaveImage.setMinimumSize(90, 30)
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

        self.mapFrame = self.image_frame_widget()
        self.map = pg.ImageItem()
        self.mapFrame.addItem(self.map)

        map_lay = QGridLayout(smap)
        map_lay.addWidget(self.mapFrame)

        # Map dimensions, experimental details

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

        map_dimensions_group = QGroupBox('Scan dimensions')
        map_dimensions = QTableWidget(4, 3)
        map_dimensions.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # map_dimensions.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        map_dimensions.setStyleSheet("border: 0")
        map_dimensions.setHorizontalHeaderLabels(['Dim.', 'Min', 'Max'])
        map_dimensions.setVerticalHeaderLabels(['X1', 'X2', 'X3', 'X4'])
        map_dimensions.setItem(0, 0, self.x1_dim)
        map_dimensions.setItem(0, 1, self.x1_min)
        map_dimensions.setItem(0, 2, self.x1_max)
        map_dimensions.setItem(1, 0, self.x2_dim)
        map_dimensions.setItem(1, 1, self.x2_min)
        map_dimensions.setItem(1, 2, self.x2_max)
        map_dimensions.setItem(2, 0, self.x3_dim)
        map_dimensions.setItem(2, 1, self.x3_min)
        map_dimensions.setItem(2, 2, self.x3_max)
        map_dimensions.setItem(3, 0, self.x4_dim)
        map_dimensions.setItem(3, 1, self.x4_min)
        map_dimensions.setItem(3, 2, self.x4_max)

        map_dimensions_lay = QVBoxLayout(map_dimensions_group)
        map_dimensions_lay.addWidget(map_dimensions)

        experiment_details_group = QGroupBox('Experiment details')
        exp_filename_lbl = QLabel('File name: ', self)
        self.exp_filename = QLineEdit()
        self.exp_filename.setReadOnly(True)
        exp_date_lbl = QLabel('Date: ', self)
        self.exp_date = QLabel()
        exp_duration_lbl = QLabel('Exp. duration: ', self)
        self.exp_duration = QLabel()
        exp_comment_lbl = QLabel('Comment: ', self)
        self.exp_comment = QTextEdit()
        self.exp_comment.setReadOnly(True)

        experiment_details_lay = QGridLayout(experiment_details_group)
        experiment_details_lay.addWidget(exp_filename_lbl, 0, 0)
        experiment_details_lay.addWidget(self.exp_filename, 0, 1)
        experiment_details_lay.addWidget(exp_date_lbl, 1, 0)
        experiment_details_lay.addWidget(self.exp_date, 1, 1)
        experiment_details_lay.addWidget(exp_duration_lbl, 2, 0)
        experiment_details_lay.addWidget(self.exp_duration, 2, 1)
        experiment_details_lay.addWidget(exp_comment_lbl, 5, 0)
        experiment_details_lay.addWidget(self.exp_comment, 5, 1)

        map_param_lay = QVBoxLayout(topleft_frame)
        map_param_lay.setSpacing(30)
        map_param_lay.addWidget(map_dimensions_group)
        map_param_lay.addWidget(experiment_details_group)

        # Scan controls

        scan_setup_group = QGroupBox('Map setup')
        scan_setup_table = QTableWidget(5, 4)
        scan_setup_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        scan_setup_table.setStyleSheet("border: 0")
        scan_setup_table.setHorizontalHeaderLabels(['', 'Instrument', 'Count', 'Step'])

        self.scanSetup = []
        for i in range(5):
            v_set = {
                'use': QCheckBox(),
                'instruments': QComboBox(),
                'count': QTableWidgetItem(1),
                'step': QTableWidgetItem(1)
            }
            v_set['instruments'].addItems(['-Select-', 'Mot. X', 'Mot. Y', 'Mot. Z', 'Monochromator WL'])
            self.scanSetup.append(v_set)

            scan_setup_table.setCellWidget(i, 0, v_set['use'])
            scan_setup_table.setCellWidget(i, 1, v_set['instruments'])
            scan_setup_table.setItem(i, 2, v_set['count'])
            scan_setup_table.setItem(i, 3, v_set['step'])

        scan_setup_lay = QVBoxLayout(scan_setup_group)
        scan_setup_lay.addWidget(scan_setup_table)

        scan_actions_group = QGroupBox('Actions setup')
        scan_actions_table = QTableWidget(5, 3)
        scan_actions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        scan_actions_table.setStyleSheet("border: 0")
        scan_actions_table.setHorizontalHeaderLabels(['', 'Action', 'Par.1'])

        self.scanActions = {'use': [], 'actions': [], 'Par.1': []}
        self.scanActions = []
        for i in range(5):
            a_set = {
                'use': QCheckBox(),
                'actions': QComboBox(),
                'Par.1': QTableWidgetItem()
            }
            a_set['actions'].addItems(['-Select-', 'Acquire spectra', 'Visible frame', 'Ext. measurements'])
            self.scanSetup.append(a_set)

            scan_actions_table.setCellWidget(i, 0, a_set['use'])
            scan_actions_table.setCellWidget(i, 1, a_set['actions'])
            scan_actions_table.setItem(i, 2, a_set['Par.1'])

        scan_actions_lay = QVBoxLayout(scan_actions_group)
        scan_actions_lay.addWidget(scan_actions_table)

        scan_save_group = QGroupBox('')

        self.scanDstPath = QLineEdit(QDir.currentPath(), self)
        self.scanChooseDst = QPushButton('Choose Dir')
        self.scanChooseDst.setMinimumSize(90, 30)
        self.scanDstFilename = QLineEdit(self)
        self.scanExpComment = QTextEdit(self)
        scan_path_lbl = QLabel('Directory: ')
        scan_file_lbl = QLabel('Filename: ')
        scan_comment_lbl = QLabel('Comment: ')

        scan_actions_lay = QGridLayout(scan_save_group)
        scan_actions_lay.addWidget(scan_path_lbl, 0, 0)
        scan_actions_lay.addWidget(self.scanDstPath, 0, 1)
        scan_actions_lay.addWidget(self.scanChooseDst, 0, 2)
        scan_actions_lay.addWidget(scan_file_lbl, 1, 0)
        scan_actions_lay.addWidget(self.scanDstFilename, 1, 1, 1, 2)
        scan_actions_lay.addWidget(scan_comment_lbl, 2, 0)
        scan_actions_lay.addWidget(self.scanExpComment, 2, 1, 1, 2)

        scan_ctrl_group = QFrame(self)

        scan_buttons_group = QFrame(self)
        self.scanStart = QPushButton('Start')
        self.scanPause = QPushButton('Pause')
        self.scanResume = QPushButton('Resume')
        self.scanAbort = QPushButton('Abort')
        self.scanStart.setMinimumSize(80, 30)
        self.scanPause.setMinimumSize(80, 30)
        self.scanResume.setMinimumSize(80, 30)
        self.scanAbort.setMinimumSize(80, 30)
        scan_buttons_lay = QHBoxLayout(scan_buttons_group)
        scan_buttons_lay.addWidget(self.scanStart)
        scan_buttons_lay.addWidget(self.scanPause)
        scan_buttons_lay.addWidget(self.scanResume)
        scan_buttons_lay.addWidget(self.scanAbort)

        self.scanProgress = QProgressBar(self)
        # self.scanProgress.setGeometry(0, 0, 300, 25)
        self.scanProgress.setMaximum(100)
        self.scanProgress.setValue(0)
        self.scanProgress.setStyleSheet("border: 1px solid #32414B; border-radius: 4px")

        scan_log_group = QGroupBox('Scan log')
        self.scanLog = QTextEdit(self)
        self.scanLog.setStyleSheet("border: 0")
        scan_log_lay = QVBoxLayout(scan_log_group)
        scan_log_lay.addWidget(self.scanLog)

        scan_ctrl_lay = QVBoxLayout(scan_ctrl_group)
        scan_ctrl_lay.setContentsMargins(0, 16, 0, 0)
        # scan_ctrl_lay.addSpacing(20)
        scan_ctrl_lay.addWidget(self.scanProgress)
        scan_ctrl_lay.addSpacing(10)
        scan_ctrl_lay.addWidget(scan_buttons_group)
        scan_ctrl_lay.addWidget(scan_log_group)

        scan_manage_lay = QHBoxLayout(bottom_frame)
        scan_manage_lay.setSpacing(20)
        scan_manage_lay.addWidget(scan_setup_group)
        scan_manage_lay.addWidget(scan_actions_group)
        scan_manage_lay.addWidget(scan_save_group)
        scan_manage_lay.addWidget(scan_ctrl_group)

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
