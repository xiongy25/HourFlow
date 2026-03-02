"""时间可视化组件"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont

from src.utils.time_utils import calculate_work_progress, get_time_period
from src.core.config_manager import ConfigManager


class TimeVizWidget(QWidget):
    """时间进度可视化组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = ConfigManager()
        self._progress = 0.0
        self._timer = QTimer()
        self._init_ui()
        self._connect_signals()
        # 立即更新进度
        self._update_progress()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        self._title_label = QLabel("时间进度")
        self._title_label.setObjectName("viz_title")
        layout.addWidget(self._title_label)

        # 进度百分比
        self._progress_label = QLabel("0%")
        self._progress_label.setObjectName("progress_percent")
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        self._progress_label.setFont(font)
        self._progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._progress_label)

        # 时间段标签
        self._period_label = QLabel()
        self._period_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._period_label)

        # 统计信息
        self._stats_label = QLabel()
        self._stats_label.setObjectName("stats")
        layout.addWidget(self._stats_label)

        layout.addStretch()

    def _connect_signals(self):
        """连接信号"""
        self._timer.timeout.connect(self._update_progress)
        self._timer.start(60000)  # 每分钟更新

    def _update_progress(self):
        """更新进度"""
        work_start = self._config.get_work_start_time()
        work_end = self._config.get_work_end_time()

        # 获取午休时间设置
        lunch_enabled = self._config.is_lunch_break_enabled()
        lunch_start = self._config.get_lunch_break_start()
        lunch_end = self._config.get_lunch_break_end()

        self._progress = calculate_work_progress(
            work_start, work_end,
            lunch_enabled, lunch_start, lunch_end
        )
        self._progress_label.setText(f"{self._progress:.1f}%")

        # 更新时间段
        period = get_time_period()
        period_names = {
            "morning": "上午",
            "afternoon": "下午",
            "evening": "傍晚"
        }
        self._period_label.setText(period_names.get(period, ""))

        self.update()  # 重绘

    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 获取组件尺寸
        width = self.width()
        height = self.height()

        # 计算圆环尺寸
        size = min(width, height - 60)
        if size < 50:
            size = 50

        center_x = width // 2
        center_y = height // 2 - 10
        radius = size // 2 - 10
        pen_width = 12

        # 获取时间段颜色
        period = get_time_period()
        if period == "morning":
            progress_color = QColor("#F59E0B")  # 橙色
        elif period == "afternoon":
            progress_color = QColor("#3B82F6")  # 蓝色
        else:
            progress_color = QColor("#8B5CF6")  # 紫色

        # 绘制背景圆环
        bg_color = QColor("#E5E7EB")
        painter.setPen(QPen(bg_color, pen_width))
        painter.setBrush(Qt.NoBrush)
        rect = center_x - radius, center_y - radius, radius * 2, radius * 2
        painter.drawEllipse(*rect)

        # 绘制进度圆环
        if self._progress > 0:
            painter.setPen(QPen(progress_color, pen_width))
            painter.setBrush(Qt.NoBrush)

            # 计算角度
            angle = int(360 * self._progress / 100)

            # 绘制弧形
            arc_rect = (center_x - radius, center_y - radius,
                       radius * 2, radius * 2)
            start_angle = 90 * 16
            span_angle = -angle * 16
            painter.drawArc(*arc_rect, start_angle, span_angle)

    def get_progress(self) -> float:
        """获取当前进度"""
        return self._progress

    def start(self):
        """启动更新"""
        self._update_progress()
        if not self._timer.isActive():
            self._timer.start(60000)

    def stop(self):
        """停止更新"""
        self._timer.stop()
