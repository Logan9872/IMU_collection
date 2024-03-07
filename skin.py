import datetime
import os
from datetime import datetime, timedelta
from PyQt6.QtCharts import QChartView, QChart, QLineSeries, QValueAxis, QScatterSeries, QDateTimeAxis, QLegend
from PyQt6 import QtCore, QtGui, QtWidgets,Qt6
from PyQt6.QtCore import QPointF, QTimer, Qt, QDateTime, QMargins
from PyQt6.QtGui import QFont, QColor, QPen
from PyQt6.QtWidgets import QVBoxLayout, QGraphicsTextItem
from multiprocessing import Process

import read_imu2
import read_imu3
import ECG_Model


# Windows线程优先级常量
THREAD_PRIORITY_LOWEST = -2
THREAD_PRIORITY_BELOW_NORMAL = -1
THREAD_PRIORITY_NORMAL = 0
THREAD_PRIORITY_ABOVE_NORMAL = 1
THREAD_PRIORITY_HIGHEST = 2

class Ui_Form(object):

    def __init__(self):
        self.connected1 = False
        self.connected2 = False
        self.connected3 = False
        self.current_hr_data = 60

        # self.current_imu_data1 = None
        # self.current_imu_data2 = None
        # self.current_imu_data3 = None


    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(1200, 900)
        Form.setStyleSheet("QPushButton {\n"
                           "    background-color: rgb(255, 0, 0);\n"
                           "    color: rgb(255, 255, 255);\n"
                           "    border-radius: 10px;\n"
                           "}")
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.widget_2 = QtWidgets.QWidget(parent=Form)
        self.widget_2.setObjectName("widget_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.widget_2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.widget_4 = QtWidgets.QWidget(parent=self.widget_2)
        self.widget_4.setObjectName("widget_4")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.widget_4)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.function_widget_1 = QtWidgets.QWidget(parent=self.widget_4)
        # -----
        self.hrLabel = QtWidgets.QLabel(Form)
        self.hrLabel.setObjectName("hrLabel")
        self.hrLabel.setText("心率: 0 bpm")
        self.hrLabel.setFont(QtGui.QFont('Arial', 15))
        self.hrLabel.setStyleSheet("color:#FF4136")  # 将文本颜色设置为红色
        self.hrLabel.setFixedSize(150, 40)  # 调整大小以适应文本
        # 假设已知窗体的宽度，这里以1200为例
        form_width = 1200  # 假设或从Form.width()获取
        # 标签的x位置是窗体宽度减去标签宽度和一些边距
        label_x = form_width - self.hrLabel.width() - 0  # 右边留出10px边距
        # 设置标签的y位置为窗体顶部边缘
        label_y = 0  # 顶部留出10px边距，可根据需要调整
        self.hrLabel.move(label_x, label_y)
        self.hrLabel.raise_()  # 确保标签显示在其他组件之上
        # _____
        self.function_widget_1.setObjectName("function_widget_1")
        self.verticalLayout_2.addWidget(self.function_widget_1)
        self.function_widget_2 = QtWidgets.QWidget(parent=self.widget_4)
        self.function_widget_2.setObjectName("function_widget_2")
        self.verticalLayout_2.addWidget(self.function_widget_2)
        self.function_widget_3 = QtWidgets.QWidget(parent=self.widget_4)
        self.function_widget_3.setObjectName("function_widget_3")
        self.verticalLayout_2.addWidget(self.function_widget_3)
        self.horizontalLayout_2.addWidget(self.widget_4)
        self.horizontalLayout_2.setStretch(0, 2)
        self.verticalLayout.addWidget(self.widget_2)
        self.widget = QtWidgets.QWidget(parent=Form)
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(500, 10, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.function_widget_1.setMinimumSize(400, 280)  # 设置更大的最小尺寸
        self.function_widget_2.setMinimumSize(400, 280)  # 设置更大的最小尺寸
        self.function_widget_3.setMinimumSize(400, 280)  # 设置更大的最小尺寸
        self.widget_4.setMinimumSize(0, 20)  # 设置更大的最小尺寸


        # ------
        self.start_btn = QtWidgets.QPushButton(parent=self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.start_btn.sizePolicy().hasHeightForWidth())
        self.start_btn.setSizePolicy(sizePolicy)
        self.start_btn.setMinimumSize(QtCore.QSize(50, 40))
        self.start_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.start_btn.setStyleSheet("")
        self.start_btn.setObjectName("start_btn")
        self.horizontalLayout.addWidget(self.start_btn)
        # ------
        self.stop_btn = QtWidgets.QPushButton(parent=self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stop_btn.sizePolicy().hasHeightForWidth())
        self.stop_btn.setSizePolicy(sizePolicy)
        self.stop_btn.setMinimumSize(QtCore.QSize(50, 40))
        self.stop_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.stop_btn.setStyleSheet("")
        self.stop_btn.setObjectName("stop_btn")
        self.horizontalLayout.addWidget(self.stop_btn)
        # -----
        self.connect_btn = QtWidgets.QPushButton(parent=self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.connect_btn.sizePolicy().hasHeightForWidth())
        self.connect_btn.setSizePolicy(sizePolicy)
        self.connect_btn.setMinimumSize(QtCore.QSize(50, 40))
        self.connect_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.connect_btn.setStyleSheet("")
        self.connect_btn.setObjectName("connect_btn")
        self.horizontalLayout.addWidget(self.connect_btn)
        # -----
        self.verticalLayout.addWidget(self.widget)
        self.verticalLayout.setStretch(0, 15)
        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

        # 绑定点击事件
        self.start_btn.clicked.connect(lambda: self.start_btn_clicked())  # type: ignore
        self.connect_btn.clicked.connect(lambda: self.connect_btn_clicked())  # type: ignore
        self.stop_btn.clicked.connect(lambda: self.stop_btn_clicked())  # type: ignore

        # ----------------------
        self.init_charts()
        # 读取数据
        # 尝试连接第二个IMU

        self.thread2 = read_imu2.IMUThread(priority=THREAD_PRIORITY_HIGHEST)
        # 尝试连接第二个IMU
        self.thread3 = read_imu3.IMUThread(priority=THREAD_PRIORITY_HIGHEST)

        # ----ecg process-------
        self.ECGthread = ECG_Model.ECGThread("Polar H10 B606F424")
        self.ECGthread.ECGSignals.connect(self.get_data4)
        self.ECGthread.HRSignals.connect(self.get_data1)
        # ----ecg process-------

        self.thread2.data_signal2.connect(self.get_data2)
        self.thread3.data_signal3.connect(self.get_data3)

        # # 定时器

        self.timer2 = QTimer()
        self.timer2.setInterval(100)  # 定时器间隔为1000毫秒

        self.timer3 = QTimer()
        self.timer3.setInterval(100)  # 定时器间隔为1000毫秒

        # self.timer4 = QTimer()
        # self.timer4.setInterval(1000)  # 定时器间隔为1000毫秒

        self.timer2.timeout.connect(self.update_data2)  #
        self.timer3.timeout.connect(self.update_data3)  #
        # self.timer4.timeout.connect(self.update_data4)  #


    def get_data2(self, imu_dat):
        # 保存数据以供定时器使用
        self.current_imu_data2 = imu_dat
        # print("data2", self.current_imu_data2)

    def get_data3(self, imu_dat):
        # 保存数据以供定时器使用
        self.current_imu_data3 = imu_dat
        # print("data3", self.current_imu_data3)

    def get_data4(self, ecg_data):
        # 保存数据以供定时器使用
        self.current_ecg_data = ecg_data
        self.update_chart1(ecg_data)
        # print("get",self.current_ecg_data)

    def get_data1(self, hr_data):
        # 保存数据以供定时器使用
        self.current_hr_data = hr_data
        self.hrLabel.setText(f"心率: {self.current_hr_data} bpm")
        # print("get", self.current_hr_data)


    def update_data2(self):
        if hasattr(self, 'current_imu_data2'):
            aX2 = self.current_imu_data2[3]
            aY2 = self.current_imu_data2[4]
            aZ2 = self.current_imu_data2[5]

            self.update_chart2(aX2, aY2, aZ2 )
        else:
            pass

    def update_data3(self):
        if hasattr(self, 'current_imu_data3'):
            aX3 = self.current_imu_data3[3]
            aY3 = self.current_imu_data3[4]
            aZ3 = self.current_imu_data3[5]
            self.update_chart3( aX3, aY3, aZ3)
        else:
            pass

    # -----
    def update_data4(self):
        if hasattr(self, 'current_ecg_data'):
            ecg = self.current_ecg_data
            self.update_chart1(ecg)
            # print("up",ecg)
        else:
            pass
    # -----

    def init_charts(self):
        self.chart, self.x_axis1,self.y_axis1, self.series_ax = (
            self.create_chart_ecg("ECG心电信号",-800,800,True))
        self.chart2,self.x_axis2,self.y_axis2, self.series_gx, self.series_gy, self.series_gz = (
            self.create_chart("IMU_1_加速度",-100,100,True))
        self.chart3,self.x_axis3,self.y_axis3, self.series_cx, self.series_cy, self.series_cz = (
            self.create_chart("IMU_2_加速度",-100,100,True))

        self.chartView = QChartView(self.chart)
        self.chartView2 = QChartView(self.chart2)
        self.chartView3 = QChartView(self.chart3)

        layout1 = QVBoxLayout(self.function_widget_1)
        layout1.addWidget(self.chartView)
        layout2 = QVBoxLayout(self.function_widget_2)
        layout2.addWidget(self.chartView2)
        layout3 = QVBoxLayout(self.function_widget_3)
        layout3.addWidget(self.chartView3)

    def create_chart(self, title, xSet, ySet, show):

        titleFont = QFont("Arial", 14)  # 设置图表标题的字体和大小
        labelFontX = QFont("Arial", 8)  # 设置坐标轴标签的字体和大小
        labelFontY = QFont("Arial", 8)  # 设置坐标轴标签的字体和大小
        legendFont = QFont("Arial",8)

        chart = QChart()
        chart.setTitleFont(titleFont)
        chart.setTitle(title)
        chart.legend().setVisible(show)
        chart.legend().setFont(legendFont)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)


        # 创建和添加X轴和Y轴
        x_axis = QDateTimeAxis()
        x_axis.setFormat("hh:mm:ss")
        # x_axis.setTitleText("Time")
        x_axis.setLabelsFont(labelFontX)  # 应用字体到X轴标签
        y_axis = QValueAxis()
        y_axis.setLabelsFont(labelFontY)  # 应用字体到Y轴标签
        y_axis.setRange(xSet, ySet)

        x_axis.setTickCount(6)
        y_axis.setTickCount(5)
        y_axis.setMinorTickCount(2)

        chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)
        chart.setMargins(QMargins(5, 5, 0, 20))  # 设置边距

        # 创建折线序列并添加到图表
        series_ax = QLineSeries()
        series_ay = QLineSeries()
        series_az = QLineSeries()

        # 设置X轴数据序列的颜色
        x_color = QColor("#007FFF")  # 例如，设置为蓝色
        series_ax.setPen(QPen(x_color, 3))  # 第二个参数是线条宽度

        y_color = QColor("#00BF00")  # 例如，设置为绿色
        series_ay.setPen(QPen(y_color, 3))  # 第二个参数是线条宽度

        z_color = QColor("#FFA500")  # 例如，设置为黄
        series_az.setPen(QPen(z_color, 3))  # 第二个参数是线条宽度

        series_ax.setName("X")
        series_ay.setName("Y")
        series_az.setName("Z")
        chart.addSeries(series_ax)
        chart.addSeries(series_ay)
        chart.addSeries(series_az)

        # 将序列关联到坐标轴
        series_ax.attachAxis(x_axis)
        series_ax.attachAxis(y_axis)
        series_ay.attachAxis(x_axis)
        series_ay.attachAxis(y_axis)
        series_az.attachAxis(x_axis)
        series_az.attachAxis(y_axis)
        return chart, x_axis, y_axis, series_ax, series_ay, series_az

    def create_chart_ecg(self, title, xSet, ySet, show):

        titleFont = QFont("Arial", 14)  # 设置图表标题的字体和大小
        labelFontX = QFont("Arial", 8)  # 设置坐标轴标签的字体和大小
        labelFontY = QFont("Arial", 8)  # 设置坐标轴标签的字体和大小
        legendFont = QFont("Arial", 8)

        chart = QChart()
        chart.setTitleFont(titleFont)
        chart.setTitle(title)
        chart.legend().setVisible(show)
        chart.legend().setFont(legendFont)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)

        # 创建和添加X轴和Y轴
        x_axis = QDateTimeAxis()
        x_axis.setFormat("hh:mm:ss")
        # x_axis.setTitleText("Time")
        x_axis.setLabelsFont(labelFontX)  # 应用字体到X轴标签
        y_axis = QValueAxis()
        y_axis.setLabelsFont(labelFontY)  # 应用字体到Y轴标签
        y_axis.setRange(xSet, ySet)

        x_axis.setTickCount(6)
        y_axis.setTickCount(5)
        y_axis.setMinorTickCount(2)

        chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)
        chart.setMargins(QMargins(5, 5, 0, 20))  # 设置边距

        # 创建折线序列并添加到图表
        series_ax = QLineSeries()

        # 启用抗锯齿以使线条更平滑

        # 设置X轴数据序列的颜色
        x_color = QColor("#FF4136")  # 例如，设置为红色
        series_ax.setPen(QPen(x_color, 3))  # 第二个参数是线条宽度
        series_ax.setName("ECG")
        chart.addSeries(series_ax)

        # 将序列关联到坐标轴
        series_ax.attachAxis(x_axis)
        series_ax.attachAxis(y_axis)

        return chart, x_axis, y_axis, series_ax

    def update_chart1(self, ecg):
        now = QDateTime.currentDateTime()
        now_msecs = now.toMSecsSinceEpoch()

        # 更新1数据
        self.series_ax.append(now_msecs, ecg)
        # 更新X轴范围
        two_minutes_ago = now.addSecs(-3).toMSecsSinceEpoch()
        self.x_axis1.setRange(QDateTime.fromMSecsSinceEpoch(two_minutes_ago), now)

        # 限制显示数据点数量
        max_points = 2000   # 假设最多显示100个数据点
        count = self.series_ax.count()
        # print(count)
        if count > max_points:
            self.series_ax.remove(0)

        # 动态更新X轴的范围以显示最近2分钟的数据
        self.chartView.update()

# ------
    def update_chart2(self, aX2, aY2, aZ2):
        now = QDateTime.currentDateTime()
        now_msecs = now.toMSecsSinceEpoch()

        # # -----
        # self.series_ax.append(now_msecs, GX2)
        # self.series_ay.append(now_msecs, GY2)
        # self.series_az.append(now_msecs, GZ2)
        # # -----

        # 更新2数据
        self.series_gx.append(now_msecs, aX2)
        self.series_gy.append(now_msecs, aY2)
        self.series_gz.append(now_msecs, aZ2)

        # 更新X轴范围
        two_minutes_ago = now.addSecs(-30).toMSecsSinceEpoch()
        self.x_axis2.setRange(QDateTime.fromMSecsSinceEpoch(two_minutes_ago), now)

        # 限制显示数据点数量
        max_points = 1000  # 假设最多显示100个数据点
        count = self.series_gx.count()
        # print(count)
        if count > max_points:
            self.series_gx.remove(0)
            self.series_gy.remove(0)
            self.series_gz.remove(0)
        # 动态更新X轴的范围以显示最近2分钟的数据
        self.chartView2.update()
# ------
    def update_chart3(self, aX3, aY3, aZ3):
        now = QDateTime.currentDateTime()
        now_msecs = now.toMSecsSinceEpoch()

        # 更新3数据
        self.series_cx.append(now_msecs, aX3)
        self.series_cy.append(now_msecs, aY3)
        self.series_cz.append(now_msecs, aZ3)

        # 更新X轴范围
        two_minutes_ago = now.addSecs(-30).toMSecsSinceEpoch()

        self.x_axis3.setRange(QDateTime.fromMSecsSinceEpoch(two_minutes_ago), now)

        # 限制显示数据点数量
        max_points = 1000  # 假设最多显示100个数据点
        count = self.series_cx.count()
        # print(count)
        if count > max_points:

            self.series_cx.remove(0)
            self.series_cy.remove(0)
            self.series_cz.remove(0)

        # 动态更新X轴的范围以显示最近2分钟的数据
        self.chartView3.update()

# ------
    def connect_btn_clicked(self):
        # ---
        if not self.ECGthread.isRunning():
            self.ECGthread.start()  # 启动线程
            self.connected1 = True
        # ---
        if not self.thread2.isRunning():
            self.thread2.start()  # 启动线程2
            self.connected2 = True

        if not self.thread3.isRunning():
            self.thread3.start()  # 启动线程3
            self.connected3 = True

        self.timer2.start()  # 启动定时器
        self.timer3.start()  # 启动定时器
    def stop_btn_clicked(self):
        if self.connected1:
            print("stop1")
            self.timer4.stop()  # 启动定时器
            # 停止数据上报
            self.ECGthread.stop_hr_stream()
            self.ECGthread.stop_ecg_stream()
        else:
            print("设备1未连接，请连接Polar设备...")

        if self.connected2:
            print("stop1")
            self.timer2.stop()  # 启动定时器
            # 停止数据上报
            data = bytes([0x18])
            self.thread2.send_data_to_device(data)
            self.thread2.initTimeSet = False
        else:
            print("设备1未连接，请连接IMU设备...")

        if self.connected3:
            print("stop3")
            self.timer3.stop()  # 启动定时器
            # 停止数据上报
            data = bytes([0x18])
            self.thread3.send_data_to_device(data)
            self.thread3.initTimeSet = False
        else:
            print("设备3未连接，请连接IMU设备...")

    def start_btn_clicked(self):

        if self.connected1:
            print("start1")
            self.clear_chart_data()
            # self.timer.start()  # 启动定时器
            data = bytes([0x19])
            self.ECGthread.send_data_to_device(data)

            start_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join('IMU_Data2', f'IMU_Data2_{start_time}.csv')
            self.ECGthread.start_hr_stream()
            self.ECGthread.start_ecg_stream()
        else:
            print("设备未连接，请连接Polar设备...")

        if self.connected2:
            print("start1")
            self.clear_chart_data()
            self.timer2.start()  # 启动定时器
            # 开始数据上报
            data = bytes([0x19])
            self.thread2.send_data_to_device(data)
            start_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path2 = os.path.join('IMU_Data5', f'IMU_Data5_{start_time}.csv')
            self.thread2.set_file_path(file_path2)
            self.thread2.initTimeSet = False
        else:
            print("设备1未连接，请连接IMU设备...")

        if self.connected3:
            print("start3")
            self.clear_chart_data()
            self.timer3.start()  # 启动定时器
            # 开始数据上报
            data = bytes([0x19])
            self.thread3.send_data_to_device(data)
            start_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path3 = os.path.join('IMU_Data6', f'IMU_Data6_{start_time}.csv')
            self.thread3.set_file_path(file_path3)
            self.thread3.initTimeSet = False

        else:print("设备3未连接，请连接IMU设备...")
    # 清空图表
    def clear_chart_data(self):
        # 清空每个序列中的所有数据点
        for chart in [self.chart, self.chart2, self.chart3]:
            for series in chart.series():
                series.clear()

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "IMU_Form"))
        self.start_btn.setText(_translate("Form", "开始"))
        self.stop_btn.setText(_translate("Form", "停止"))
        self.connect_btn.setText(_translate("Form", "连接"))
