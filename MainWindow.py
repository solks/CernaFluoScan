from PyQt5.QtWidgets import (QMainWindow, QDesktopWidget, QWidget, QTabWidget, QMenu, QMessageBox)
from PyQt5.QtCore import Qt
import qdarkstyle
import json

from SpectraModule import SpectraModule
from ScanModule import ScanModule
from CameraWI import CamWI
from WidgetsUI import VTabBar
from HardWareController import HardWare
from AndorController import AndorCCD
from CameraController import Cam


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

        self.hardware = HardWare(self.hardwareConf)
        self.ccd = AndorCCD(self.hardwareConf['Andor'], self.paramSet['Andor'])

        self.ui_construct()
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    def ui_construct(self):
        # Main widget
        self.mainWidget = QTabWidget(self)
        self.setCentralWidget(self.mainWidget)
        # tb = CTabBar()
        # self.mainWidget.setTabBar(tb)

        # Menu items
        self.fileMenu = QMenu('&File', self)
        self.helpMenu = QMenu('&Help', self)

        self.setWindowTitle('CernaFluoScan')
        self.statusBar().showMessage("Cerna Fluorescence Scan Microscope control")

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.helpMenu)

        self.fileMenu.addAction('&Quit', self.file_quit, Qt.CTRL + Qt.Key_Q)
        self.helpMenu.addAction('&About', self.about)

        # Camera control module
        self.CamCtrl = Cam()
        # Camera widget
        self.CameraSpWI = CamWI(self.CamCtrl, self.paramSet, True)
        self.CameraScWI = CamWI(self.CamCtrl, self.paramSet, False)

        # Module for spectrum acquisition
        # self.spectraModuleUI = SpectraModuleUI(self.CameraSpWI, self.hardwareConf['Andor'])
        # self.spectraModuleUI.setFocus()
        # Module for scanning
        # self.scanModuleUI = ScanModuleUI(self.CameraScWI, self.statusBar())
        # Module for analysis data

        self.spectraModule = SpectraModule(self.CameraSpWI, self.ccd, self.hardware, self.hardwareConf['Andor'],
                                           self.paramSet, self.statusBar())
        self.spectraModule.setFocus()

        self.scanModule = ScanModule(self.CameraScWI, self.spectraModule, self.hardware, self.paramSet, self.statusBar())

        self.analysisModule = QWidget()

        self.mainWidget.currentChanged.connect(self.tab_chenge)

        self.mainWidget.addTab(self.spectraModule, "Spectrum Acquisition Module")
        self.mainWidget.addTab(self.scanModule, "Scan Module")
        self.mainWidget.addTab(self.analysisModule, "Analysis Module")

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
        print('Save parameters...')
        with open('current-params.json', 'w') as f:
            json.dump(self.paramSet, f, indent=2)

        print('Stopping processes...')
        self.scanModule.stop_threads()
        self.spectraModule.stop_threads()
        self.CameraScWI.shut_down()

        print('Shutting down HardWare...')
        self.hardware.shut_down()

        print('Shutting down the Andor CCD...')
        self.CameraSpWI.shut_down()
        self.ccd.shut_down()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Confirm close', "Are you sure you want to close?",
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
Vladimir Stolyarevsky

Source code:
https://github.com/solks/CernaFluoScan

© Copyright 2019-2021"""
                          )
