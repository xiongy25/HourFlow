"""任务数据模型"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class Priority(Enum):
    """任务优先级枚举"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @classmethod
    def from_string(cls, value: str) -> 'Priority':
        """从字符串创建优先级"""
        value = value.lower()
        for item in cls:
            if item.value == value:
                return item
        return cls.MEDIUM  # 默认中等优先级


@dataclass
class Task:
    """任务模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    estimated_minutes: int = 30
    priority: Priority = Priority.MEDIUM
    deadline: Optional[datetime] = None
    completed: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.priority, str):
            self.priority = Priority.from_string(self.priority)
        if isinstance(self.deadline, str):
            self.deadline = datetime.fromisoformat(self.deadline)
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'estimated_minutes': self.estimated_minutes,
            'priority': self.priority.value,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'completed': self.completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """从字典创建任务"""
        # 处理 priority
        priority = data.get('priority', 'medium')
        if isinstance(priority, str):
            priority = Priority.from_string(priority)

        # 处理 deadline
        deadline = data.get('deadline')
        if isinstance(deadline, str):
            deadline = datetime.fromisoformat(deadline)

        # 处理 created_at
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        # 处理 updated_at
        updated_at = data.get('updated_at')
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return cls(
            id=data.get('id', str(uuid.uuid4())),
            title=data.get('title', ''),
            estimated_minutes=data.get('estimated_minutes', 30),
            priority=priority,
            deadline=deadline,
            completed=data.get('completed', False),
            created_at=created_at,
            updated_at=updated_at,
        )
