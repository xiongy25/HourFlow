"""时间工具函数"""
from datetime import datetime, time, timedelta
from typing import List, Optional, Tuple


def format_countdown(seconds: int, show_seconds: bool = False) -> str:
    """
    格式化倒计时显示

    Args:
        seconds: 秒数
        show_seconds: 是否显示秒数，默认False不显示

    Returns:
        格式化的字符串 "时:分" 或 "时:分:秒"
    """
    if seconds <= 0:
        return "00:00" if not show_seconds else "00:00:00"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if show_seconds:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{hours:02d}:{minutes:02d}"


def calculate_work_progress(
    work_start_time: str,
    work_end_time: str,
    lunch_break_enabled: bool = True,
    lunch_break_start: str = "12:00",
    lunch_break_end: str = "13:30"
) -> float:
    """
    计算工作时间进度百分比（排除午休时间）

    Args:
        work_start_time: 上班时间 "HH:MM"
        work_end_time: 下班时间 "HH:MM"
        lunch_break_enabled: 是否启用午休
        lunch_break_start: 午休开始时间 "HH:MM"
        lunch_break_end: 午休结束时间 "HH:MM"

    Returns:
        进度百分比 (0-100)
    """
    now = datetime.now()

    start_hour, start_min = map(int, work_start_time.split(':'))
    end_hour, end_min = map(int, work_end_time.split(':'))

    start = now.replace(
        hour=start_hour,
        minute=start_min,
        second=0,
        microsecond=0
    )
    end = now.replace(
        hour=end_hour,
        minute=end_min,
        second=0,
        microsecond=0
    )

    # 如果还未到上班时间
    if now < start:
        return 0.0

    # 如果已经过了下班时间
    if now >= end:
        return 100.0

    # 计算总工作时长（秒）
    total_work_seconds = (end - start).total_seconds()

    # 如果启用午休，减去午休时间
    if lunch_break_enabled:
        lunch_s, lunch_e = map(int, lunch_break_start.split(':'))
        lunch_start = now.replace(hour=lunch_s, minute=lunch_e, second=0, microsecond=0)
        lunch_end = now.replace(hour=lunch_e, minute=0, second=0, microsecond=0) if lunch_e == 0 else now.replace(hour=lunch_e, minute=0, second=0, microsecond=0)

        # 重新解析午餐时间
        lb_start_hour, lb_start_min = map(int, lunch_break_start.split(':'))
        lb_end_hour, lb_end_min = map(int, lunch_break_end.split(':'))
        lunch_start = now.replace(hour=lb_start_hour, minute=lb_start_min, second=0, microsecond=0)
        lunch_end = now.replace(hour=lb_end_hour, minute=lb_end_min, second=0, microsecond=0)

        lunch_duration = (lunch_end - lunch_start).total_seconds()
        total_work_seconds -= lunch_duration

    # 计算已工作时间（秒）
    elapsed_seconds = (now - start).total_seconds()

    # 如果当前在午休时间内，不计算进度
    if lunch_break_enabled:
        lb_start_hour, lb_start_min = map(int, lunch_break_start.split(':'))
        lb_end_hour, lb_end_min = map(int, lunch_break_end.split(':'))
        lunch_start = now.replace(hour=lb_start_hour, minute=lb_start_min, second=0, microsecond=0)
        lunch_end = now.replace(hour=lb_end_hour, minute=lb_end_min, second=0, microsecond=0)

        # 如果在午休前已经工作了一段时间
        if now > lunch_start:
            # 已度过午休时间长度
            if now >= lunch_end:
                elapsed_seconds -= (lunch_end - lunch_start).total_seconds()

    if total_work_seconds <= 0:
        return 0.0

    progress = (elapsed_seconds / total_work_seconds) * 100
    return round(min(max(progress, 0.0), 100.0), 1)


def calculate_time_remaining(
    work_end_hour: int,
    work_end_minute: int = 0,
    lunch_break_enabled: bool = True,
    lunch_break_start: str = "12:00",
    lunch_break_end: str = "13:30"
) -> int:
    """
    计算距离下班的时间（秒），考虑午休时间

    Args:
        work_end_hour: 下班小时（24小时制）
        work_end_minute: 下班分钟
        lunch_break_enabled: 是否启用午休
        lunch_break_start: 午休开始时间 "HH:MM"
        lunch_break_end: 午休结束时间 "HH:MM"

    Returns:
        剩余秒数
    """
    now = datetime.now()
    end_time = now.replace(
        hour=work_end_hour,
        minute=work_end_minute,
        second=0,
        microsecond=0
    )

    # 如果已经过了下班时间，返回0
    if now >= end_time:
        return 0

    # 计算基础剩余时间
    remaining = int((end_time - now).total_seconds())

    # 如果启用午休，减去午休时间
    if lunch_break_enabled:
        lb_start_hour, lb_start_min = map(int, lunch_break_start.split(':'))
        lb_end_hour, lb_end_min = map(int, lunch_break_end.split(':'))

        lunch_start = now.replace(hour=lb_start_hour, minute=lb_start_min, second=0, microsecond=0)
        lunch_end = now.replace(hour=lb_end_hour, minute=lb_end_min, second=0, microsecond=0)

        # 如果当前在午休前，且下班时间在午休后
        if now < lunch_start and end_time > lunch_end:
            lunch_duration = (lunch_end - lunch_start).total_seconds()
            remaining -= int(lunch_duration)
        # 如果当前在午休期间
        elif now >= lunch_start and now < lunch_end:
            remaining += int((lunch_end - now).total_seconds())

    return max(remaining, 0)


def is_workday(work_days: List[int]) -> bool:
    """
    检查当前是否是工作日

    Args:
        work_days: 工作日列表 [1,2,3,4,5] 1=周一, 7=周日

    Returns:
        是否是工作日
    """
    # datetime.weekday() 返回 0-6，0=周一，6=周日
    # 转换为 1=周一，7=周日
    today = datetime.now().weekday() + 1
    return today in work_days


def get_time_period() -> str:
    """
    获取当前时间段

    Returns:
        时间段名称：morning/afternoon/evening
    """
    hour = datetime.now().hour
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    else:
        return "evening"


def get_current_time_string() -> str:
    """
    获取当前时间字符串

    Returns:
        当前时间 "HH:MM:SS"
    """
    return datetime.now().strftime("%H:%M:%S")


def get_current_date_string() -> str:
    """
    获取当前日期字符串

    Returns:
        当前日期 "YYYY-MM-DD"
    """
    return datetime.now().strftime("%Y-%m-%d")


def parse_time_string(time_str: str) -> Tuple[int, int]:
    """
    解析时间字符串为小时和分钟

    Args:
        time_str: 时间字符串 "HH:MM"

    Returns:
        (小时, 分钟) 元组
    """
    parts = time_str.split(':')
    return int(parts[0]), int(parts[1])


def create_datetime_from_time(time_str: str) -> datetime:
    """
    从时间字符串创建当天的datetime

    Args:
        time_str: 时间字符串 "HH:MM"

    Returns:
        datetime对象
    """
    hour, minute = parse_time_string(time_str)
    now = datetime.now()
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)


def format_time_range(start: Optional[datetime], end: Optional[datetime]) -> str:
    """
    格式化时间范围

    Args:
        start: 开始时间
        end: 结束时间

    Returns:
        格式化的字符串 "HH:MM - HH:MM"
    """
    if start is None or end is None:
        return ""
    return f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"


def is_time_in_range(check_time: datetime, start: datetime, end: datetime) -> bool:
    """
    检查时间是否在范围内

    Args:
        check_time: 要检查的时间
        start: 开始时间
        end: 结束时间

    Returns:
        是否在范围内
    """
    return start <= check_time <= end


def get_time_until(target_hour: int, target_minute: int = 0) -> timedelta:
    """
    获取到目标时间的差值

    Args:
        target_hour: 目标小时
        target_minute: 目标分钟

    Returns:
        时间差
    """
    now = datetime.now()
    target = now.replace(
        hour=target_hour,
        minute=target_minute,
        second=0,
        microsecond=0
    )

    if now >= target:
        # 如果已经过了目标时间，返回0
        return timedelta(0)

    return target - now


def get_weekday_name(weekday: int) -> str:
    """
    获取星期几的中文名称

    Args:
        weekday: 星期几 (1=周一, 7=周日)

    Returns:
        中文星期名称
    """
    names = {
        1: "周一",
        2: "周二",
        3: "周三",
        4: "周四",
        5: "周五",
        6: "周六",
        7: "周日"
    }
    return names.get(weekday, "")


def get_today_weekday() -> int:
    """
    获取今天是星期几

    Returns:
        星期几 (1=周一, 7=周日)
    """
    return datetime.now().weekday() + 1
