import os, base64, json

from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QCheckBox,
    QFileDialog, QMessageBox,
)
from PySide6.QtGui import QPainter, QPixmap, QPen, QBrush, QColor, QImage
from PySide6.QtCore import Qt, QRect, QPoint, Signal

from login.auth_service import AuthService
from ui.image_page import ImagePage


class _CropView(QGraphicsView):
    def __init__(self, scene, crop_size):
        super().__init__(scene)
        self.crop_size = crop_size
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setStyleSheet("background: #dcdcdc; border: none;")

    def crop_rect(self):
        w = self.viewport().width()
        h = self.viewport().height()
        r = QRect(0, 0, self.crop_size, self.crop_size)
        r.moveCenter(QPoint(w // 2, h // 2))
        return r

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        painter.save()
        painter.resetTransform()

        w = self.viewport().width()
        h = self.viewport().height()
        cr = self.crop_rect()

        dim = QColor(180, 180, 180, 140)
        painter.setBrush(QBrush(dim))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, w, cr.top())
        painter.drawRect(0, cr.bottom(), w, h - cr.bottom())
        painter.drawRect(0, cr.top(), cr.left(), cr.height())
        painter.drawRect(cr.right(), cr.top(), w - cr.right(), cr.height())

        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(cr)

        painter.restore()


class AvatarCropDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("裁剪头像 — 滚轮/+/- 缩放，拖拽移动")
        self.setMinimumSize(520, 440)

        self.orig_image = QImage(image_path)
        self.crop_size = 300

        self.scene = QGraphicsScene(self)
        self.view = _CropView(self.scene, self.crop_size)

        orig_pix = QPixmap.fromImage(self.orig_image)
        self._pw, self._ph = orig_pix.width(), orig_pix.height()

        margin = max(self._pw, self._ph) * 2
        self.scene.setSceneRect(-margin, -margin, self._pw + 2 * margin, self._ph + 2 * margin)

        self.pixmap_item = self.scene.addPixmap(orig_pix)
        self.pixmap_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.pixmap_item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.pixmap_item.setTransformOriginPoint(self._pw / 2, self._ph / 2)

        max_dim = max(self._pw, self._ph)
        init_zoom = self.crop_size / max_dim * 0.85 if max_dim > 0 else 1.0
        self.pixmap_item.setScale(init_zoom)
        self.pixmap_item.setPos(-self._pw / 2, -self._ph / 2)

        btn_confirm = QPushButton("确认裁剪")
        btn_confirm.clicked.connect(self.accept)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_confirm)
        btn_layout.addWidget(btn_cancel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        layout.addLayout(btn_layout)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta == 0:
            return
        self._zoom(1.1 if delta > 0 else 0.9)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
            self._zoom(1.1)
        elif key == Qt.Key.Key_Minus:
            self._zoom(0.9)
        else:
            super().keyPressEvent(event)

    def _zoom(self, factor):
        s = self.pixmap_item.scale()
        self.pixmap_item.setScale(max(0.05, min(s * factor, 5.0)))

    def get_cropped_image(self):
        vp_rect = self.view.crop_rect()
        scene_rect = self.view.mapToScene(vp_rect).boundingRect()
        item_rect = self.pixmap_item.mapFromScene(scene_rect).boundingRect().toRect()

        ow = self.orig_image.width()
        oh = self.orig_image.height()

        src_x = max(0, item_rect.x())
        src_y = max(0, item_rect.y())
        src_w = min(item_rect.width(), ow - src_x)
        src_h = min(item_rect.height(), oh - src_y)

        if src_w <= 0 or src_h <= 0:
            return QImage()

        cropped = self.orig_image.copy(src_x, src_y, src_w, src_h)
        return cropped.scaled(128, 128, Qt.AspectRatioMode.IgnoreAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)


class LoginPage(ImagePage):

    login_success = Signal(str)

    def __init__(self, auth_service):
        super().__init__("login_bg.png")

        self.title = QLabel("暗夜竞技场", self)
        self.title.setGeometry(578, 110, 600, 90)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("""
            QLabel {
                color: #f0d28c;
                font-size: 58px;
                font-weight: bold;
                background: transparent;
            }
        """)

        self.login_title = QLabel("登录你的账号", self)
        self.login_title.setGeometry(670, 300, 416, 55)
        self.login_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.login_title.setStyleSheet("""
            QLabel {
                color: #f5e6c8;
                font-size: 34px;
                font-weight: bold;
                background: transparent;
            }
        """)

        self.account_edit = QLineEdit(self)
        self.account_edit.setGeometry(700, 385, 356, 52)
        self.account_edit.setPlaceholderText("请输入账号")
        self.account_edit.setStyleSheet(self.input_style())

        self.password_edit = QLineEdit(self)
        self.password_edit.setGeometry(700, 460, 356, 52)
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setStyleSheet(self.input_style())

        self.remember_check = QCheckBox("记住我", self)
        self.remember_check.setGeometry(700, 530, 140, 32)
        self.remember_check.setStyleSheet("""
            QCheckBox {
                color: #f5e6c8;
                font-size: 18px;
                background: transparent;
            }
        """)

        self.login_button = QPushButton("登录", self)
        self.login_button.setGeometry(700, 590, 356, 64)
        self.login_button.setStyleSheet(self.main_button_style())
        self.login_button.clicked.connect(self.handle_login)

        self.register_button = QPushButton("注册账号", self)
        self.register_button.setGeometry(760, 670, 236, 42)
        self.register_button.setStyleSheet(self.secondary_button_style())

        self.register_button.clicked.connect(self.handle_register)
        self.auth = auth_service
        self.load_user_data()

    def input_style(self):
        return """
            QLineEdit {
                color: #f5e6c8;
                background-color: rgba(0, 0, 0, 130);
                border: 2px solid #8f6a36;
                border-radius: 8px;
                font-size: 20px;
                padding-left: 14px;
            }

            QLineEdit:focus {
                border: 2px solid #d6a85f;
            }
        """

    def main_button_style(self):
        return """
            QPushButton {
                color: #f5e6c8;
                background-color: rgba(130, 30, 20, 230);
                border: 2px solid #d6a85f;
                border-radius: 10px;
                font-size: 30px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: rgba(170, 45, 28, 240);
            }

            QPushButton:pressed {
                background-color: rgba(80, 18, 12, 240);
            }
        """

    def secondary_button_style(self):
        return """
            QPushButton {
                color: #f0d28c;
                background-color: rgba(0, 0, 0, 80);
                border: 1px solid #8f6a36;
                border-radius: 8px;
                font-size: 20px;
                font-weight: bold;
            }

            QPushButton:hover {
                border: 1px solid #d6a85f;
                color: #ffffff;
            }
        """

    def load_user_data(self):
        db = self.auth.load_db()
        last_user = db.get("remember_me")
        if last_user and last_user in db["users"]:
            self.account_edit.setText(last_user)
            user_data = db["users"][last_user]
            try:
                self.password_edit.setText(self.auth.fernet.decrypt(user_data["encrypted_pass"].encode()).decode())
                self.remember_check.setChecked(True)
            except:
                pass

    def handle_login(self):
        db = self.auth.load_db()
        user = self.account_edit.text()
        pwd = self.password_edit.text()

        if user in db["users"]:
            data = db["users"][user]
            if self.auth.verify_password(pwd, base64.b64decode(data["hash"]), base64.b64decode(data["salt"])):
                db["remember_me"] = user if self.remember_check.isChecked() else None
                with open(self.auth.DB_PATH, "w") as f:
                    json.dump(db, f)
                self.login_success.emit(user)
            else:
                QMessageBox.critical(self, "错误", "密码错误")

    def handle_register(self):
        username = self.account_edit.text().strip()
        password = self.password_edit.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "注册失败", "账号和密码不能为空！")
            return

        db = self.auth.load_db()
        if username in db["users"]:
            QMessageBox.warning(self, "注册失败", "该账号已存在，请尝试登录。")
            return

        avatar_path, _ = QFileDialog.getOpenFileName(
            self, "请选择头像", "", "Images (*.png *.jpg *.jpeg)"
        )

        if not avatar_path:
            return

        crop_dlg = AvatarCropDialog(avatar_path, self)
        if not crop_dlg.exec():
            return

        try:
            avatar_dest = f"login/avatars/{username}.png"
            os.makedirs("login/avatars", exist_ok=True)

            scaled_img = crop_dlg.get_cropped_image()
            if scaled_img.isNull():
                QMessageBox.critical(self, "错误", "裁剪失败，请重试。")
                return
            scaled_img.save(avatar_dest)

            self.auth.save_user(username, password, avatar_dest)

            QMessageBox.information(self, "注册成功", f"欢迎你，{username}！现在可以登录了。")

        except Exception as e:
            QMessageBox.critical(self, "系统错误", f"注册过程中出错: {str(e)}")
