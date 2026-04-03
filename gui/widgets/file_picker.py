import os
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QFileDialog)


class FilePicker(QWidget):
    """
    可复用的文件/目录选择组件：标签 + 文本框 + 浏览按钮。

    参数：
        label       显示在左侧的标签文字
        filter      文件过滤器（仅 file_mode 生效），如 "PKL files (*.pkl)"
        save_mode   True = 另存为对话框；False = 打开对话框
        dir_mode    True = 选择文件夹（忽略 filter 和 save_mode）
        default     预填充的默认路径
    """

    def __init__(self, label: str = "文件:", filter: str = "All files (*)",
                 save_mode: bool = False, dir_mode: bool = False,
                 default: str = "", parent=None):
        super().__init__(parent)
        self._filter = filter
        self._save_mode = save_mode
        self._dir_mode = dir_mode

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel(label)
        self._label.setMinimumWidth(120)
        self._label.setMaximumWidth(160)

        self._edit = QLineEdit()
        self._edit.setPlaceholderText("点击浏览或直接输入路径...")
        if default:
            self._edit.setText(default)

        self._btn = QPushButton("浏览")
        self._btn.setFixedWidth(60)
        self._btn.clicked.connect(self._on_browse)

        layout.addWidget(self._label)
        layout.addWidget(self._edit)
        layout.addWidget(self._btn)

    def _on_browse(self):
        start_dir = os.path.dirname(self._edit.text()) if self._edit.text() else ""
        if self._dir_mode:
            path = QFileDialog.getExistingDirectory(self, "选择文件夹", start_dir)
        elif self._save_mode:
            path, _ = QFileDialog.getSaveFileName(self, "保存文件", start_dir, self._filter)
        else:
            path, _ = QFileDialog.getOpenFileName(self, "选择文件", start_dir, self._filter)
        if path:
            self._edit.setText(path)

    def path(self) -> str:
        return self._edit.text().strip()

    def set_path(self, path: str):
        self._edit.setText(path)
