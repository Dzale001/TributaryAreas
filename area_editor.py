import sys
import math
import json
from PySide6.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsView, QGraphicsEllipseItem,
    QGraphicsPolygonItem, QGraphicsSimpleTextItem, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout,
    QWidget, QSplitter, QFrame, QGroupBox
)
from PySide6.QtGui import QPolygonF, QBrush, QColor, QPen, QPainter
from PySide6.QtCore import Qt, QPointF, QRectF


class VoronoiEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tributary Areas")
        self.resize(900, 650)
        self.file_path = 1

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        splitter_group = QGroupBox("Splitter")
        splitter_layout = QVBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)

        label = QLabel("Text")

        self.left = QFrame()
        self.left_layout = QVBoxLayout(self.left)


        self.right = QFrame()
        self.right_layout = QVBoxLayout(self.right)

        if self.file_path is not None:
            label = self.renderer()
            self.left_layout.addWidget(label)
            self.right_layout.addWidget(QLabel("Text"))
        
        
        

        
        
        
        
        
        
        #label_layout.addWidget(label)

        splitter.setSizes([200,300])
        splitter.addWidget(self.left)
        splitter.addWidget(self.right)

        splitter_layout.addWidget(splitter)
        splitter_group.setLayout(splitter_layout)
        main_layout.addWidget(splitter)

    def renderer(self):
        label = QLabel("Stuff")
        return label
            



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VoronoiEditor()
    window.show()
    sys.exit(app.exec())
