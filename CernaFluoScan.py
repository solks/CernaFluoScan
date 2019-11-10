import sys
import qdarkstyle
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMessageBox)

from UIMain import UI
from UActions import *

import time


class App(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ui = UI(self)
        self.actions = UActions(self.ui)

        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.actions.shut_down()
            event.accept()
        else:
            event.ignore()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    aw = App()

    aw.show()
    sys.exit(app.exec_())
