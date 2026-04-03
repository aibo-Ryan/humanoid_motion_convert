import sys
import io
from contextlib import contextmanager
from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtCore import pyqtSlot


class _SignalStream(io.TextIOBase):
    """将 write() 调用转发为 Qt 信号（线程安全）。"""

    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def write(self, text):
        if text:
            self.signal.emit(text)
        return len(text)

    def flush(self):
        pass


@contextmanager
def capture_stdout(log_line_signal):
    """
    上下文管理器：将 sys.stdout / sys.stderr 重定向到 Qt 信号。
    在 worker 线程中使用，信号会线程安全地更新 GUI 日志区。
    """
    stream = _SignalStream(log_line_signal)
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = stream
    try:
        yield
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class LogWidget(QPlainTextEdit):
    """
    只读的日志输出区。
    通过 append_text(str) 槽接收来自任意线程的文本（Qt 信号槽保证线程安全）。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        font = QFont("Monospace", 9)
        font.setStyleHint(QFont.TypeWriter)
        self.setFont(font)
        self.setMaximumBlockCount(5000)
        self.setPlaceholderText("运行日志将显示在这里...")

    @pyqtSlot(str)
    def append_text(self, text: str):
        self.moveCursor(QTextCursor.End)
        self.insertPlainText(text)
        self.moveCursor(QTextCursor.End)

    def clear_log(self):
        self.clear()
