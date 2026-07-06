from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import QSize


class SkillButton(QPushButton):
    def __init__(self, skill=None, parent=None, image_path=None):
        super().__init__(parent)

        self.skill = skill
        self.selected = False
        self.image_path = image_path
        self.has_image = False

        if skill is None:
            self.setText("")
            self.setEnabled(False)
        else:
            self.setText(skill.name)

        if image_path is not None:
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                self.setIcon(QIcon(pixmap))
                self.setIconSize(QSize(90, 104))
                self.setText("")
                self.has_image = True
            else:
                print("技能按钮图片加载失败：", image_path)

        self.update_style()

    def set_selected(self, selected):
        self.selected = selected
        self.update_style()

    def update(self):
        self.update_text()
        self.update_style()
        super().update()

    def update_text(self):
        if self.skill is None:
            self.setText("")
            return

        if self.has_image:
            if self.skill.current_cd > 0:
                self.setText(f"CD:{self.skill.current_cd}")
            else:
                self.setText("")
            return

        if self.skill.current_cd > 0:
            self.setText(f"{self.skill.name}\nCD:{self.skill.current_cd}")
        else:
            self.setText(self.skill.name)

    def update_style(self):
        if self.skill is None:
            self.setStyleSheet("""
                QPushButton {
                    background-color: rgba(30, 30, 30, 120);
                    border: 2px solid rgba(120, 100, 70, 120);
                    color: #777777;
                    font-size: 14px;
                    border-radius: 8px;
                }
            """)
            return

        if self.selected:
            border_color = "#ffd75a"
            bg_color = "rgba(160, 80, 30, 90)" if self.has_image else "rgba(160, 80, 30, 230)"
        elif not self.skill.can_use():
            border_color = "#5f4a2e"
            bg_color = "rgba(50, 45, 40, 120)" if self.has_image else "rgba(50, 45, 40, 180)"
        else:
            border_color = "#d6a85f"
            bg_color = "rgba(0, 0, 0, 5)" if self.has_image else "rgba(80, 35, 20, 210)"

        self.setStyleSheet(f"""
            QPushButton {{
                color: #f5e6c8;
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: rgba(130, 55, 30, 80);
            }}

            QPushButton:pressed {{
                background-color: rgba(60, 25, 15, 120);
            }}

            QPushButton:disabled {{
                color: #7f6f55;
                background-color: rgba(50, 45, 40, 140);
                border: 2px solid #5f4a2e;
            }}
        """)