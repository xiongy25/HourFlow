"""任务管理器"""
from typing import List, Optional, Callable, Dict, Any
from pathlib import Path
import json
from datetime import datetime
import uuid

from src.models.task import Task, Priority


class TaskManager:
    """任务管理器（单例模式）"""

    _instance: Optional['TaskManager'] = None
    _tasks: List[Task] = []
    _config_path: Optional[Path] = None
    _listeners: List[Callable] = []
    _time_blocks: List[Dict[str, Any]] = []

    def __new__(cls, config_path: Path = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config_path = config_path or cls._get_default_config_path()
            cls._instance._load_tasks()
        return cls._instance

    @staticmethod
    def _get_default_config_path() -> Path:
        """获取默认配置文件路径"""
        home = Path.home()
        config_dir = home / '.work-assistant'
        config_dir.mkdir(exist_ok=True)
        return config_dir / 'tasks.json'

    def _load_tasks(self):
        """从文件加载任务"""
        if self._config_path.exists():
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._tasks = [Task.from_dict(t) for t in data.get('tasks', [])]
                    self._time_blocks = data.get('time_blocks', [])
            except Exception:
                self._tasks = []
                self._time_blocks = []

    def _save_tasks(self):
        """保存任务到文件"""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'tasks': [t.to_dict() for t in self._tasks],
            'time_blocks': self._time_blocks
        }

        with open(self._config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 通知监听器
        for listener in self._listeners:
            listener()

    def add_task(self, title: str, estimated_minutes: int = 30,
                 priority: Priority = Priority.MEDIUM,
                 deadline: Optional[datetime] = None) -> Task:
        """
        添加任务

        Args:
            title: 任务标题
            estimated_minutes: 预计时长（分钟）
            priority: 优先级
            deadline: 截止时间

        Returns:
            创建的任务
        """
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            estimated_minutes=estimated_minutes,
            priority=priority,
            deadline=deadline,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self._tasks.append(task)
        self._save_tasks()
        return task

    def update_task(self, task_id: str, **updates):
        """更新任务"""
        for task in self._tasks:
            if task.id == task_id:
                for key, value in updates.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                task.updated_at = datetime.now()
                self._save_tasks()
                break

    def delete_task(self, task_id: str):
        """删除任务"""
        self._tasks = [t for t in self._tasks if t.id != task_id]
        self._save_tasks()

    def toggle_task_complete(self, task_id: str):
        """切换任务完成状态"""
        for task in self._tasks:
            if task.id == task_id:
                task.completed = not task.completed
                task.updated_at = datetime.now()
                self._save_tasks()
                break

    def get_tasks(self) -> List[Task]:
        """获取所有任务"""
        return self._tasks.copy()

    def get_pending_tasks(self) -> List[Task]:
        """获取待完成的任务"""
        return [t for t in self._tasks if not t.completed]

    def get_completed_tasks(self) -> List[Task]:
        """获取已完成的任务"""
        return [t for t in self._tasks if t.completed]

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def clear_completed_tasks(self):
        """清除已完成的任务"""
        self._tasks = [t for t in self._tasks if not t.completed]
        self._save_tasks()

    def get_time_blocks(self) -> List[Dict[str, Any]]:
        """获取时间块列表"""
        return self._time_blocks.copy()

    def set_time_blocks(self, blocks: List[Dict[str, Any]]):
        """设置时间块列表"""
        self._time_blocks = blocks
        self._save_tasks()

    def add_listener(self, listener: Callable):
        """添加状态变化监听器"""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: Callable):
        """移除状态变化监听器"""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def get_task_stats(self) -> Dict[str, int]:
        """获取任务统计信息"""
        total = len(self._tasks)
        completed = len([t for t in self._tasks if t.completed])
        pending = total - completed

        return {
            'total': total,
            'completed': completed,
            'pending': pending
        }
