"""
Motion Target Tools — GUI 入口

运行方式：
    conda activate zqsa01
    cd /home/abo/rl_workspace/motion_target
    python -m gui.main
"""

import sys
import os

# 确保项目根目录在 sys.path 中，使 gui.xxx 包导入正常工作
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from gui.app import MainWindow


def main():
    # 高 DPI 支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Motion Target Tools")
    app.setOrganizationName("RL Workspace")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
