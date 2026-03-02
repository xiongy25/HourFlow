"""上班助手 - 主入口文件"""
import sys
import signal
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from src.ui.main_window import MainWindow
from src.core.config_manager import ConfigManager


def main():
    """主函数"""
    # 创建应用
    app = QApplication(sys.argv)

    # 设置应用属性
    app.setApplicationName("上班助手")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("WorkAssistant")

    # 设置属性（用于托盘通知）
    app._tray_icon = None

    # 加载配置
    config = ConfigManager()

    # 创建并显示主窗口
    window = MainWindow()

    # 设置托盘图标引用到应用
    if hasattr(window, '_tray'):
        app._tray_icon = window._tray

    # 显示窗口
    window.show()

    # 处理Ctrl+C信号
    def signal_handler(signum, frame):
        print("\n正在退出...")
        app.quit()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
