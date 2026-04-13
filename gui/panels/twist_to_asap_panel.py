import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TWIST_PKL_DIR = os.path.join(_PROJECT_ROOT, 'input_twist_pkl')
_DEFAULT_XML = os.path.join(_PROJECT_ROOT, 'pm01_description', 'xml', 'serial_pm_v2_merged.xml')

if _TWIST_PKL_DIR not in sys.path:
    sys.path.insert(0, _TWIST_PKL_DIR)

from PyQt5.QtWidgets import QVBoxLayout, QFormLayout, QGroupBox, QHBoxLayout
from PyQt5.QtWidgets import QSpinBox, QLabel

from gui.base_panel import BasePanel
from gui.widgets.file_picker import FilePicker


class TwistToAsapPanel(BasePanel):
    """TWIST PKL 转 ASAP PKL：转换运动数据格式并计算速度字段。"""

    PANEL_TITLE = "TWIST → ASAP"
    PANEL_GROUP = "Conversion"

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        group = QGroupBox("参数")
        form = QFormLayout(group)

        self._input = FilePicker("输入 TWIST PKL 文件:", filter="PKL files (*.pkl)")
        self._output = FilePicker("输出 ASAP PKL 文件:", filter="PKL files (*.pkl)", save_mode=True)

        # 目标帧率
        fps_layout = QHBoxLayout()
        self._fps_spin = QSpinBox()
        self._fps_spin.setRange(10, 200)
        self._fps_spin.setValue(50)
        self._fps_spin.setSuffix(" FPS")
        fps_layout.addWidget(self._fps_spin)
        fps_layout.addStretch()
        fps_layout.addWidget(QLabel("(ASAP 标准: 50 FPS)"))

        # 运动名称
        self._motion_name = FilePicker("运动名称 (可选):", save_mode=False)

        # XML 文件路径 (用于 FK)
        self._xml = FilePicker("MuJoCo XML 文件 (FK 用):", filter="XML files (*.xml)")
        self._xml.set_path(_DEFAULT_XML if os.path.exists(_DEFAULT_XML) else "")

        form.addRow(self._input)
        form.addRow(self._output)
        form.addRow("目标帧率:", fps_layout)
        form.addRow(self._motion_name)
        form.addRow(self._xml)

        layout.addWidget(group)
        self._add_run_button(layout, "执行转换")

    def get_params(self) -> dict:
        return {
            "input_file": self._input.path(),
            "output_file": self._output.path() or None,
            "target_fps": self._fps_spin.value(),
            "motion_name": self._motion_name.path() or None,
            "xml_file": self._xml.path() or None,
        }

    def validate(self) -> tuple:
        p = self.get_params()
        if not p["input_file"]:
            return False, "请选择输入 TWIST PKL 文件"
        if not os.path.exists(p["input_file"]):
            return False, f"文件不存在: {p['input_file']}"
        return True, ""

    def _execute(self, params: dict):
        from twist_to_asap_pkl import twist_to_asap
        twist_to_asap(
            input_file=params["input_file"],
            output_file=params["output_file"],
            target_fps=params["target_fps"],
            motion_name=params["motion_name"],
            xml_file=params["xml_file"],
        )
