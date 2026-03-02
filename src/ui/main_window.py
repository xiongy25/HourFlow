"""主窗口"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSystemTrayIcon, QMenu, QLabel, QMessageBox,
    QPushButton, QFrame, QScrollArea, QTabWidget
)
from PySide6.QtCore import Signal, QTimer, Qt
from PySide6.QtGui import QAction, QCloseEvent, QPixmap, QPainter, QColor, QIcon

from src.ui.widgets.countdown_widget import CountdownWidget
from src.ui.widgets.time_viz_widget import TimeVizWidget
from src.ui.widgets.schedule_widget import ScheduleWidget
from src.ui.widgets.task_manager_widget import TaskManagerWidget, AddTaskDialog
from src.ui.widgets.settings_dialog import SettingsDialog
from src.core.config_manager import ConfigManager
from src.core.task_manager import TaskManager
from src.services.reminder_service import ReminderService


def create_default_icon() -> QIcon:
    """创建默认图标"""
    # 创建一个 64x64 的 pixmap
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))  # 透明背景
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # 绘制一个简单的时钟圆形
    painter.setBrush(QColor("#3B82F6"))  # 蓝色
    painter.setPen(QColor("#3B82F6"))
    painter.drawEllipse(8, 8, 48, 48)
    
    # 绘制时针
    painter.setPen(QColor("#FFFFFF"))
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRect(30, 20, 4, 18)
    
    # 绘制分针
    painter.drawRect(40, 26, 3, 14)
    
    painter.end()
    return QIcon(pixmap)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self._config = ConfigManager()
        self._task_manager = TaskManager()
        self._reminder_service = None
        self._task_widget_visible = False
        self._init_ui()
        self._init_tray()
        self._init_reminder()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("上班助手")
        self.setMinimumSize(700, 500)

        # 应用窗口透明度设置
        self._apply_opacity()

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局 - 垂直
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # ===== 顶部：倒计时 + 时间进度 =====
        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)

        # 左侧：倒计时组件
        self._countdown_widget = CountdownWidget()
        self._countdown_widget.setFixedWidth(320)
        top_layout.addWidget(self._countdown_widget)

        # 右侧：时间进度圆环
        self._time_viz_widget = TimeVizWidget()
        self._time_viz_widget.setFixedWidth(180)
        top_layout.addWidget(self._time_viz_widget)

        top_layout.addStretch()

        main_layout.addLayout(top_layout)

        # ===== 中间：今日计划（主要区域）=====
        self._schedule_widget = ScheduleWidget()
        self._schedule_widget.add_task_clicked.connect(self._show_add_task_dialog)
        main_layout.addWidget(self._schedule_widget, 1)

        # ===== 底部：可折叠的任务管理 =====
        self._create_collapsible_task_section(main_layout)

        # 菜单栏
        self._create_menu_bar()

        # 更新统计
        self._update_stats()
        timer = QTimer()
        timer.timeout.connect(self._update_stats)
        timer.start(60000)  # 每分钟更新

    def _create_button_panel(self) -> QWidget:
        """创建快捷操作按钮面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # 任务管理按钮
        self._task_toggle_btn = QPushButton("任务管理 ▼")
        self._task_toggle_btn.setObjectName("toggle_button")
        self._task_toggle_btn.clicked.connect(self._toggle_task_widget)
        layout.addWidget(self._task_toggle_btn)

        # 设置按钮
        settings_btn = QPushButton("设置")
        settings_btn.clicked.connect(self._show_settings)
        layout.addWidget(settings_btn)

        layout.addStretch()
        return panel

    def _create_collapsible_task_section(self, parent_layout):
        """创建可折叠的任务管理区域"""
        # 任务管理容器（默认隐藏）
        self._task_container = QFrame()
        self._task_container.setObjectName("task_container")
        self._task_container.setVisible(False)  # 默认隐藏

        task_layout = QVBoxLayout(self._task_container)
        task_layout.setContentsMargins(0, 5, 0, 0)

        # 任务管理组件
        self._task_widget = TaskManagerWidget()
        task_layout.addWidget(self._task_widget)

        parent_layout.addWidget(self._task_container)

    def _toggle_task_widget(self):
        """切换任务管理显示/隐藏"""
        self._task_widget_visible = not self._task_widget_visible
        self._task_container.setVisible(self._task_widget_visible)

        # 更新按钮文字
        if self._task_widget_visible:
            self._task_toggle_btn.setText("任务管理 ▲")
        else:
            self._task_toggle_btn.setText("任务管理 ▼")

    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _init_tray(self):
        """初始化系统托盘"""
        self._tray = QSystemTrayIcon(self)
        
        # 设置托盘图标
        self._tray.setIcon(create_default_icon())
        self._tray.setToolTip("上班助手")

        # 托盘菜单
        tray_menu = QMenu()

        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._show_settings)
        tray_menu.addAction(settings_action)

        tray_menu.addSeparator()

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)

        self._tray.setContextMenu(tray_menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

        # 更新托盘提示
        self._countdown_widget.time_updated.connect(self._update_tray_tooltip)

    def _update_tray_tooltip(self, countdown: str, current_time: str):
        """更新托盘提示"""
        self._tray.setToolTip(f"上班助手\n剩余时间: {countdown}")

    def _on_tray_activated(self, reason):
        """托盘图标被点击"""
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()

    def _init_reminder(self):
        """初始化久坐提醒服务"""
        if self._config.is_sedentary_reminder_enabled():
            self._reminder_service = ReminderService(
                self._config.get_sedentary_interval()
            )
            self._reminder_service.start(self._on_reminder_triggered)

    def _on_reminder_triggered(self):
        """久坐提醒触发"""
        tip = ReminderService.get_random_tip()
        QMessageBox.information(
            self,
            "休息提醒",
            f"您已经连续工作{self._config.get_sedentary_interval()}分钟了！\n\n"
            f"💡 {tip}"
        )

    def _show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec()

    def _show_add_task_dialog(self):
        """显示添加任务对话框"""
        dialog = AddTaskDialog(self)
        dialog.task_added.connect(self._on_task_added)
        dialog.exec()

    def _on_task_added(self, title: str, minutes: int, priority):
        """任务添加回调"""
        self._task_manager.add_task(title, minutes, priority)
        # 刷新今日计划
        self._schedule_widget.refresh()

    def _on_settings_changed(self):
        """设置变更回调"""
        if self._reminder_service:
            self._reminder_service.stop()

        if self._config.is_sedentary_reminder_enabled():
            self._reminder_service = ReminderService(
                self._config.get_sedentary_interval()
            )
            self._reminder_service.start(self._on_reminder_triggered)

        # 应用窗口透明度设置
        self._apply_opacity()

    def _apply_opacity(self):
        """应用窗口透明度设置"""
        opacity = self._config.get_window_opacity()
        
        if opacity == 0:
            # 窗口完全透明，但内容保持可见
            # 使用WA_TranslucentBackground使窗口背景透明
            self.setAttribute(Qt.WA_TranslucentBackground)
            # 设置窗口背景为透明，但子组件保持原色
            self.setStyleSheet("QMainWindow { background: transparent; }")
        else:
            # 恢复默认设置
            self.setAttribute(Qt.WA_TranslucentBackground, False)
            self.setStyleSheet("")
            self.setWindowOpacity(opacity)

    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于上班助手",
            "上班助手 v1.0\n\n"
            "一款帮助上班族管理时间、提高效率的桌面工具。\n\n"
            "功能特点：\n"
            "• 下班倒计时\n"
            "• 智能时间块分配\n"
            "• 久坐提醒\n"
            "• 今日计划视图"
        )

    def _update_stats(self):
        """更新统计信息（占位方法）"""
        # 统计功能现在集成在倒计时组件中
        pass

    def closeEvent(self, event: QCloseEvent):
        """关闭事件"""
        if self._config.is_minimize_to_tray():
            self.hide()
            event.ignore()
        else:
            if self._reminder_service:
                self._reminder_service.stop()
            event.accept()
