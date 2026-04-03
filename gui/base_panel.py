from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout
from PyQt5.QtCore import pyqtSignal, QThread, QObject
import traceback


class _InProcessWorker(QObject):
    finished = pyqtSignal(bool, str)

    def __init__(self, fn, params, log_signal):
        super().__init__()
        self.fn = fn
        self.params = params
        self.log_signal = log_signal

    def run(self):
        from gui.widgets.log_widget import capture_stdout
        with capture_stdout(self.log_signal):
            try:
                self.fn(self.params)
                self.finished.emit(True, "")
            except Exception as e:
                self.log_signal.emit(traceback.format_exc())
                self.finished.emit(False, str(e))


class BasePanel(QWidget):
    """
    每个功能面板的基类契约。

    轻量功能（在进程内运行）继承此类并实现 _execute(params)。
    重型功能（需要 subprocess）继承 SubprocessPanel。

    扩展方式：
      1. 在 gui/panels/ 新建一个 panel 文件，继承 BasePanel 或 SubprocessPanel
      2. 在 gui/registry.py 追加一行 PanelEntry
      框架代码无需修改。
    """

    PANEL_TITLE: str = "Unnamed Panel"
    PANEL_GROUP: str = "General"
    IS_SUBPROCESS: bool = False

    log_line = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self) -> None:
        """创建并布局所有 Qt 组件，由 __init__ 调用一次。子类必须覆写。"""
        raise NotImplementedError(f"{self.__class__.__name__} 必须实现 build_ui()")

    def get_params(self) -> dict:
        """返回当前 UI 中的参数值字典，必须在 GUI 线程中调用。子类必须覆写。"""
        raise NotImplementedError(f"{self.__class__.__name__} 必须实现 get_params()")

    def validate(self) -> tuple:
        """
        校验参数合法性。
        返回 (is_valid: bool, error_message: str)。子类必须覆写。
        """
        raise NotImplementedError(f"{self.__class__.__name__} 必须实现 validate()")

    def _add_run_button(self, layout: QVBoxLayout, label: str = "执行"):
        """在 layout 中添加执行按钮（供子类 build_ui 调用）。"""
        self._run_btn = QPushButton(label)
        self._run_btn.clicked.connect(self._on_run_clicked)
        layout.addStretch()
        layout.addWidget(self._run_btn)

    def _execute(self, params: dict) -> None:
        """在 worker 线程中执行实际逻辑，子类覆写此方法。用 print() 输出日志。"""
        raise NotImplementedError

    def _on_run_clicked(self):
        ok, msg = self.validate()
        if not ok:
            self.log_line.emit(f"[错误] {msg}\n")
            return

        params = self.get_params()
        self._run_btn.setEnabled(False)
        self.log_line.emit(f"\n{'='*50}\n开始: {self.PANEL_TITLE}\n{'='*50}\n")

        self._thread = QThread()
        self._worker = _InProcessWorker(self._execute, params, self.log_line)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._on_finished)
        self._thread.start()

    def _on_finished(self, success: bool, message: str):
        self._run_btn.setEnabled(True)
        if success:
            self.log_line.emit(f"\n[完成] {self.PANEL_TITLE}\n")
        else:
            self.log_line.emit(f"\n[失败] {message}\n")
        self.on_run_finished(success, message)

    def on_run_finished(self, success: bool, message: str) -> None:
        """可选 hook：执行完成后在 GUI 线程中调用。"""
        pass
