"""平台相关工具函数"""
import sys
import platform
from typing import Optional


def get_platform() -> str:
    """
    获取当前操作系统平台

    Returns:
        平台名称：windows, linux, darwin
    """
    return platform.system().lower()


def is_windows() -> bool:
    """是否是Windows系统"""
    return get_platform() == "windows"


def is_linux() -> bool:
    """是否是Linux系统"""
    return get_platform() == "linux"


def is_macos() -> bool:
    """是否是macOS系统"""
    return get_platform() == "darwin"


def get_config_dir() -> str:
    """
    获取配置文件目录

    Returns:
        配置文件目录路径
    """
    import os
    from pathlib import Path

    if is_windows():
        # Windows: %APPDATA%
        return os.environ.get('APPDATA', str(Path.home() / 'AppData' / 'Roaming'))
    elif is_macos():
        # macOS: ~/Library/Application Support
        return str(Path.home() / 'Library' / 'Application Support')
    else:
        # Linux: ~/.config
        return os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))


def get_app_config_dir(app_name: str = "work-assistant") -> str:
    """
    获取应用配置目录

    Args:
        app_name: 应用名称

    Returns:
        应用配置目录路径
    """
    import os
    from pathlib import Path

    config_dir = Path(get_config_dir()) / app_name
    config_dir.mkdir(parents=True, exist_ok=True)
    return str(config_dir)


def get_resource_path(relative_path: str) -> str:
    """
    获取资源文件的绝对路径

    Args:
        relative_path: 相对路径

    Returns:
        绝对路径
    """
    import os

    # 如果是打包后的可执行文件
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        # 开发环境
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)
        )))

    return os.path.join(base_path, relative_path)


def show_notification(title: str, message: str, icon_path: Optional[str] = None):
    """
    显示系统通知

    Args:
        title: 通知标题
        message: 通知内容
        icon_path: 图标路径
    """
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QIcon
        from PySide6.QtCore import QTimer

        # 获取主应用实例
        app = QApplication.instance()
        if app is None:
            return

        # 使用系统托盘显示通知
        tray = getattr(app, '_tray_icon', None)
        if tray and tray.isVisible():
            tray.showMessage(title, message, QIcon(icon_path) if icon_path else None, 3000)
    except Exception:
        pass


def set_auto_start(enabled: bool, app_name: str = "work-assistant") -> bool:
    """
    设置开机自启动

    Args:
        enabled: 是否启用
        app_name: 应用名称

    Returns:
        是否设置成功
    """
    import os
    import subprocess

    if is_windows():
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

            if enabled:
                exe_path = sys.executable
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0,
                                   winreg.KEY_WRITE):
                    winreg.SetValueEx(winreg.HKEY_CURRENT_USER, key_path,
                                     0, winreg.REG_SZ, exe_path)
            else:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0,
                                   winreg.KEY_WRITE):
                    try:
                        winreg.DeleteValue(winreg.HKEY_CURRENT_USER, key_path)
                    except FileNotFoundError:
                        pass
            return True
        except Exception:
            return False

    elif is_linux():
        autostart_dir = Path.home() / '.config' / 'autostart'
        autostart_dir.mkdir(parents=True, exist_ok=True)
        desktop_file = autostart_dir / f"{app_name}.desktop"

        if enabled:
            content = f"""[Desktop Entry]
Type=Application
Name={app_name}
Exec={sys.executable}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
            desktop_file.write_text(content)
        else:
            if desktop_file.exists():
                desktop_file.unlink()
        return True

    elif is_macos():
        # macOS 使用 launchd
        plist_path = Path.home() / 'Library' / 'LaunchAgents' / f"{app_name}.plist"
        if enabled:
            content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{app_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
            plist_path.parent.mkdir(parents=True, exist_ok=True)
            plist_path.write_text(content)
        else:
            if plist_path.exists():
                plist_path.unlink()
        return True

    return False
