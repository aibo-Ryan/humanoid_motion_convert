"""
CSV 数据检查面板 —— 加载 CSV 运动数据文件，解析维度、帧率、字段分布等信息。
"""

import os
import numpy as np
from PyQt5.QtWidgets import QVBoxLayout, QFormLayout, QGroupBox

from gui.base_panel import BasePanel
from gui.widgets.file_picker import FilePicker


# 已知的 CSV 列数 → 结构描述
_KNOWN_FORMATS = {
    31: "PKL 导出 / TWIST 格式: root_pos(3) + root_rot(4) + dof_pos(24)",
    59: "IsaacLab 格式: joint_pos(23) + joint_vel(23) + body_pos(3) + body_quat(4) + body_lin_vel(3) + body_ang_vel(3)",
    61: "MJLab / BeyondMimic 格式: joint_pos(24) + joint_vel(24) + body_pos(3) + body_quat(4) + body_lin_vel(3) + body_ang_vel(3)",
}


class CsvInspectPanel(BasePanel):
    """CSV 数据检查：加载 CSV 文件并打印帧数、列数、格式推断、统计信息等。"""

    PANEL_TITLE = "CSV 数据检查"
    PANEL_GROUP = "Utilities"

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        group = QGroupBox("参数")
        form = QFormLayout(group)
        self._input = FilePicker("输入 CSV 文件:", filter="CSV files (*.csv)")
        form.addRow(self._input)
        layout.addWidget(group)
        self._add_run_button(layout, "加载并检查")

    def get_params(self) -> dict:
        return {"input_file": self._input.path()}

    def validate(self) -> tuple:
        p = self.get_params()
        if not p["input_file"]:
            return False, "请选择输入 CSV 文件"
        if not os.path.exists(p["input_file"]):
            return False, f"文件不存在: {p['input_file']}"
        return True, ""

    def _execute(self, params: dict):
        path = params["input_file"]
        print(f"加载文件: {path}")

        # 用 numpy 加载，自动跳过头部注释行
        try:
            data = np.loadtxt(path, delimiter=",")
        except ValueError as e:
            # 尝试用 pandas 加载（处理可能的非数字头行）
            try:
                import pandas as pd
                df = pd.read_csv(path, header=None)
                data = df.to_numpy(dtype=float)
                print(f"（以 pandas 方式加载，共 {df.shape[0]} 行）")
            except Exception:
                raise RuntimeError(f"CSV 解析失败，请检查文件格式。\nnumpy 错误: {e}")

        if data.ndim == 1:
            data = data.reshape(1, -1)

        rows, cols = data.shape
        print(f"\n{'=' * 50}")
        print(f"  基本结构")
        print(f"{'=' * 50}")
        print(f"数据行数（帧数）: {rows}")
        print(f"数据列数        : {cols}")

        # 推断格式
        fmt_desc = _KNOWN_FORMATS.get(cols, None)
        if fmt_desc:
            print(f"\n{'=' * 50}")
            print(f"  格式推断")
        else:
            print(f"\n{'=' * 50}")
            print(f"  未知格式（列数 {cols} 不在预设模板中）")
        if fmt_desc:
            print(f"匹配: {fmt_desc}")

        # 字段分割建议
        self._print_field_suggestion(cols)

        # 统计信息
        print(f"\n{'=' * 50}")
        print(f"  数据范围（min / max per column）")
        print(f"{'=' * 50}")

        col_min = data.min(axis=0)
        col_max = data.max(axis=0)
        col_mean = data.mean(axis=0)

        for i in range(cols):
            print(f"  col[{i:2d}]: [{col_min[i]:10.4f}, {col_max[i]:10.4f}]  mean={col_mean[i]:10.4f}")

        # 帧率推断（如果有对应的 PKL 或 NPZ 源文件，用户可以手动确认）
        print(f"\n{'=' * 50}")
        print(f"  提示")
        print(f"{'=' * 50}")
        print("CSV 文件不含 FPS 元数据。如需确认帧率，请参考源数据或 resample 后的命名。")

    def _print_field_suggestion(self, cols: int):
        """根据列数给出字段分割建议。"""
        print(f"\n字段分割建议:")
        if cols == 31:
            print("  root_pos  : col[0:3]   (3)  根位置 xyz")
            print("  root_rot  : col[3:7]   (4)  根四元数 wxyz")
            print("  dof_pos   : col[7:31]  (24) 关节角度")
        elif cols == 59:
            print("  joint_pos  : col[0:23]  (23) 关节位置")
            print("  joint_vel  : col[23:46] (23) 关节速度")
            print("  body_pos   : col[46:49] (3)  根位置 xyz")
            print("  body_quat  : col[49:53] (4)  根四元数 wxyz")
            print("  body_lin_vel  : col[53:56] (3) 线速度")
            print("  body_ang_vel: col[56:59] (3) 角速度")
        elif cols == 61:
            print("  joint_pos  : col[0:24]  (24) 关节位置")
            print("  joint_vel  : col[24:48] (24) 关节速度")
            print("  body_pos   : col[48:51] (3)  根位置 xyz")
            print("  body_quat  : col[51:55] (4)  根四元数 wxyz")
            print("  body_lin_vel  : col[55:58] (3) 线速度")
            print("  body_ang_vel: col[58:61] (3) 角速度")
        else:
            print(f"  未知列数 {cols}，无法自动分割字段。")
