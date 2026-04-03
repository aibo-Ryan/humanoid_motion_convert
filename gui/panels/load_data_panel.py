import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QVBoxLayout, QFormLayout, QGroupBox

from gui.base_panel import BasePanel
from gui.widgets.file_picker import FilePicker


class LoadDataPanel(BasePanel):
    """PKL 数据检查：加载 PKL 文件并打印帧率、帧数、body link 列表等基本信息。"""

    PANEL_TITLE = "PKL 数据检查"
    PANEL_GROUP = "Utilities"

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        group = QGroupBox("参数")
        form = QFormLayout(group)
        self._input = FilePicker("输入 PKL 文件:", filter="PKL files (*.pkl)")
        form.addRow(self._input)
        layout.addWidget(group)
        self._add_run_button(layout, "加载并检查")

    def get_params(self) -> dict:
        return {"input_file": self._input.path()}

    def validate(self) -> tuple:
        p = self.get_params()
        if not p["input_file"]:
            return False, "请选择输入 PKL 文件"
        if not os.path.exists(p["input_file"]):
            return False, f"文件不存在: {p['input_file']}"
        return True, ""

    def _execute(self, params: dict):
        _twist_dir = os.path.join(_PROJECT_ROOT, 'input_twist_pkl')
        if _twist_dir not in sys.path:
            sys.path.insert(0, _twist_dir)
        from pkl_loader import load_pkl

        path = params["input_file"]
        print(f"加载文件: {path}")

        # 数据检查面板不做字段归一化，保留原始字段名以便用户看到真实结构
        data = load_pkl(path, normalize_keys=False)

        # 如果是嵌套结构（如 joblib/ASAP 格式：{motion_name: {fps, ...}}），展开所有子项
        if isinstance(data, dict) and "fps" not in data:
            nested = {k: v for k, v in data.items() if isinstance(v, dict)}
            if nested:
                print(f"\n检测到嵌套结构，包含 {len(nested)} 个运动片段:")
                for name, sub in nested.items():
                    self._print_motion_info(name, sub)
                return
        # 普通扁平结构
        self._print_motion_info(os.path.basename(path), data)

    def _print_motion_info(self, title: str, data: dict):
        """打印单个运动数据的信息，兼容多种字段命名。"""
        print(f"\n{'='*50}")
        print(f"  {title}")
        print(f"{'='*50}")

        fps = data.get("fps", "N/A")
        print(f"FPS        : {fps}")

        # 遍历所有字段打印 shape
        for key, val in data.items():
            if key == "fps":
                continue
            if hasattr(val, "shape"):
                print(f"{key:<25}: {val.shape}  dtype={val.dtype}")
            elif isinstance(val, (list, tuple)):
                print(f"{key:<25}: len={len(val)}")
            else:
                print(f"{key:<25}: {repr(val)}")

        # 尝试推断帧数
        for key in ("root_pos", "root_rot", "dof_pos", "root_trans_offset", "dof", "pose_aa"):
            if key in data and hasattr(data[key], "shape"):
                print(f"\n总帧数: {data[key].shape[0]}")
                break

        # body link 列表
        links = data.get("link_body_list", None)
        if links is not None:
            print(f"\nbody link 列表 ({len(links)} 个):")
            for i, name in enumerate(links):
                print(f"  [{i:2d}] {name}")
