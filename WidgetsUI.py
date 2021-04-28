from PyQt5.QtWidgets import (QWidget, QTabBar, QSizePolicy)
from PyQt5.QtCore import Qt, QRectF, QLineF, QPointF, QSize

import pyqtgraph as pg


class VTabBar(QTabBar):
    def __init__(self, parent=None):
        QTabBar.__init__(self, parent)

    def tabSizeHint(self, index):
        size = QTabBar.tabSizeHint(self, index)
        h = int(self.height()/2)
        return QSize(size.width(), h)


class PgGraphicsView(pg.GraphicsView):
    def __init__(self, parent=None, aspect_locked=True):
        super().__init__(parent, useOpenGL=False, background=pg.mkColor('#29353D'))

        pg.setConfigOptions(imageAxisOrder='row-major')

        self.vb = pg.ViewBox()
        self.setCentralItem(self.vb)

        self.image = pg.ImageItem()
        self.vb.addItem(self.image)

        self.init_ui(aspect_locked)

    def init_ui(self, asp_lock):
        self.vb.setMenuEnabled(True)
        self.vb.setAspectLocked(asp_lock)
        self.vb.enableAutoRange()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


class PgPlotWidget(pg.PlotWidget):
    def __init__(self, parent=None, w='row'):
        super().__init__(parent, background=pg.mkColor('#29353D'))

        self.curve = self.plot(pen='y')
        self.vb = self.plotItem.getViewBox()

        self.init_ui(w)

    def init_ui(self, w):
        self.showGrid(x=True, y=True)
        self.setMouseTracking(True)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if w == 'row':
            self.plotItem.setContentsMargins(0, 20, 20, 0)
            self.plotItem.showAxis('top', True)
            self.plotItem.showAxis('right', True)
            self.plotItem.getAxis('top').setStyle(showValues=False)
            self.plotItem.getAxis('right').setStyle(showValues=False)

        else:
            self.plotItem.setContentsMargins(10, 8, 0, 10)
            self.plotItem.showAxis('top', True)
            self.plotItem.showAxis('right', True)
            self.plotItem.getAxis('top').setStyle(showValues=False)
            self.plotItem.getAxis('left').setStyle(showValues=False)
            self.plotItem.getAxis('bottom').setStyle(showValues=False)
            self.plotItem.getViewBox().invertX(True)


class CrossLine(pg.InfiniteLine):
    def __init__(self,  angle=0, bounds=(0, 1)):

        pen = pg.mkPen(color=pg.mkColor('#C8C86466'), width=1)
        hover_pen = pg.mkPen(color=pg.mkColor('#FF000077'), width=1)

        super().__init__(angle=angle, pen=pen, hoverPen=hover_pen, movable=True, bounds=bounds)



class CrossCursor(pg.InfiniteLine):
    def __init__(self, size=30, pos=None, bounds=None, label=None, labelOpts=None, name=None):
        pg.InfiniteLine.__init__(self, pos, 0, pg.mkColor('#C8C86477'), False, bounds, None, label, labelOpts, name)

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