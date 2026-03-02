"""下班倒计时组件"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtGui import QFont

from src.utils.time_utils import (
    calculate_time_remaining,
    format_countdown,
    get_current_time_string,
    is_workday,
    get_weekday_name,
    get_today_weekday
)
from src.core.config_manager import ConfigManager


class CountdownWidget(QWidget):
    """下班倒计时组件"""

    # 信号：时间更新
    time_updated = Signal(str, str)  # (countdown, current_time)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = ConfigManager()
        self._timer = QTimer()
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        self._title_label = QLabel("下班倒计时")
        self._title_label.setObjectName("countdown_title")
        layout.addWidget(self._title_label)

        # 倒计时显示（不显示秒）
        self._countdown_label = QLabel("00:00")
        self._countdown_label.setObjectName("countdown_time")
        font = QFont()
        font.setPointSize(36)
        font.setBold(True)
        self._countdown_label.setFont(font)
        self._countdown_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._countdown_label)

        # 当前时间
        self._current_time_label = QLabel("当前时间: --:--:--")
        self._current_time_label.setObjectName("current_time")
        layout.addWidget(self._current_time_label)

        # 星期几
        self._weekday_label = QLabel()
        self._weekday_label.setObjectName("weekday")
        layout.addWidget(self._weekday_label)

        # 状态标签
        self._status_label = QLabel()
        self._status_label.setObjectName("status")
        layout.addWidget(self._status_label)

        layout.addStretch()

        # 设置样式
        self._update_style()

    def _connect_signals(self):
        """连接信号"""
        self._timer.timeout.connect(self._update_time)
        self._timer.start(1000)  # 每秒更新

    def _update_time(self):
        """更新时间"""
        work_end_hour, work_end_minute = self._parse_work_time()

        # 获取午休时间设置
        lunch_enabled = self._config.is_lunch_break_enabled()
        lunch_start = self._config.get_lunch_break_start()
        lunch_end = self._config.get_lunch_break_end()

        # 计算倒计时（考虑午休时间，不显示秒）
        remaining_seconds = calculate_time_remaining(
            work_end_hour, work_end_minute,
            lunch_enabled, lunch_start, lunch_end
        )
        countdown = format_countdown(remaining_seconds, show_seconds=False)

        # 获取当前时间
        current_time = get_current_time_string()

        # 更新显示
        self._countdown_label.setText(countdown)
        self._current_time_label.setText(f"当前时间: {current_time}")

        # 更新星期
        weekday = get_today_weekday()
        weekday_name = get_weekday_name(weekday)
        work_days = self._config.get_work_days()
        is_work = is_workday(work_days)
        day_type = "工作日" if is_work else "休息日"
        self._weekday_label.setText(f"{weekday_name} - {day_type}")

        # 更新状态
        if remaining_seconds <= 0:
            if is_work:
                self._status_label.setText("🎉 下班啦！")
            else:
                self._status_label.setText("🌙 休息时间")
        elif remaining_seconds < 3600:  # 小于1小时
            self._status_label.setText("💪 加油，快下班了！")
        else:
            self._status_label.setText("💼 工作中...")

        # 更新样式（根据剩余时间）
        self._update_style(remaining_seconds)

        # 发送信号
        self.time_updated.emit(countdown, current_time)

    def _parse_work_time(self):
        """解析下班时间"""
        work_end = self._config.get_work_end_time()
        parts = work_end.split(':')
        return int(parts[0]), int(parts[1])

    def _update_style(self, remaining_seconds: int = None):
        """更新样式"""
        if remaining_seconds is None:
            work_end_hour, _ = self._parse_work_time()
            lunch_enabled = self._config.is_lunch_break_enabled()
            lunch_start = self._config.get_lunch_break_start()
            lunch_end = self._config.get_lunch_break_end()
            remaining_seconds = calculate_time_remaining(
                work_end_hour, 0,
                lunch_enabled, lunch_start, lunch_end
            )

        # 根据剩余时间设置颜色
        if remaining_seconds <= 0:
            color = "#22C55E"  # 绿色
        elif remaining_seconds < 1800:  # 小于30分钟
            color = "#EF4444"  # 红色
        elif remaining_seconds < 3600:  # 小于1小时
            color = "#F97316"  # 橙色
        else:
            color = "#3B82F6"  # 蓝色

        self._countdown_label.setStyleSheet(f"""
            color: {color};
            font-weight: bold;
        """)

    def start(self):
        """启动倒计时"""
        if not self._timer.isActive():
            self._timer.start(1000)

    def stop(self):
        """停止倒计时"""
        self._timer.stop()
