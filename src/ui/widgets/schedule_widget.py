"""今日计划组件"""
from datetime import datetime
from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,
    QFrame, QHBoxLayout, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from src.models.time_block import TimeBlock, BlockType
from src.models.task import Task
from src.core.task_manager import TaskManager
from src.core.config_manager import ConfigManager
from src.utils.time_utils import format_time_range


class ScheduleWidget(QWidget):
    """今日计划时间轴组件"""

    # 信号
    task_clicked = Signal(str)  # 任务ID
    add_task_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._task_manager = TaskManager()
        self._config = ConfigManager()
        self._time_blocks: List[TimeBlock] = []
        self._init_ui()
        self._load_time_blocks()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题栏
        header_layout = QHBoxLayout()
        self._title_label = QLabel("📅 今日计划")
        self._title_label.setObjectName("schedule_title")
        font = QFont()
        font.setBold(True)
        self._title_label.setFont(font)
        header_layout.addWidget(self._title_label)

        header_layout.addStretch()

        # 添加任务按钮
        self._add_button = QPushButton("+ 添加")
        self._add_button.setObjectName("add_task_button")
        self._add_button.clicked.connect(self.add_task_clicked.emit)
        header_layout.addWidget(self._add_button)

        layout.addLayout(header_layout)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("schedule_scroll")

        # 时间轴容器
        self._timeline_container = QWidget()
        self._timeline_layout = QVBoxLayout(self._timeline_container)
        self._timeline_layout.setSpacing(8)
        self._timeline_layout.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(self._timeline_container)
        layout.addWidget(scroll)

        # 设置样式
        self.setStyleSheet("""
            #schedule_scroll {
                border: none;
                background: transparent;
            }
            #add_task_button {
                background: #3B82F6;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
            }
            #add_task_button:hover {
                background: #2563EB;
            }
        """)

    def _load_time_blocks(self):
        """加载时间块"""
        # 从TaskManager获取时间块数据
        blocks_data = self._task_manager.get_time_blocks()

        if blocks_data:
            self._time_blocks = [TimeBlock.from_dict(b) for b in blocks_data]
        else:
            # 如果没有保存的时间块，则重新生成
            self._regenerate_time_blocks()

        self._update_timeline()

    def _regenerate_time_blocks(self):
        """重新生成时间块"""
        from src.services.schedule_optimizer import ScheduleOptimizer

        tasks = self._task_manager.get_pending_tasks()
        work_start_str = self._config.get_work_start_time()
        work_end_str = self._config.get_work_end_time()

        # 解析时间
        start_hour, start_min = map(int, work_start_str.split(':'))
        end_hour, end_min = map(int, work_end_str.split(':'))

        now = datetime.now()
        work_start = now.replace(hour=start_hour, minute=start_min, second=0)
        work_end = now.replace(hour=end_hour, minute=end_min, second=0)

        # 生成时间块
        self._time_blocks = ScheduleOptimizer.allocate_time_blocks(
            tasks, work_start, work_end
        )

        # 保存到TaskManager
        blocks_data = [b.to_dict() for b in self._time_blocks]
        self._task_manager.set_time_blocks(blocks_data)

    def _update_timeline(self):
        """更新时间轴显示"""
        # 清除旧的项目
        while self._timeline_layout.count():
            item = self._timeline_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        if not self._time_blocks:
            # 没有时间块显示提示
            empty_label = QLabel("暂无计划，点击\"+ 添加\"添加任务")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #9CA3AF; padding: 20px;")
            self._timeline_layout.addWidget(empty_label)
            return

        # 当前时间
        now = datetime.now()

        # 添加时间块
        for block in self._time_blocks:
            block_widget = TimeBlockWidget(block, now)
            block_widget.clicked.connect(self._on_block_clicked)
            self._timeline_layout.addWidget(block_widget)

        self._timeline_layout.addStretch()

    def _on_block_clicked(self, block_id: str):
        """时间块点击事件"""
        self.task_clicked.emit(block_id)

    def refresh(self):
        """刷新时间轴"""
        self._regenerate_time_blocks()
        self._update_timeline()


class TimeBlockWidget(QFrame):
    """时间块组件"""

    clicked = Signal(str)

    def __init__(self, block: TimeBlock, current_time: datetime, parent=None):
        super().__init__(parent)
        self._block = block
        self._current_time = current_time
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.setObjectName("time_block")
        self.setFixedHeight(50)
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 5, 10, 5)

        # 时间显示
        time_label = QLabel(format_time_range(self._block.start, self._block.end))
        time_label.setObjectName("time_label")
        time_label.setFixedWidth(90)
        layout.addWidget(time_label)

        # 描述
        desc_label = QLabel(self._block.description or "未命名")
        desc_label.setObjectName("description_label")
        desc_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(desc_label, 1)

        # 设置颜色
        self._set_block_color()

    def _set_block_color(self):
        """设置块颜色"""
        if self._block.type == BlockType.WORK:
            color = "#3B82F6"  # 蓝色
        elif self._block.type == BlockType.BREAK:
            color = "#22C55E"  # 绿色
        else:
            color = "#F59E0B"  # 黄色

        # 如果是当前时间块，添加边框
        if self._current_time and self._block.start <= self._current_time <= self._block.end:
            self.setStyleSheet(f"""
                #time_block {{
                    background: {color}20;
                    border-left: 4px solid {color};
                    border-radius: 4px;
                    margin-left: 10px;
                }}
                #time_label {{
                    color: {color};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                #time_block {{
                    background: #F3F4F6;
                    border-left: 4px solid {color};
                    border-radius: 4px;
                    margin-left: 10px;
                }}
                #time_label {{
                    color: {color};
                }}
            """)

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._block.id)
        super().mousePressEvent(event)
