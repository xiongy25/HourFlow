"""久坐提醒服务"""
from datetime import datetime, timedelta
from typing import Optional, Callable
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication


class ReminderService:
    """久坐提醒服务"""

    def __init__(self, interval_minutes: int = 45):
        """
        初始化提醒服务

        Args:
            interval_minutes: 提醒间隔（分钟）
        """
        self._interval_minutes = interval_minutes
        self._timer: Optional[QTimer] = None
        self._last_break_time: Optional[datetime] = None
        self._is_paused: bool = False
        self._callback: Optional[Callable] = None
        self._break_count: int = 0
        self._total_sedentary_minutes: int = 0

    def start(self, callback: Optional[Callable] = None):
        """
        启动提醒服务

        Args:
            callback: 提醒回调函数
        """
        self._callback = callback
        self._last_break_time = datetime.now()
        self._break_count = 0
        self._total_sedentary_minutes = 0
        self._is_paused = False

        if self._timer is None:
            self._timer = QTimer()
            self._timer.timeout.connect(self._on_timer_tick)

        # 每分钟检查一次
        self._timer.start(60000)  # 60秒

    def stop(self):
        """停止提醒服务"""
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def pause(self):
        """暂停提醒"""
        self._is_paused = True

    def resume(self):
        """恢复提醒"""
        self._is_paused = False
        self._last_break_time = datetime.now()

    def skip_break(self):
        """跳过当前休息"""
        self._last_break_time = datetime.now()

    def set_interval(self, minutes: int):
        """
        设置提醒间隔

        Args:
            minutes: 间隔分钟数
        """
        self._interval_minutes = minutes

    def get_interval(self) -> int:
        """获取提醒间隔"""
        return self._interval_minutes

    def get_break_count(self) -> int:
        """获取今日休息次数"""
        return self._break_count

    def get_total_sedentary_minutes(self) -> int:
        """获取今日总久坐时间（分钟）"""
        return self._total_sedentary_minutes

    def reset_daily_stats(self):
        """重置每日统计"""
        self._break_count = 0
        self._total_sedentary_minutes = 0
        self._last_break_time = datetime.now()

    def _on_timer_tick(self):
        """定时器触发"""
        if self._is_paused:
            return

        now = datetime.now()
        if self._last_break_time is None:
            self._last_break_time = now
            return

        # 计算上次休息后经过的时间
        elapsed_minutes = (now - self._last_break_time).total_seconds() / 60

        # 累计久坐时间
        self._total_sedentary_minutes = int(elapsed_minutes)

        # 如果达到提醒间隔
        if elapsed_minutes >= self._interval_minutes:
            self._trigger_reminder()

    def _trigger_reminder(self):
        """触发提醒"""
        self._break_count += 1

        if self._callback:
            self._callback()

        # 重置计时
        self._last_break_time = datetime.now()

        # 显示系统通知
        self._show_notification()

    def _show_notification(self):
        """显示系统通知"""
        try:
            app = QApplication.instance()
            if app is None:
                return

            # 尝试通过托盘图标发送通知
            tray = getattr(app, '_tray_icon', None)
            if tray and hasattr(tray, 'showMessage'):
                tray.showMessage(
                    "休息提醒",
                    f"您已经连续工作 {self._interval_minutes} 分钟了，"
                    f"建议休息一下，活动身体！",
                    None,
                    3000
                )
        except Exception:
            pass

    @staticmethod
    def get_health_tips() -> list:
        """获取健康建议"""
        return [
            "每小时站起来活动5-10分钟",
            "眺望远方，让眼睛得到休息",
            "做几组颈部旋转运动",
            "伸展手臂和肩膀",
            "喝一杯水，补充水分",
            "深呼吸几次，缓解压力",
            "走动一下，促进血液循环",
            "做几分钟的轻度运动"
        ]

    @staticmethod
    def get_random_tip() -> str:
        """获取随机健康建议"""
        import random
        tips = ReminderService.get_health_tips()
        return random.choice(tips)
