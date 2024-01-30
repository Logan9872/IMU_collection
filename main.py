from PyQt6.QtWidgets import QApplication, QWidget, QLabel
import sys
import skin

class skinWidget(QWidget):  # 调用主页面类
    def __init__(self):
        QWidget.__init__(self)
        self.main_ui = skin.Ui_Form()
        self.main_ui.setupUi(self)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    print("正在加载页面.....")
    w = skinWidget()
    # w.showFullScreen()
    w.show()
    print("加载完成，请连接IMU...")


    sys.exit(app.exec())
