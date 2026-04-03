import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TWIST_PKL_DIR = os.path.join(_PROJECT_ROOT, 'input_twist_pkl')
if _TWIST_PKL_DIR not in sys.path:
    sys.path.insert(0, _TWIST_PKL_DIR)

from PyQt5.QtWidgets import QVBoxLayout, QFormLayout, QGroupBox

from gui.base_panel import BasePanel
from gui.widgets.file_picker import FilePicker


class PklToCsvPanel(BasePanel):
    """PKL 转 CSV：提取 root_pos + root_rot + dof_pos 合并为 31 列 CSV。"""

    PANEL_TITLE = "PKL → CSV"
    PANEL_GROUP = "Conversion"

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        group = QGroupBox("参数")
        form = QFormLayout(group)

        self._input = FilePicker("输入 PKL 文件:", filter="PKL files (*.pkl)")
        self._output = FilePicker("输出 CSV 文件:", filter="CSV files (*.csv)", save_mode=True)

        form.addRow(self._input)
        form.addRow(self._output)

        layout.addWidget(group)
        self._add_run_button(layout, "执行转换")

    def get_params(self) -> dict:
        return {
            "input_file": self._input.path(),
            "output_file": self._output.path() or None,
        }

    def validate(self) -> tuple:
        p = self.get_params()
        if not p["input_file"]:
            return False, "请选择输入 PKL 文件"
        if not os.path.exists(p["input_file"]):
            return False, f"文件不存在: {p['input_file']}"
        return True, ""

    def _execute(self, params: dict):
        from main_pkl_to_csv import pkl_to_csv
        pkl_to_csv(
            input_file=params["input_file"],
            output_file=params["output_file"],
        )
