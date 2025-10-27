import sys
import random
import csv
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout,
                             QHBoxLayout, QPushButton, QFileDialog, QMessageBox, QSizePolicy)
from PyQt5.QtCore import QTimer, QDateTime, Qt, QThread, pyqtSignal
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

matplotlib.use('Qt5Agg')


# === GitHub 上傳執行緒 ===
class GitUploader(QThread):
    log_signal = pyqtSignal(str)

    def run(self):
        try:
            # Git 自動上傳流程
            subprocess.run(["git", "add", "data.csv"], check=True)
            subprocess.run(["git", "commit", "-m", "auto update data"], check=False)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            self.log_signal.emit("[GitHub] ✅ Data pushed successfully.")
        except subprocess.CalledProcessError as e:
            self.log_signal.emit(f"[GitHub] ❌ Push failed: {e}")


# === 主應用 ===
class EnergyMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Energy Monitor System")
        self.resize(900, 600)

        # === 主布局 ===
        main_layout = QVBoxLayout()

        title = QLabel("⚡ Energy Monitor System")
        title.setStyleSheet("font-size:20px; font-weight:bold; color:#0055AA;")
        main_layout.addWidget(title)

        self.time_label = QLabel()
        main_layout.addWidget(self.time_label)

        self.power_label = QLabel("Current Power: 0 W")
        self.energy_label = QLabel("Total Energy: 0 kWh")
        self.cost_label = QLabel("Estimated Cost: $0.00")

        for label in [self.power_label, self.energy_label, self.cost_label]:
            label.setStyleSheet("font-size:14px;")
            main_layout.addWidget(label)

        # === 按鈕 ===
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Monitor")
        self.stop_btn = QPushButton("Stop Monitor")
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        main_layout.addLayout(btn_layout)

        # === Matplotlib 圖表 ===
        self.figure = Figure(figsize=(6, 6), dpi=90)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Real-time Power")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Power (W)")
        self.ax.grid(True)
        self.figure.tight_layout()
        self.power_data, self.time_data = [], []
        main_layout.addWidget(self.canvas, stretch=1)

        # === 狀態輸出 ===
        self.log_label = QLabel()
        self.log_label.setAlignment(Qt.AlignLeft)
        self.log_label.setWordWrap(True)
        main_layout.addWidget(self.log_label)

        self.setLayout(main_layout)

        # === 定時器 ===
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.git_timer = QTimer(self)
        self.git_timer.timeout.connect(self.upload_to_github)

        # === 連接事件 ===
        self.start_btn.clicked.connect(self.start_monitor)
        self.stop_btn.clicked.connect(self.stop_monitor)

        # === 初始化數據 ===
        self.power = 0
        self.energy = 0.0
        self.cost_rate = 0.12
        self.records = []
        self.start_time = None
        self.update_time()
        self.update_data()

        # === Git Uploader Thread ===
        self.uploader = GitUploader()
        self.uploader.log_signal.connect(self.append_log)

    def append_log(self, text):
        """顯示狀態輸出訊息"""
        self.log_label.setText(f"{text}\n" + self.log_label.text())

    def start_monitor(self):
        self.timer.start(100)  # 100ms 更新數據
        self.git_timer.start(30000)  # 每 30 秒上傳一次
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.records.clear()
        self.power_data.clear()
        self.time_data.clear()
        self.start_time = QDateTime.currentDateTime()
        self.ax.clear()
        self.ax.set_title("Real-time Power")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Power (W)")
        self.ax.grid(True)
        self.figure.tight_layout()
        self.canvas.draw()
        self.append_log("[System] ✅ Monitoring started.")

    def stop_monitor(self):
        self.timer.stop()
        self.git_timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.append_log("[System] 🛑 Monitoring stopped.")
        if self.records:
            self.save_data("data.csv")

    def save_data(self, file_path="data.csv"):
        """保存資料到 data.csv（供 Git 上傳使用）"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["時間", "功率(W)", "累計能耗(kWh)", "預估費用($)"])
                writer.writerows(self.records)
            self.append_log(f"[File] 💾 Data saved to {file_path}")
        except Exception as e:
            self.append_log(f"[File] ❌ Save failed: {e}")

    def upload_to_github(self):
        """每30秒自動儲存並上傳"""
        self.save_data("data.csv")
        self.uploader.start()

    def update_time(self):
        self.time_label.setText("Current Time: " + QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss.zzz"))

    def update_data(self):
        self.power = random.randint(200, 5000)
        self.energy += self.power / 1000.0 / 3600.0 / 10.0
        cost = self.energy * self.cost_rate
        self.power_label.setText(f"Current Power: {self.power} W")
        self.energy_label.setText(f"Total Energy: {self.energy:.4f} kWh")
        self.cost_label.setText(f"Estimated Cost: ${cost:.2f}")
        self.update_time()

        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss.zzz")
        self.records.append([current_time, self.power, round(self.energy, 4), round(cost, 2)])
        self.power_data.append(self.power)
        self.time_data.append(current_time)

        if len(self.power_data) > 500:
            self.power_data.pop(0)
            self.time_data.pop(0)

        self.ax.clear()
        self.ax.set_title("Real-time Power")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Power (W)")
        self.ax.plot(self.time_data, self.power_data, 'b-')
        self.ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins=6))
        self.ax.tick_params(axis='x', rotation=45)
        self.figure.tight_layout()
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    monitor = EnergyMonitor()
    monitor.show()
    sys.exit(app.exec_())