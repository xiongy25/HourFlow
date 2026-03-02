"""任务管理组件"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton,
    QCheckBox, QFrame, QLineEdit, QComboBox,
    QSpinBox, QDialog, QDialogButtonBox, QFormLayout,
    QMessageBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from src.models.task import Task, Priority
from src.core.task_manager import TaskManager


class TaskListItem(QListWidgetItem):
    """任务列表项"""

    def __init__(self, task: Task, parent=None, on_delete=None):
        super().__init__(parent)
        self._task = task
        self._on_delete = on_delete
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        widget = QFrame()
        widget.setObjectName("task_item")

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)

        # 复选框
        self._checkbox = QCheckBox()
        self._checkbox.setChecked(self._task.completed)
        layout.addWidget(self._checkbox)

        # 任务标题
        title_label = QLabel(self._task.title)
        title_label.setStyleSheet(
            "text-decoration: line-through;" if self._task.completed else ""
        )
        layout.addWidget(title_label, 1)

        # 优先级标签
        priority_text = {
            Priority.HIGH: "高",
            Priority.MEDIUM: "中",
            Priority.LOW: "低"
        }
        priority_label = QLabel(priority_text.get(self._task.priority, ""))
        priority_colors = {
            Priority.HIGH: "#EF4444",
            Priority.MEDIUM: "#F59E0B",
            Priority.LOW: "#22C55E"
        }
        priority_label.setStyleSheet(f"""
            color: {priority_colors.get(self._task.priority, '#000')};
            background: #F3F4F6;
            padding: 2px 8px;
            border-radius: 4px;
        """)
        layout.addWidget(priority_label)

        # 时长
        duration_label = QLabel(f"{self._task.estimated_minutes}分钟")
        layout.addWidget(duration_label)

        # 删除按钮
        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(24, 24)
        delete_btn.setStyleSheet("""
            QPushButton {
                background: #EF4444;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #DC2626;
            }
        """)
        layout.addWidget(delete_btn)

        self.setSizeHint(widget.sizeHint())
        self.setData(Qt.UserRole, self._task.id)
        
        # 连接信号
        self._checkbox.stateChanged.connect(
            lambda state: self.listWidget().itemChanged.emit(self)
        )
        delete_btn.clicked.connect(
            lambda: self._on_delete(self._task.id) if self._on_delete else None
        )


class TaskManagerWidget(QWidget):
    """任务管理组件"""

    # 信号
    tasks_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._task_manager = TaskManager()
        self._init_ui()
        self._load_tasks()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        self._title_label = QLabel("📋 任务管理")
        self._title_label.setObjectName("task_title")
        font = QFont()
        font.setBold(True)
        self._title_label.setFont(font)
        layout.addWidget(self._title_label)

        # 统计信息
        self._stats_label = QLabel()
        self._stats_label.setObjectName("task_stats")
        layout.addWidget(self._stats_label)

        # 任务列表
        self._task_list = QListWidget()
        self._task_list.setObjectName("task_list")
        layout.addWidget(self._task_list)

        # 按钮栏
        button_layout = QHBoxLayout()

        # 添加任务按钮
        self._add_button = QPushButton("+ 添加任务")
        self._add_button.setObjectName("primary_button")
        self._add_button.clicked.connect(self._show_add_task_dialog)
        button_layout.addWidget(self._add_button)

        # 优化安排按钮
        self._optimize_button = QPushButton("🔄 优化安排")
        self._optimize_button.setObjectName("secondary_button")
        self._optimize_button.clicked.connect(self._optimize_schedule)
        button_layout.addWidget(self._optimize_button)

        # 清除已完成按钮
        self._clear_button = QPushButton("清除已完成")
        self._clear_button.setObjectName("secondary_button")
        self._clear_button.clicked.connect(self._clear_completed)
        button_layout.addWidget(self._clear_button)

        layout.addLayout(button_layout)

        # 设置样式
        self.setStyleSheet("""
            #primary_button {
                background: #3B82F6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            #primary_button:hover {
                background: #2563EB;
            }
            #secondary_button {
                background: #6B7280;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            #secondary_button:hover {
                background: #4B5563;
            }
            #task_list {
                border: 1px solid #E5E7EB;
                border-radius: 4px;
            }
        """)

    def _load_tasks(self):
        """加载任务列表"""
        self._task_list.clear()
        tasks = self._task_manager.get_tasks()

        for task in tasks:
            item = TaskListItem(task, on_delete=self._on_task_delete)
            self._task_list.addItem(item)

        # 连接 QListWidget 的内置信号
        self._task_list.itemChanged.connect(self._on_item_check_changed)

        self._update_stats()

    def _on_item_check_changed(self, item: TaskListItem):
        """任务勾选状态改变"""
        task_id = item.data(Qt.UserRole)
        checked = item._checkbox.isChecked()
        self._on_task_check_changed(task_id, checked)

    def _update_stats(self):
        """更新统计信息"""
        stats = self._task_manager.get_task_stats()
        self._stats_label.setText(
            f"总任务: {stats['total']} | "
            f"已完成: {stats['completed']} | "
            f"待完成: {stats['pending']}"
        )

    def _show_add_task_dialog(self):
        """显示添加任务对话框"""
        dialog = AddTaskDialog(self)
        dialog.task_added.connect(self._on_task_added)
        dialog.exec()

    def _on_task_added(self, title: str, minutes: int, priority: Priority):
        """任务添加回调"""
        self._task_manager.add_task(title, minutes, priority)
        self._load_tasks()
        self.tasks_changed.emit()

    def _on_task_check_changed(self, task_id: str, checked: bool):
        """任务勾选状态改变"""
        task = self._task_manager.get_task_by_id(task_id)
        if task:
            task.completed = checked
            self._task_manager.update_task(task_id, completed=checked)
            self._update_stats()
            self.tasks_changed.emit()

    def _on_task_delete(self, task_id: str):
        """任务删除"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这个任务吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._task_manager.delete_task(task_id)
            self._load_tasks()
            self.tasks_changed.emit()

    def _optimize_schedule(self):
        """优化安排"""
        self.tasks_changed.emit()

    def _clear_completed(self):
        """清除已完成的任务"""
        reply = QMessageBox.question(
            self,
            "确认清除",
            "确定要清除所有已完成的任务吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._task_manager.clear_completed_tasks()
            self._load_tasks()
            self.tasks_changed.emit()

    def refresh(self):
        """刷新任务列表"""
        self._load_tasks()


class AddTaskDialog(QDialog):
    """添加任务对话框"""

    task_added = Signal(str, int, Priority)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("添加任务")
        self.setModal(True)
        self.resize(400, 250)

        layout = QFormLayout(self)

        # 任务标题
        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("请输入任务标题")
        layout.addRow("任务标题:", self._title_input)

        # 预计时长
        self._duration_input = QSpinBox()
        self._duration_input.setRange(5, 480)
        self._duration_input.setValue(30)
        self._duration_input.setSuffix(" 分钟")
        layout.addRow("预计时长:", self._duration_input)

        # 优先级
        self._priority_input = QComboBox()
        self._priority_input.addItems(["高", "中", "低"])
        layout.addRow("优先级:", self._priority_input)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_ok(self):
        """确定按钮点击"""
        title = self._title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "警告", "请输入任务标题")
            return

        duration = self._duration_input.value()
        priority_map = {"高": Priority.HIGH, "中": Priority.MEDIUM, "低": Priority.LOW}
        priority = priority_map.get(self._priority_input.currentText(), Priority.MEDIUM)

        self.task_added.emit(title, duration, priority)
        self.accept()
