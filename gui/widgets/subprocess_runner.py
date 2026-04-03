from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import QProcess, pyqtSignal
from gui.base_panel import BasePanel


class SubprocessPanel(BasePanel):
    """
    重型功能面板基类，使用 QProcess 在独立子进程中启动脚本。
    适用于需要特殊 import 顺序的工具（如 isaacgym 必须在 torch 之前导入）。

    子类使用示例（以后扩展 Mujoco/IsaacGym 时）：

        class Sim2SimPanel(SubprocessPanel):
            PANEL_TITLE = "Mujoco 仿真录制"
            IS_SUBPROCESS = True

            def build_ui(self):
                layout = QVBoxLayout(self)
                # ... 添加信息标签等 ...
                self._build_subprocess_controls(layout)

            def get_params(self): return {}
            def validate(self): return True, ""

            def build_command(self, params):
                python = "/home/abo/miniconda3/envs/zqsa01/bin/python"
                script = "/home/abo/rl_workspace/motion_target/sim2motion/sim2sim_pm01.py"
                return python, [script]

    在 registry.py 追加一行即可完成集成，框架无需修改。
    """

    IS_SUBPROCESS = True

    def _build_subprocess_controls(self, layout):
        """在 layout 中添加启动/终止按钮和状态标签。子类在 build_ui 中调用此方法。"""
        btn_layout = QHBoxLayout()
        self._launch_btn = QPushButton("启动")
        self._kill_btn = QPushButton("终止进程")
        self._kill_btn.setEnabled(False)
        self._status_label = QLabel("就绪")

        self._launch_btn.clicked.connect(self._on_launch)
        self._kill_btn.clicked.connect(self._on_kill)

        btn_layout.addWidget(self._launch_btn)
        btn_layout.addWidget(self._kill_btn)
        btn_layout.addWidget(self._status_label)
        btn_layout.addStretch()
        layout.addStretch()
        layout.addLayout(btn_layout)

        self._process = None

    def build_command(self, params: dict) -> tuple:
        """
        返回 (python可执行文件路径, [脚本路径, 参数...])。
        示例：('/path/to/python', ['/path/to/script.py', '--flag', 'val'])
        子类必须覆写此方法。
        """
        raise NotImplementedError(f"{self.__class__.__name__} 必须实现 build_command()")

    def _on_launch(self):
        ok, msg = self.validate()
        if not ok:
            self.log_line.emit(f"[错误] {msg}\n")
            return

        params = self.get_params()
        program, args = self.build_command(params)

        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.finished.connect(self._on_proc_finished)
        self._process.start(program, args)

        self._launch_btn.setEnabled(False)
        self._kill_btn.setEnabled(True)
        self._status_label.setText("运行中...")
        self.log_line.emit(f"\n{'='*50}\n启动: {self.PANEL_TITLE}\n命令: {program} {' '.join(args)}\n{'='*50}\n")

    def _on_kill(self):
        if self._process and self._process.state() != QProcess.NotRunning:
            self._process.kill()
            self.log_line.emit("\n[手动终止] 进程已被终止\n")

    def _on_stdout(self):
        raw = self._process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        self.log_line.emit(raw)

    def _on_proc_finished(self, exit_code, exit_status):
        self._launch_btn.setEnabled(True)
        self._kill_btn.setEnabled(False)
        success = (exit_code == 0)
        self._status_label.setText("完成" if success else f"退出码: {exit_code}")
        self.log_line.emit(f"\n[{'完成' if success else '失败'}] 退出码: {exit_code}\n")
        self.on_run_finished(success, f"exit_code={exit_code}")

    # SubprocessPanel 不使用 _execute，覆写为空实现避免 ABC 报错
    def _execute(self, params: dict) -> None:
        pass
