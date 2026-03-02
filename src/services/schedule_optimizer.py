"""智能时间块分配器"""
from datetime import datetime, timedelta
from typing import List, Optional
import uuid

from src.models.task import Task, Priority
from src.models.time_block import TimeBlock, BlockType


class ScheduleOptimizer:
    """智能时间块分配器"""

    # 优先级分数
    PRIORITY_SCORE = {
        Priority.HIGH: 3,
        Priority.MEDIUM: 2,
        Priority.LOW: 1
    }

    # 黄金时间（上午精力充沛时段）
    GOLDEN_HOURS_START = 9
    GOLDEN_HOURS_END = 11

    @classmethod
    def allocate_time_blocks(
        cls,
        tasks: List[Task],
        work_start: datetime,
        work_end: datetime,
        break_interval: int = 90,
        break_duration: int = 15
    ) -> List[TimeBlock]:
        """
        智能分配时间块

        Args:
            tasks: 任务列表
            work_start: 上班时间
            work_end: 下班时间
            break_interval: 休息间隔（分钟）
            break_duration: 休息时长（分钟）

        Returns:
            分配好的时间块数组
        """
        # 过滤掉已完成和没有预计时间的任务
        valid_tasks = [t for t in tasks if not t.completed and t.estimated_minutes > 0]

        if not valid_tasks:
            return []

        # 1. 分离高优先级任务和其他任务
        high_priority_tasks = [t for t in valid_tasks if t.priority == Priority.HIGH]
        other_tasks = [t for t in valid_tasks if t.priority != Priority.HIGH]

        # 2. 高优先级任务优先安排在黄金时间
        golden_tasks, remaining_tasks = cls._allocate_golden_time_tasks(
            high_priority_tasks, work_start, work_end
        )

        # 3. 按优先级和截止时间排序其他任务
        sorted_tasks = cls._sort_tasks(remaining_tasks + other_tasks)

        blocks = []
        current_time = work_start

        # 4. 安排黄金时间任务
        for task in golden_tasks:
            block = cls._create_work_block(task, current_time)
            blocks.append(block)
            current_time = block.end

        # 5. 安排剩余任务
        for task in sorted_tasks:
            # 检查是否需要休息时间
            if cls._should_add_break(current_time, blocks, break_interval):
                break_block = cls._create_break_block(current_time, break_duration)
                blocks.append(break_block)
                current_time = break_block.end

            # 创建工作块
            work_block = cls._create_work_block(task, current_time)

            # 检查是否超出下班时间
            if work_block.end > work_end:
                remaining_minutes = int((work_end - current_time).total_seconds() / 60)
                if remaining_minutes >= 15:
                    work_block.end = work_end
                    blocks.append(work_block)
                break

            blocks.append(work_block)
            current_time = work_block.end

        return blocks

    @classmethod
    def _allocate_golden_time_tasks(
        cls,
        tasks: List[Task],
        work_start: datetime,
        work_end: datetime
    ) -> tuple:
        """
        分配黄金时间任务

        Args:
            tasks: 高优先级任务列表
            work_start: 上班时间
            work_end: 下班时间

        Returns:
            (黄金时间任务, 剩余任务)
        """
        golden_start = work_start.replace(
            hour=cls.GOLDEN_HOURS_START,
            minute=0,
            second=0,
            microsecond=0
        ) if work_start.hour < cls.GOLDEN_HOURS_START else work_start

        golden_end = work_start.replace(
            hour=cls.GOLDEN_HOURS_END,
            minute=0,
            second=0,
            microsecond=0
        )

        if golden_end > work_end:
            golden_end = work_end

        golden_time_minutes = int((golden_end - golden_start).total_seconds() / 60)

        golden_tasks = []
        remaining_tasks = []
        used_minutes = 0

        # 按优先级排序
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (
                -cls.PRIORITY_SCORE[t.priority],
                t.deadline if t.deadline else datetime.max,
                t.estimated_minutes
            )
        )

        for task in sorted_tasks:
            if used_minutes + task.estimated_minutes <= golden_time_minutes:
                golden_tasks.append(task)
                used_minutes += task.estimated_minutes
            else:
                remaining_tasks.append(task)

        return golden_tasks, remaining_tasks

    @classmethod
    def _sort_tasks(cls, tasks: List[Task]) -> List[Task]:
        """排序任务：优先级 > deadline > 预计时长"""
        return sorted(
            tasks,
            key=lambda t: (
                -cls.PRIORITY_SCORE[t.priority],
                t.deadline if t.deadline else datetime.max,
                t.estimated_minutes
            )
        )

    @classmethod
    def _should_add_break(
        cls,
        current_time: datetime,
        blocks: List[TimeBlock],
        interval_minutes: int
    ) -> bool:
        """检查是否应该添加休息时间"""
        if not blocks:
            return False

        # 找到上一个工作块
        last_work_block = None
        for block in reversed(blocks):
            if block.type == BlockType.WORK:
                last_work_block = block
                break

        if not last_work_block:
            return False

        # 计算从上一个工作块开始到现在的时间
        elapsed_minutes = (current_time - last_work_block.start).total_seconds() / 60

        return elapsed_minutes >= interval_minutes

    @classmethod
    def _create_break_block(cls, start_time: datetime, duration: int = 15) -> TimeBlock:
        """创建休息时间块"""
        return TimeBlock(
            id=f"break-{uuid.uuid4().hex[:8]}",
            start=start_time,
            end=start_time + timedelta(minutes=duration),
            type=BlockType.BREAK,
            description="休息时间"
        )

    @classmethod
    def _create_work_block(cls, task: Task, start_time: datetime) -> TimeBlock:
        """创建工作块"""
        return TimeBlock(
            id=task.id,
            start=start_time,
            end=start_time + timedelta(minutes=task.estimated_minutes),
            task_id=task.id,
            type=BlockType.WORK,
            description=task.title
        )

    @classmethod
    def get_current_block(
        cls,
        blocks: List[TimeBlock]
    ) -> Optional[TimeBlock]:
        """
        获取当前时间块

        Args:
            blocks: 时间块列表

        Returns:
            当前时间块，如果没有则返回None
        """
        now = datetime.now()

        for block in blocks:
            if block.start <= now <= block.end:
                return block

        return None

    @classmethod
    def get_upcoming_blocks(
        cls,
        blocks: List[TimeBlock],
        count: int = 3
    ) -> List[TimeBlock]:
        """
        获取即将到来的时间块

        Args:
            blocks: 时间块列表
            count: 获取数量

        Returns:
            即将到来的时间块列表
        """
        now = datetime.now()
        upcoming = [b for b in blocks if b.start > now]
        return sorted(upcoming, key=lambda b: b.start)[:count]
