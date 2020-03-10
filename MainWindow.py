from PyQt5.QtWidgets import (QMainWindow, QDesktopWidget, QWidget, QTabWidget, QMenu, QMessageBox)
from PyQt5.QtCore import Qt
import qdarkstyle

from SpectraModuleUI import SpectraModuleUI
from SpectraModuleCtrl import SpectraModuleCtrl
from ScanModuleUI import ScanModuleUI
from WidgetsUI import CTabBar


class AppWindow(QMainWindow):

    W_HEIGHT = 960
    W_WIDTH = 1440

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.resize(self.W_WIDTH, self.W_HEIGHT)

        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

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
        self.spectraActions = SpectraModuleCtrl(self.spectraModule)

        self.mainWidget.addTab(self.scanModule, "Scan Module")
        # self.scanActions = ScanModuleCtrl(self.scanModule)

        self.mainWidget.addTab(self.analysisModule, "Analysis Module")

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', "Are you sure to quit?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.spectraActions.shut_down()
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
