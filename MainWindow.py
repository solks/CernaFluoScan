from PyQt5.QtWidgets import (QMainWindow, QDesktopWidget, QWidget, QTabWidget, QMenu, QMessageBox)
from PyQt5.QtCore import Qt
import qdarkstyle
import json

from SpectraModuleUI import SpectraModuleUI
from SpectraModuleCtrl import SpectraModuleCtrl
from ScanModuleUI import ScanModuleUI
from ScanModuleCtrl import ScanModuleCtrl
from WidgetsUI import CTabBar
from HardWare import HardWare
from AndorCCD import AndorCCD

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
        self.ccd = AndorCCD(self.paramSet['Andor'])

        self.ctrl_init()

    def ui_construct(self):
        # Main widget
        self.mainWidget = QTabWidget(self)
        self.setCentralWidget(self.mainWidget)
        # tb = CTabBar()
        # self.mainWidget.setTabBar(tb)

        # Menu items
        self.fileMenu = QMenu('&File', self)
        self.helpMenu = QMenu('&Help', self)

        # Module for spectrum acquisition
        self.spectraModule = SpectraModuleUI()
        self.spectraModule.setFocus()
        # Module for scanning
        self.scanModule = ScanModuleUI()
        # Module for analysis data
        self.analysisModule = QWidget()

        self.setWindowTitle('CernaFluoScan')
        self.statusBar().showMessage("Cerna Fluorescence Scan Microscope control")

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.helpMenu)

        self.fileMenu.addAction('&Quit', self.file_quit, Qt.CTRL + Qt.Key_Q)
        self.helpMenu.addAction('&About', self.about)

        self.mainWidget.addTab(self.spectraModule, "Spectrum Acquisition Module")
        self.mainWidget.addTab(self.scanModule, "Scan Module")
        self.mainWidget.addTab(self.analysisModule, "Analysis Module")

    def ctrl_init(self):
        self.spectraActions = SpectraModuleCtrl(self.spectraModule, self.paramSet, self.hardware, self.ccd)
        self.spectraModule.init_parameters(self.paramSet)

        self.scanActions = ScanModuleCtrl(self.scanModule, self.paramSet, self.hardware, self.ccd)
        self.scanModule.init_parameters(self.paramSet)

    def shut_down(self):
        print('Shutting down the Andor CCD...')
        # self.ccd.shut_down()

        print('Stopping processes...')
        self.scanActions.stop_threads()

        print('Save parameters...')
        with open('current-params.json', 'w') as f:
            json.dump(self.paramSet, f, indent=4)

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

© Copyright 2019"""
                          )
