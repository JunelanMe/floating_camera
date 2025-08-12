import sys
import cv2
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets


class FloatingCamera(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        # 设置窗口属性：无边框、始终置顶、工具窗口
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint |
                            QtCore.Qt.WindowStaysOnTopHint |
                            QtCore.Qt.Tool)
        # 设置窗口背景透明
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # 初始化摄像头
        self.cap = cv2.VideoCapture(0)
        # 创建定时器，用于更新摄像头画面
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 每30毫秒更新一次画面

        # 用于窗口拖动的变量
        self.drag_pos = None
        # 设置窗口初始大小
        self.resize(220, 220)

        # 创建显示摄像头画面的标签
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(0, 0, 200, 200)

        # 创建关闭按钮
        self.close_btn = QtWidgets.QPushButton("×", self)
        self.close_btn.setGeometry(190, -5, 30, 30)
        # 设置关闭按钮样式
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: red;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: darkred;
            }
        """)
        self.close_btn.setCursor(QtCore.Qt.PointingHandCursor)  # 设置鼠标悬停样式
        self.close_btn.clicked.connect(self.close)  # 绑定点击事件
        self.close_btn.setVisible(False)  # 默认隐藏关闭按钮

    def update_frame(self):
        """更新摄像头画面"""
        ret, frame = self.cap.read()
        if not ret:
            return

        # 转换颜色空间BGR->RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # 水平翻转画面（镜像效果）
        frame = cv2.flip(frame, 1)

        # 裁剪为正方形
        h, w, _ = frame.shape
        size = min(w, h)

        # 修改这里：让裁剪区域偏左
        # 原代码是 frame[0:size, 0:size] 从左上角开始裁剪
        # 新代码让x轴起始位置向右偏移，这样裁剪区域就会偏左
        x_offset = int(size * 0.2)  # 向右偏移20%的宽度，这样裁剪区域看起来就是偏左的
        frame = frame[0:size, x_offset:x_offset+size]  # 修改后的裁剪区域

        # 创建RGBA图像（带透明度通道）
        rgba = np.zeros((size, size, 4), dtype=np.uint8)
        rgba[:, :, :3] = frame  # 填充RGB通道

        # 创建圆形遮罩
        mask = np.zeros((size, size), dtype=np.uint8)
        cv2.circle(mask, (size // 2, size // 2), size // 2, 255, -1)
        rgba[:, :, 3] = mask  # 设置Alpha通道

        # 将numpy数组转换为Qt图像
        qimg = QtGui.QImage(rgba.data, size, size, 4 * size, QtGui.QImage.Format_RGBA8888)
        # 转换为QPixmap并缩放
        pixmap = QtGui.QPixmap.fromImage(qimg).scaled(self.label.width(), self.label.height(),
                                                    QtCore.Qt.KeepAspectRatio,
                                                    QtCore.Qt.SmoothTransformation)
        self.label.setPixmap(pixmap)  # 显示图像

    def enterEvent(self, event):
        """鼠标进入窗口时显示关闭按钮"""
        self.close_btn.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开窗口时隐藏关闭按钮"""
        self.close_btn.setVisible(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """鼠标按下事件，用于拖动窗口"""
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动事件，用于拖动窗口"""
        if self.drag_pos and event.buttons() & QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件，结束拖动"""
        self.drag_pos = None

    def closeEvent(self, event):
        """窗口关闭事件，释放摄像头并退出程序"""
        self.cap.release()
        QtWidgets.QApplication.quit()
        event.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = FloatingCamera()
    win.show()
    sys.exit(app.exec_())