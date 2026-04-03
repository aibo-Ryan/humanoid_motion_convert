from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QTabWidget, QSplitter, QPushButton,
                               QHBoxLayout, QLabel, QStatusBar)
from PyQt5.QtCore import Qt

from gui.widgets.log_widget import LogWidget
from gui.registry import PANEL_REGISTRY


class MainWindow(QMainWindow):
    """
    主窗口：自动从 PANEL_REGISTRY 创建标签页，共用底部日志区。

    布局：
        ┌──────────────────────────────────────────────┐
        │  [Tab1] [Tab2] [Tab3] ...                    │
        ├──────────────────────────────────────────────┤
        │  Panel 专属控件 + 执行按钮                    │
        ├──────────────────────────────────────────────┤
        │  [清空日志]                                   │
        │  日志输出区（所有 tab 共用）                   │
        └──────────────────────────────────────────────┘
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Motion Target Tools")
        self.resize(1280, 720)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(4)

        # 上下可拖拽分割
        splitter = QSplitter(Qt.Vertical)

        # ── 标签页区域 ──────────────────────────────────────────────────────
        self._tabs = QTabWidget()
        self._panels = []
        for entry in PANEL_REGISTRY:
            panel = entry.cls()
            self._panels.append(panel)
            self._tabs.addTab(panel, entry.tab_label)

        splitter.addWidget(self._tabs)

        # ── 日志区域 ────────────────────────────────────────────────────────
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 4, 0, 0)
        log_layout.setSpacing(2)

        log_header = QHBoxLayout()
        log_label = QLabel("运行日志")
        log_label.setStyleSheet("font-weight: bold;")
        clear_btn = QPushButton("清空日志")
        clear_btn.setFixedWidth(80)
        log_header.addWidget(log_label)
        log_header.addStretch()
        log_header.addWidget(clear_btn)

        self._log = LogWidget()
        clear_btn.clicked.connect(self._log.clear_log)

        log_layout.addLayout(log_header)
        log_layout.addWidget(self._log)

        splitter.addWidget(log_container)
        splitter.setSizes([420, 260])

        main_layout.addWidget(splitter)

        # ── 连接所有 panel 的 log_line 信号到日志区 ─────────────────────────
        for panel in self._panels:
            panel.log_line.connect(self._log.append_text)

        # ── 状态栏 ───────────────────────────────────────────────────────────
        status_bar = QStatusBar()
        status_bar.showMessage(f"已加载 {len(self._panels)} 个功能面板")
        self.setStatusBar(status_bar)
