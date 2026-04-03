import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TWIST_PKL_DIR = os.path.join(_PROJECT_ROOT, 'input_twist_pkl')
if _TWIST_PKL_DIR not in sys.path:
    sys.path.insert(0, _TWIST_PKL_DIR)

from PyQt5.QtWidgets import (QVBoxLayout, QFormLayout, QGroupBox,
                               QSpinBox, QRadioButton, QButtonGroup,
                               QHBoxLayout, QStackedWidget)

from gui.base_panel import BasePanel
from gui.widgets.file_picker import FilePicker


class CsvResamplePanel(BasePanel):
    """CSV 重采样：将 CSV 运动数据插值到目标帧率（线性插值）。"""

    PANEL_TITLE = "CSV 重采样"
    PANEL_GROUP = "Resampling"

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        # 模式选择
        mode_group = QGroupBox("处理模式")
        mode_layout = QHBoxLayout(mode_group)
        self._radio_single = QRadioButton("单文件")
        self._radio_batch = QRadioButton("批量（文件夹）")
        self._radio_single.setChecked(True)
        btn_group = QButtonGroup(self)
        btn_group.addButton(self._radio_single)
        btn_group.addButton(self._radio_batch)
        mode_layout.addWidget(self._radio_single)
        mode_layout.addWidget(self._radio_batch)
        mode_layout.addStretch()
        layout.addWidget(mode_group)

        # 输入路径切换
        self._stack = QStackedWidget()
        self._single_input = FilePicker("输入 CSV 文件:", filter="CSV files (*.csv)")
        self._batch_input = FilePicker("输入文件夹:", dir_mode=True)
        self._stack.addWidget(self._single_input)
        self._stack.addWidget(self._batch_input)
        layout.addWidget(self._stack)

        self._radio_single.toggled.connect(lambda checked: self._stack.setCurrentIndex(0) if checked else None)
        self._radio_batch.toggled.connect(lambda checked: self._stack.setCurrentIndex(1) if checked else None)

        # 参数
        param_group = QGroupBox("参数")
        form = QFormLayout(param_group)

        self._input_fps = QSpinBox()
        self._input_fps.setRange(1, 10000)
        self._input_fps.setValue(100)

        self._output_fps = QSpinBox()
        self._output_fps.setRange(1, 10000)
        self._output_fps.setValue(30)

        form.addRow("输入帧率 (FPS):", self._input_fps)
        form.addRow("目标帧率 (FPS):", self._output_fps)
        layout.addWidget(param_group)

        self._add_run_button(layout, "开始重采样")

    def get_params(self) -> dict:
        return {
            "mode": "single" if self._radio_single.isChecked() else "batch",
            "input_file": self._single_input.path(),
            "input_folder": self._batch_input.path(),
            "input_fps": self._input_fps.value(),
            "output_fps": self._output_fps.value(),
        }

    def validate(self) -> tuple:
        p = self.get_params()
        if p["mode"] == "single":
            if not p["input_file"]:
                return False, "请选择输入 CSV 文件"
            if not os.path.exists(p["input_file"]):
                return False, f"文件不存在: {p['input_file']}"
        else:
            if not p["input_folder"]:
                return False, "请选择输入文件夹"
            if not os.path.isdir(p["input_folder"]):
                return False, f"文件夹不存在: {p['input_folder']}"
        return True, ""

    def _execute(self, params: dict):
        from main_csv_resample import resample_single_file, resample_folder
        if params["mode"] == "single":
            resample_single_file(
                input_file=params["input_file"],
                input_fps=params["input_fps"],
                output_fps=params["output_fps"],
            )
        else:
            resample_folder(
                input_folder=params["input_folder"],
                input_fps=params["input_fps"],
                output_fps=params["output_fps"],
            )
