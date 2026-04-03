import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TWIST_PKL_DIR = os.path.join(_PROJECT_ROOT, 'input_twist_pkl')
if _TWIST_PKL_DIR not in sys.path:
    sys.path.insert(0, _TWIST_PKL_DIR)

from PyQt5.QtWidgets import (QVBoxLayout, QFormLayout, QGroupBox,
                               QSpinBox, QComboBox, QRadioButton,
                               QButtonGroup, QHBoxLayout, QStackedWidget, QWidget)

from gui.base_panel import BasePanel
from gui.widgets.file_picker import FilePicker


class PklResamplePanel(BasePanel):
    """PKL 重采样：将 PKL 运动数据插值到目标帧率（LERP 位置/关节，SLERP 旋转）。"""

    PANEL_TITLE = "PKL 重采样"
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

        # 输入路径（单文件 / 批量 两个 widget 切换）
        self._stack = QStackedWidget()
        self._single_input = FilePicker("输入 PKL 文件:", filter="PKL files (*.pkl)")
        self._batch_input = FilePicker("输入文件夹:", dir_mode=True)
        self._stack.addWidget(self._single_input)
        self._stack.addWidget(self._batch_input)
        layout.addWidget(self._stack)

        self._radio_single.toggled.connect(lambda checked: self._stack.setCurrentIndex(0) if checked else None)
        self._radio_batch.toggled.connect(lambda checked: self._stack.setCurrentIndex(1) if checked else None)

        # 参数
        param_group = QGroupBox("参数")
        form = QFormLayout(param_group)

        self._output_fps = QSpinBox()
        self._output_fps.setRange(1, 10000)
        self._output_fps.setValue(500)

        self._device = QComboBox()
        self._device.addItems(["cuda:0", "cpu"])

        form.addRow("目标帧率 (FPS):", self._output_fps)
        form.addRow("计算设备:", self._device)
        layout.addWidget(param_group)

        self._add_run_button(layout, "开始重采样")

    def get_params(self) -> dict:
        return {
            "mode": "single" if self._radio_single.isChecked() else "batch",
            "input_file": self._single_input.path(),
            "input_folder": self._batch_input.path(),
            "output_fps": self._output_fps.value(),
            "device": self._device.currentText(),
        }

    def validate(self) -> tuple:
        p = self.get_params()
        if p["mode"] == "single":
            if not p["input_file"]:
                return False, "请选择输入 PKL 文件"
            if not os.path.exists(p["input_file"]):
                return False, f"文件不存在: {p['input_file']}"
        else:
            if not p["input_folder"]:
                return False, "请选择输入文件夹"
            if not os.path.isdir(p["input_folder"]):
                return False, f"文件夹不存在: {p['input_folder']}"
        return True, ""

    def _execute(self, params: dict):
        from main_pkl_resample import resample_single_file, resample_folder
        if params["mode"] == "single":
            resample_single_file(
                input_file=params["input_file"],
                output_fps=params["output_fps"],
                device=params["device"],
            )
        else:
            resample_folder(
                input_folder=params["input_folder"],
                output_fps=params["output_fps"],
                device=params["device"],
            )
