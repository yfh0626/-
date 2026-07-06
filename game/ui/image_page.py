from pathlib import Path

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap, QColor


class ImagePage(QWidget):
    def __init__(self, bg_name=None):
        super().__init__()

        self.setFixedSize(1536, 1024)

        base_dir = Path(__file__).resolve().parent.parent
        self.bg = QPixmap()

        if bg_name is not None:
            self.bg = QPixmap(str(base_dir / "assets" / "images" / bg_name))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self.bg.isNull():
            painter.drawPixmap(self.rect(), self.bg)
        else:
            painter.fillRect(self.rect(), QColor(21, 16, 12))
