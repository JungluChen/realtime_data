import sys
import random
import csv
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QFileDialog, QMessageBox, QSizePolicy)
from PyQt5.QtCore import QTimer, QDateTime
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
# 新增绘图所需模块
matplotlib.use('Qt5Agg')  # 使用Qt5后端
class EnergyMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Energy Monitor System")
        self.resize(900, 600)  # 增大窗口以容纳图表

        # 主布局
        main_layout = QVBoxLayout()

        # 标题
        title = QLabel("Energy Monitor System")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        main_layout.addWidget(title)

        # 当前时间（含毫秒）
        self.time_label = QLabel()
        main_layout.addWidget(self.time_label)

        # 能耗数据标签
        self.power_label = QLabel("Current Power: 0 W")
        self.energy_label = QLabel("Total Energy: 0 kWh")
        self.cost_label = QLabel("Estimated Cost: $0.00")

        main_layout.addWidget(self.power_label)
        main_layout.addWidget(self.energy_label)
        main_layout.addWidget(self.cost_label)

        # 控制按钮
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Monitor")
        self.stop_btn = QPushButton("Stop Monitor")
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        main_layout.addLayout(btn_layout)

        # 创建matplotlib图表
        self.figure = Figure(figsize=(6, 6), dpi=90)
        self.canvas = FigureCanvas(self.figure)
        # 让画布在布局中尽可能扩展，避免显示被裁剪
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.updateGeometry()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Real-time Power")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Power (W)")
        self.ax.grid(True)
        # 初始调整布局，保证坐标轴标签不被裁剪
        self.figure.tight_layout()
        self.power_data = []  # 存储功率数据
        self.time_data = []   # 存储对应时间
        main_layout.addWidget(self.canvas, stretch=1)

        self.setLayout(main_layout)

        # 定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)

        # 连接按钮事件
        self.start_btn.clicked.connect(self.start_monitor)
        self.stop_btn.clicked.connect(self.stop_monitor)

        # 初始化数据
        self.power = 0
        self.energy = 0.0
        self.cost_rate = 0.12  # 每kWh费用
        self.records = []  # 存储记录
        self.start_time = None  # 记录开始时间
        self.update_time()
        self.update_data()

    def start_monitor(self):
        self.timer.start(100)  # 100毫秒刷新一次
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.records.clear()  # 清空旧记录
        self.power_data.clear()
        self.time_data.clear()
        self.start_time = QDateTime.currentDateTime()  # 记录开始时间
        self.ax.clear()
        self.ax.set_title("Real-time Power")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Power (W)")
        self.ax.grid(True)
        # 防止坐标轴和标签被裁剪
        self.figure.tight_layout()
        self.canvas.draw()

    def stop_monitor(self):
        self.timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        # 询问保存位置
        if self.records:
            self.ask_save_location()

    def ask_save_location(self):
        # 生成默认文件名：开始时间_to_结束时间_energy_data.csv
        end_time = QDateTime.currentDateTime()
        default_name = f"{self.start_time.toString('yyyyMMdd_hhmmss')}_to_{end_time.toString('yyyyMMdd_hhmmss')}_energy_data.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存能耗数据",
            os.path.join(os.path.expanduser("~"), default_name),
            "CSV Files (*.csv)"
        )
        if file_path:
            self.save_data(file_path)
        else:
            QMessageBox.information(self, "提示", "未选择保存路径，数据未保存。")

    def save_data(self, file_path):
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["时间", "功率(W)", "累计能耗(kWh)", "预估费用($)"])
                writer.writerows(self.records)
            QMessageBox.information(self, "成功", f"数据已保存至：\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败：\n{str(e)}")

    def update_time(self):
        # 显示到毫秒
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss.zzz")
        self.time_label.setText("Current Time: " + current_time)

    def update_data(self):
        # 模拟实时功率（200-5000 W）
        self.power = random.randint(200, 5000)
        # 累加能耗（转换为kWh，按100ms累加）
        self.energy += self.power / 1000.0 / 3600.0 / 10.0
        cost = self.energy * self.cost_rate

        # 更新标签
        self.power_label.setText(f"Current Power: {self.power} W")
        self.energy_label.setText(f"Total Energy: {self.energy:.4f} kWh")
        self.cost_label.setText(f"Estimated Cost: ${cost:.2f}")
        self.update_time()

        # 记录数据（含毫秒）
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss.zzz")
        self.records.append([current_time, self.power, round(self.energy, 4), round(cost, 2)])

        # 更新图表
        self.power_data.append(self.power)
        self.time_data.append(current_time)
        # 限制显示最近500个点（100ms间隔，约50秒）
        if len(self.power_data) > 500:
            self.power_data.pop(0)
            self.time_data.pop(0)
        self.ax.clear()
        self.ax.set_title("Real-time Power")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Power (W)")
        self.ax.grid(False)
        self.ax.plot(self.time_data, self.power_data, 'b-')
        # 自动调整x轴刻度，避免拥挤
        self.ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins=6))
        self.ax.tick_params(axis='x', rotation=45)
        # 每次绘制后紧凑布局，确保刻度和标签完整显示
        self.figure.tight_layout()
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    monitor = EnergyMonitor()
    monitor.show()
    sys.exit(app.exec_())
