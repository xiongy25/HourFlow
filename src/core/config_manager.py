"""配置管理器"""
import json
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """配置管理器（单例模式）"""

    _instance: Optional['ConfigManager'] = None
    _config: Dict[str, Any] = {}
    _config_path: Optional[Path] = None

    # 默认配置
    DEFAULT_CONFIG = {
        # 工作时间设置（修改默认值为9:30-19:00）
        "work_start_time": "09:30",
        "work_end_time": "19:00",
        "work_days": [1, 2, 3, 4, 5],  # 周一到周五

        # 午休时间设置（新增）
        "lunch_break_enabled": True,
        "lunch_break_start": "12:00",
        "lunch_break_end": "13:30",

        # 久坐提醒设置
        "sedentary_reminder_enabled": True,
        "sedentary_reminder_interval": 45,  # 分钟
        "sedentary_reminder_sound": True,

        # 系统托盘设置
        "minimize_to_tray": True,
        "start_minimized": False,
        "tray_show_countdown": True,

        # 主题设置
        "theme": "light",
        "accent_color": "#3B82F6",  # 蓝色

        # 通知设置
        "notifications_enabled": True,
        "notification_duration": 3000,  # 毫秒

        # 窗口透明度设置
        "window_opacity": 1.0,  # 0.0-1.0，1.0为不透明
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化配置管理器"""
        if not self._config:
            self._load_config()

    def _get_default_config_path(self) -> Path:
        """获取默认配置文件路径"""
        home = Path.home()
        config_dir = home / '.work-assistant'
        config_dir.mkdir(exist_ok=True)
        return config_dir / 'config.json'

    def _load_config(self):
        """从文件加载配置"""
        self._config_path = self._get_default_config_path()

        if self._config_path.exists():
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    self._config = {**self.DEFAULT_CONFIG, **loaded_config}
            except Exception:
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            self._config = self.DEFAULT_CONFIG.copy()

    def _save_config(self):
        """保存配置到文件"""
        if self._config_path is None:
            self._config_path = self._get_default_config_path()

        self._config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self._config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """设置配置值"""
        self._config[key] = value
        self._save_config()

    def get_work_start_time(self) -> str:
        """获取上班时间"""
        return self.get("work_start_time", "09:30")

    def get_work_end_time(self) -> str:
        """获取下班时间"""
        return self.get("work_end_time", "19:00")

    def get_work_days(self) -> list:
        """获取工作日列表"""
        return self.get("work_days", [1, 2, 3, 4, 5])

    # 午休时间相关方法
    def is_lunch_break_enabled(self) -> bool:
        """是否启用午休时间"""
        return self.get("lunch_break_enabled", True)

    def get_lunch_break_start(self) -> str:
        """获取午休开始时间"""
        return self.get("lunch_break_start", "12:00")

    def get_lunch_break_end(self) -> str:
        """获取午休结束时间"""
        return self.get("lunch_break_end", "13:30")

    def is_sedentary_reminder_enabled(self) -> bool:
        """是否启用久坐提醒"""
        return self.get("sedentary_reminder_enabled", True)

    def get_sedentary_interval(self) -> int:
        """获取久坐提醒间隔（分钟）"""
        return self.get("sedentary_reminder_interval", 45)

    def is_minimize_to_tray(self) -> bool:
        """是否最小化到托盘"""
        return self.get("minimize_to_tray", True)

    def get_theme(self) -> str:
        """获取主题"""
        return self.get("theme", "light")

    def get_accent_color(self) -> str:
        """获取主题色"""
        return self.get("accent_color", "#3B82F6")

    def get_window_opacity(self) -> float:
        """获取窗口透明度"""
        return self.get("window_opacity", 1.0)

    def set_window_opacity(self, opacity: float):
        """设置窗口透明度"""
        self.set("window_opacity", max(0.1, min(1.0, opacity)))

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()

    def reset_to_default(self):
        """重置为默认配置"""
        self._config = self.DEFAULT_CONFIG.copy()
        self._save_config()

    def update_from_dict(self, config_dict: Dict[str, Any]):
        """从字典更新配置"""
        self._config.update(config_dict)
        self._save_config()
