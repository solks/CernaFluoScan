from PyQt5.QtWidgets import (QMainWindow, QDesktopWidget, QWidget, QTabWidget, QMenu, QMessageBox)
from PyQt5.QtCore import Qt
import qdarkstyle
import json

from SpectraModuleUI import SpectraModuleUI
from SpectraModuleActions import SpectraModuleActions
from ScanModuleUI import ScanModuleUI
from ScanModuleActions import ScanModuleActions
from CameraWI import CamWI
from WidgetsUI import VTabBar
from HardWareCtrl import HardWare
from AndorCtrl import AndorCCD
from CameraCtrl import Cam

class AppWindow(QMainWindow):

    storeParameters = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.paramSet = []
        if self.storeParameters:
            # read parameters from json
            with open('current-params.json', 'r') as f:
                self.paramSet = json.load(f)
        else:
            # default
            with open('default-params.json', 'r') as f:
                self.paramSet = json.load(f)

        self.hardwareConf = []
        # read parameters from json
        with open('hardware-config.json', 'r') as f:
            self.hardwareConf = json.load(f)

        self.resize(self.paramSet['windowSize']['width'], self.paramSet['windowSize']['height'])

        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.ui_construct()
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

        self.hardware = HardWare(self.hardwareConf)
        self.ccd = AndorCCD(self.hardwareConf['Andor'], self.paramSet['Andor'])

        self.actions_init()

    def ui_construct(self):
        # Main widget
        self.mainWidget = QTabWidget(self)
        self.setCentralWidget(self.mainWidget)
        # tb = CTabBar()
        # self.mainWidget.setTabBar(tb)

        # Menu items
        self.fileMenu = QMenu('&File', self)
        self.helpMenu = QMenu('&Help', self)

        # Camera control module
        self.CamCrtl = Cam()
        # Camera widget
        self.CameraSpWI = CamWI(self.CamCrtl, self.paramSet, True)
        self.CameraScWI = CamWI(self.CamCrtl, self.paramSet, False)

        # Module for spectrum acquisition
        self.spectraModuleUI = SpectraModuleUI(self.CameraSpWI, self.statusBar())
        self.spectraModuleUI.setFocus()
        # Module for scanning
        self.scanModuleUI = ScanModuleUI(self.CameraScWI, self.statusBar())
        # Module for analysis data
        self.analysisModuleUI = QWidget()

        self.setWindowTitle('CernaFluoScan')
        self.statusBar().showMessage("Cerna Fluorescence Scan Microscope control")

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.helpMenu)

        self.fileMenu.addAction('&Quit', self.file_quit, Qt.CTRL + Qt.Key_Q)
        self.helpMenu.addAction('&About', self.about)

        self.mainWidget.addTab(self.spectraModuleUI, "Spectrum Acquisition Module")
        self.mainWidget.addTab(self.scanModuleUI, "Scan Module")
        self.mainWidget.addTab(self.analysisModuleUI, "Analysis Module")

    def actions_init(self):
        self.mainWidget.currentChanged.connect(self.tab_chenge)

        self.spectraModule = SpectraModuleActions(self.spectraModuleUI, self.paramSet, self.hardware, self.ccd)
        self.spectraModuleUI.init_parameters(self.paramSet)

        self.scanModule = ScanModuleActions(self.scanModuleUI, self.paramSet, self.hardware, self.spectraModule)
        self.scanModuleUI.init_parameters(self.paramSet)

    def tab_chenge(self, idx):
        if idx == 0:
            self.CameraSpWI.set_wi_params()
            self.CameraSpWI.set_cam_controls()
            self.CameraScWI.active = False
            self.CameraSpWI.active = True
        elif idx == 1:
            self.CameraScWI.set_wi_params()
            self.CameraScWI.set_cam_controls()
            self.CameraSpWI.active = False
            self.CameraScWI.active = True
        elif idx == 2:
            self.CameraSpWI.active = False
            self.CameraScWI.active = False

    def shut_down(self):
        print('Shutting down the Andor CCD...')
        # self.ccd.shut_down()

        print('Stopping processes...')
        self.scanModule.stop_threads()
        self.CameraSpWI.shut_down()
        self.CameraScWI.shut_down()

        print('Save parameters...')
        with open('current-params.json', 'w') as f:
            json.dump(self.paramSet, f, indent=2)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', "Are you sure to quit?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.shut_down()
            event.accept()
        else:
            event.ignore()

    def file_quit(self):
        self.mainWidget.window().close()

    def about(self):
        QMessageBox.about(self.mainWidget, "About",
"""Cerna Fluorescence Scan Microscope & MDR-3
control software.

Developers:
Oleksandr Stanovyi, astanovyi@gmail.com

Source code:
https://github.com/solks/CernaFluoScan

© Copyright 2019-2021"""
                          )
