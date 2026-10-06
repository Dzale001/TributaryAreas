import sys
import math
import json
from PySide6.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsView, QGraphicsEllipseItem,
    QGraphicsPolygonItem, QGraphicsSimpleTextItem, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout,
    QWidget, QSplitter, QFrame
)
from PySide6.QtGui import QPolygonF, QBrush, QColor, QPen, QPainter
from PySide6.QtCore import Qt, QPointF, QRectF


class VoronoiEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tributary Areas")
        self.resize(900, 650)
        self.file_path = None
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter_layout = QVBoxLayout()
        if self.file_path is not None:
            splitter_layout.addWidget(self.renderer())
            splitter_layout.addWidget(self.table())
        #self.setCentralWidget(main_layout)
        splitter_layout.addWidget(splitter)

    def renderer():
        label = QLabel("Stuff")
    
    def table():
        label = QLabel("More Stuff")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VoronoiEditor()
    window.show()
    sys.exit(app.exec())
