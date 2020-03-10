from PyQt5.QtWidgets import (QWidget, QTabBar)
from PyQt5.QtCore import Qt, QRectF, QLineF, QPointF, QSize

import pyqtgraph as pg


class CTabBar(QTabBar):
    def __init__(self, parent=None):
        QTabBar.__init__(self, parent)

    def tabSizeHint(self, index):
        size = QTabBar.tabSizeHint(self, index)
        w = int(self.width()/self.count())
        return QSize(w, size.height())


class CrossCursor(pg.InfiniteLine):
    def __init__(self, size=30, pos=None, pen=None, bounds=None, label=None, labelOpts=None, name=None):
        pg.InfiniteLine.__init__(self, pos, 0, pen, False, bounds, None, label, labelOpts, name)

        # self.vb = vb
        self.cursorSize = size

    def boundingRect(self):
        if self._boundingRect is None:
            # br = UIGraphicsItem.boundingRect(self)
            br = self.viewRect()
            if br is None:
                return QRectF()

            # get vertical pixel length
            self.pxv = self.pixelLength(direction=pg.Point(0, 1), ortho=False)
            if self.pxv is None:
                self.pxv = 0
            # get horizontal pixel length
            self.pxh = self.pixelLength(direction=pg.Point(1, 0), ortho=False)
            if self.pxh is None:
                self.pxh = 0

            br = br.normalized()
            self._boundingRect = br

        return self._boundingRect

    def paint(self, p, *args):
        p.setPen(self.currentPen)

        x = self.getXPos()
        y = self.getYPos()
        # print((x, y))

        h = self.cursorSize * self.pxv
        w = self.cursorSize * self.pxh

        p.drawLine(QPointF(x, y - h), QPointF(x, y + h))
        p.drawLine(QPointF(x - w, y), QPointF(x + w, y))