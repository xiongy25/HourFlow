"""设置对话框"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QCheckBox,
    QDialogButtonBox, QGroupBox, QWidget,
    QSlider, QHBoxLayout, QLabel
)
from PySide6.QtCore import Signal, Qt

from src.core.config_manager import ConfigManager


class SettingsDialog(QDialog):
    """设置对话框"""

    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = ConfigManager()
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("设置")
        self.setModal(True)
        self.resize(500, 500)

        layout = QVBoxLayout(self)

        # 工作时间设置
        work_group = QGroupBox("工作时间设置")
        work_layout = QFormLayout()

        self._work_start_edit = QLineEdit()
        self._work_start_edit.setPlaceholderText("09:30")
        work_layout.addRow("上班时间:", self._work_start_edit)

        self._work_end_edit = QLineEdit()
        self._work_end_edit.setPlaceholderText("19:00")
        work_layout.addRow("下班时间:", self._work_end_edit)

        # 工作日选择
        self._work_days_widget = WorkDaysSelector()
        work_layout.addRow("工作日:", self._work_days_widget)

        work_group.setLayout(work_layout)
        layout.addWidget(work_group)

        # 午休时间设置（新增）
        lunch_group = QGroupBox("午休时间设置")
        lunch_layout = QFormLayout()

        self._lunch_break_enabled = QCheckBox("启用午休时间（不计入工作时间）")
        lunch_layout.addRow("", self._lunch_break_enabled)

        self._lunch_start_edit = QLineEdit()
        self._lunch_start_edit.setPlaceholderText("12:00")
        lunch_layout.addRow("午休开始:", self._lunch_start_edit)

        self._lunch_end_edit = QLineEdit()
        self._lunch_end_edit.setPlaceholderText("13:30")
        lunch_layout.addRow("午休结束:", self._lunch_end_edit)

        lunch_group.setLayout(lunch_layout)
        layout.addWidget(lunch_group)

        # 久坐提醒设置
        reminder_group = QGroupBox("久坐提醒设置")
        reminder_layout = QFormLayout()

        self._reminder_enabled = QCheckBox("启用久坐提醒")
        reminder_layout.addRow("", self._reminder_enabled)

        self._reminder_interval = QSpinBox()
        self._reminder_interval.setRange(15, 120)
        self._reminder_interval.setSuffix(" 分钟")
        reminder_layout.addRow("提醒间隔:", self._reminder_interval)

        reminder_group.setLayout(reminder_layout)
        layout.addWidget(reminder_group)

        # 系统设置
        system_group = QGroupBox("系统设置")
        system_layout = QFormLayout()

        self._minimize_to_tray = QCheckBox("关闭窗口时最小化到系统托盘")
        system_layout.addRow("", self._minimize_to_tray)

        self._notifications_enabled = QCheckBox("启用系统通知")
        system_layout.addRow("", self._notifications_enabled)

        system_group.setLayout(system_layout)
        layout.addWidget(system_group)

        # 窗口设置
        window_group = QGroupBox("窗口设置")
        window_layout = QFormLayout()

        # 透明度滑块
        opacity_layout = QHBoxLayout()
        self._opacity_slider = QSlider(Qt.Horizontal)
        self._opacity_slider.setRange(10, 100)  # 10%-100%
        self._opacity_slider.setTickPosition(QSlider.TicksBelow)
        self._opacity_slider.setTickInterval(10)
        self._opacity_label = QLabel("100%")
        self._opacity_slider.valueChanged.connect(
            lambda v: self._opacity_label.setText(f"{v}%")
        )
        opacity_layout.addWidget(self._opacity_slider)
        opacity_layout.addWidget(self._opacity_label)
        window_layout.addRow("窗口透明度:", opacity_layout)

        window_group.setLayout(window_layout)
        layout.addWidget(window_group)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Reset
        )
        buttons.accepted.connect(self._save_settings)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Reset).clicked.connect(self._reset_to_default)
        layout.addWidget(buttons)

        # 连接午休启用状态变化
        self._lunch_break_enabled.toggled.connect(self._on_lunch_enabled_changed)

    def _on_lunch_enabled_changed(self, enabled: bool):
        """午休启用状态变化"""
        self._lunch_start_edit.setEnabled(enabled)
        self._lunch_end_edit.setEnabled(enabled)

    def _load_settings(self):
        """加载设置"""
        self._work_start_edit.setText(self._config.get_work_start_time())
        self._work_end_edit.setText(self._config.get_work_end_time())
        self._work_days_widget.set_selected_days(self._config.get_work_days())

        # 午休时间设置
        self._lunch_break_enabled.setChecked(self._config.is_lunch_break_enabled())
        self._lunch_start_edit.setText(self._config.get_lunch_break_start())
        self._lunch_end_edit.setText(self._config.get_lunch_break_end())
        self._on_lunch_enabled_changed(self._config.is_lunch_break_enabled())

        self._reminder_enabled.setChecked(self._config.is_sedentary_reminder_enabled())
        self._reminder_interval.setValue(self._config.get_sedentary_interval())

        self._minimize_to_tray.setChecked(self._config.is_minimize_to_tray())
        self._notifications_enabled.setChecked(
            self._config.get("notifications_enabled", True)
        )

        # 窗口透明度设置
        opacity = int(self._config.get_window_opacity() * 100)
        self._opacity_slider.setValue(opacity)
        self._opacity_label.setText(f"{opacity}%")

    def _save_settings(self):
        """保存设置"""
        # 验证时间格式
        start_time = self._work_start_edit.text().strip()
        end_time = self._work_end_edit.text().strip()

        if not self._validate_time(start_time):
            self._work_start_edit.setFocus()
            return

        if not self._validate_time(end_time):
            self._work_end_edit.setFocus()
            return

        # 验证午休时间
        if self._lunch_break_enabled.isChecked():
            lunch_start = self._lunch_start_edit.text().strip()
            lunch_end = self._lunch_end_edit.text().strip()

            if not self._validate_time(lunch_start):
                self._lunch_start_edit.setFocus()
                return
            if not self._validate_time(lunch_end):
                self._lunch_end_edit.setFocus()
                return

        # 保存工作时间设置
        self._config.set("work_start_time", start_time)
        self._config.set("work_end_time", end_time)
        self._config.set("work_days", self._work_days_widget.get_selected_days())

        # 保存午休时间设置
        self._config.set("lunch_break_enabled", self._lunch_break_enabled.isChecked())
        if self._lunch_break_enabled.isChecked():
            self._config.set("lunch_break_start", self._lunch_start_edit.text().strip())
            self._config.set("lunch_break_end", self._lunch_end_edit.text().strip())

        # 保存久坐提醒设置
        self._config.set("sedentary_reminder_enabled", self._reminder_enabled.isChecked())
        self._config.set("sedentary_reminder_interval", self._reminder_interval.value())

        # 保存系统设置
        self._config.set("minimize_to_tray", self._minimize_to_tray.isChecked())
        self._config.set("notifications_enabled", self._notifications_enabled.isChecked())

        # 保存窗口透明度设置
        opacity_value = self._opacity_slider.value() / 100.0
        self._config.set_window_opacity(opacity_value)

        self.settings_changed.emit()
        self.accept()

    def _validate_time(self, time_str: str) -> bool:
        """验证时间格式"""
        try:
            parts = time_str.split(':')
            if len(parts) != 2:
                return False
            hour = int(parts[0])
            minute = int(parts[1])
            return 0 <= hour < 24 and 0 <= minute < 60
        except (ValueError, AttributeError):
            return False

    def _reset_to_default(self):
        """重置为默认设置"""
        self._config.reset_to_default()
        self._load_settings()
        self.settings_changed.emit()


class WorkDaysSelector(QWidget):
    """工作日选择器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建7个复选框
        self._day_checkboxes = {}
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        for i, day in enumerate(days):
            checkbox = QCheckBox(day)
            checkbox.setChecked(i < 5)  # 默认选中周一到周五
            self._day_checkboxes[i + 1] = checkbox
            layout.addWidget(checkbox)

        layout.addStretch()

    def get_selected_days(self) -> list:
        """获取选中的工作日"""
        selected = []
        for day, checkbox in self._day_checkboxes.items():
            if checkbox.isChecked():
                selected.append(day)
        return selected

    def set_selected_days(self, days: list):
        """设置选中的工作日"""
        for day, checkbox in self._day_checkboxes.items():
            checkbox.setChecked(day in days)
