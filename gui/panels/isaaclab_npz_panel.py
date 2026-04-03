import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ISAACLAB_DIR = os.path.join(_PROJECT_ROOT, 'input_isaaclab_beyondmimic_csv_npz')
if _ISAACLAB_DIR not in sys.path:
    sys.path.insert(0, _ISAACLAB_DIR)

from PyQt5.QtWidgets import QVBoxLayout, QFormLayout, QGroupBox

from gui.base_panel import BasePanel
from gui.widgets.file_picker import FilePicker


class IsaaclabNpzPanel(BasePanel):
    """IsaacLab NPZ → CSV：仅提取 base body 数据，输出 61 列 CSV。"""

    PANEL_TITLE = "IsaacLab NPZ→CSV"
    PANEL_GROUP = "Import"

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        group = QGroupBox("参数")
        form = QFormLayout(group)

        self._input = FilePicker("输入 NPZ 文件:", filter="NPZ files (*.npz)")
        self._output = FilePicker("输出 CSV 文件:", filter="CSV files (*.csv)", save_mode=True)

        form.addRow(self._input)
        form.addRow(self._output)
        layout.addWidget(group)
        self._add_run_button(layout, "执行转换")

    def get_params(self) -> dict:
        npz = self._input.path()
        csv = self._output.path() or (npz.replace(".npz", ".csv") if npz else "")
        return {"npz_path": npz, "output_csv_name": csv}

    def validate(self) -> tuple:
        p = self.get_params()
        if not p["npz_path"]:
            return False, "请选择输入 NPZ 文件"
        if not os.path.exists(p["npz_path"]):
            return False, f"文件不存在: {p['npz_path']}"
        return True, ""

    def _execute(self, params: dict):
        from isaaclab_beyondmimic_npz2csv_no_estimate import export_all_to_one_csv
        export_all_to_one_csv(
            npz_path=params["npz_path"],
            output_csv_name=params["output_csv_name"],
        )
