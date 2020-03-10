import sys
from PyQt5.QtWidgets import (QApplication)

from MainWindow import AppWindow

if __name__ == '__main__':

    app = QApplication(sys.argv)
    aw = AppWindow()

    aw.show()
    sys.exit(app.exec_())
