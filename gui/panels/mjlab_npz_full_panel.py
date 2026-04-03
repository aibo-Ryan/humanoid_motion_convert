import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MJLAB_DIR = os.path.join(_PROJECT_ROOT, 'input_mjlab_beyondmimic_csv_npz')
if _MJLAB_DIR not in sys.path:
    sys.path.insert(0, _MJLAB_DIR)

from PyQt5.QtWidgets import QVBoxLayout, QFormLayout, QGroupBox

from gui.base_panel import BasePanel
from gui.widgets.file_picker import FilePicker


class MjlabNpzFullPanel(BasePanel):
    """MJLab NPZ → CSV（全量）：展开所有 body 数据，输出 425 列 CSV。"""

    PANEL_TITLE = "MJLab NPZ→CSV Full"
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
        csv = self._output.path() or (npz.replace(".npz", "_full.csv") if npz else "")
        return {"npz_path": npz, "output_csv_name": csv}

    def validate(self) -> tuple:
        p = self.get_params()
        if not p["npz_path"]:
            return False, "请选择输入 NPZ 文件"
        if not os.path.exists(p["npz_path"]):
            return False, f"文件不存在: {p['npz_path']}"
        return True, ""

    def _execute(self, params: dict):
        from mjlab_beyondmimic_npz2csv import export_all_to_one_csv
        export_all_to_one_csv(
            npz_path=params["npz_path"],
            output_csv_name=params["output_csv_name"],
        )
