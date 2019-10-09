import sys
import qdarkstyle
from PyQt5.QtWidgets import (QApplication, QMainWindow)

from UIMain import UI
from UActions import *


class App(QMainWindow):

    def __init__(self):
        super().__init__()

        self.ui = UI(self)
        self.actions = UActions(self.ui)

        # self.setStyleSheet()

        signal.signal(signal.SIGINT, self.signal_handler)

    def closeEvent(self, event):
        self.close()

    def signal_handler(self, sig, frame):
        self.actions.shut_down()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    aw = App()

    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    aw.show()
    sys.exit(app.exec_())
