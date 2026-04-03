import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TWIST_PKL_DIR = os.path.join(_PROJECT_ROOT, 'input_twist_pkl')
if _TWIST_PKL_DIR not in sys.path:
    sys.path.insert(0, _TWIST_PKL_DIR)

from PyQt5.QtWidgets import QVBoxLayout, QFormLayout, QGroupBox, QSpinBox, QComboBox

from gui.base_panel import BasePanel
from gui.widgets.file_picker import FilePicker

_DEFAULT_XML = os.path.join(_PROJECT_ROOT, 'pm01_description', 'xml', 'serial_pm_v2_merged.xml')


class CsvToPklPanel(BasePanel):
    """CSV 转 PKL：读取 31 列 CSV，通过正向运动学计算 body link 位置，输出 PKL。"""

    PANEL_TITLE = "CSV → PKL"
    PANEL_GROUP = "Conversion"

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        group = QGroupBox("参数")
        form = QFormLayout(group)

        self._input = FilePicker("输入 CSV 文件:", filter="CSV files (*.csv)")
        self._xml = FilePicker("机器人 XML 文件:", filter="XML files (*.xml)", default=_DEFAULT_XML)
        self._output = FilePicker("输出 PKL 文件:", filter="PKL files (*.pkl)", save_mode=True)

        self._fps = QSpinBox()
        self._fps.setRange(1, 10000)
        self._fps.setValue(100)

        self._device = QComboBox()
        self._device.addItems(["cuda:0", "cpu"])

        form.addRow(self._input)
        form.addRow(self._xml)
        form.addRow(self._output)
        form.addRow("帧率 (FPS):", self._fps)
        form.addRow("计算设备:", self._device)

        layout.addWidget(group)
        self._add_run_button(layout, "执行转换")

    def get_params(self) -> dict:
        return {
            "csv_file": self._input.path(),
            "xml_file": self._xml.path(),
            "pkl_file": self._output.path() or None,
            "fps": self._fps.value(),
            "device": self._device.currentText(),
        }

    def validate(self) -> tuple:
        p = self.get_params()
        if not p["csv_file"]:
            return False, "请选择输入 CSV 文件"
        if not os.path.exists(p["csv_file"]):
            return False, f"文件不存在: {p['csv_file']}"
        if not p["xml_file"]:
            return False, "请选择机器人 XML 文件"
        if not os.path.exists(p["xml_file"]):
            return False, f"XML 文件不存在: {p['xml_file']}"
        return True, ""

    def _execute(self, params: dict):
        # 在执行时动态 patch device，kinematics_model 内部硬编码了 cuda:0
        # 通过猴子补丁临时替换，确保 panel 中选择的 device 生效
        import main_csv_to_pkl as _m
        original_fn = _m.qpos_to_motion_data

        device = params["device"]

        def patched_qpos_to_motion_data(qpos_list, xml_file, save_path, fps):
            import numpy as np
            import pickle
            import torch
            from kinematics_model import KinematicsModel

            qpos_list = np.array(qpos_list)
            kinematics_model = KinematicsModel(xml_file, device=device)

            root_pos = qpos_list[:, :3]
            root_rot = qpos_list[:, 3:7]
            dof_pos = qpos_list[:, 7:]
            num_frames = root_pos.shape[0]

            identity_root_pos = torch.zeros((num_frames, 3), device=device)
            identity_root_rot = torch.zeros((num_frames, 4), device=device)
            identity_root_rot[:, -1] = 1.0
            local_body_pos, _ = kinematics_model.forward_kinematics(
                identity_root_pos,
                identity_root_rot,
                torch.from_numpy(dof_pos).to(device=device, dtype=torch.float)
            )
            body_names = kinematics_model.body_names
            print(f'body_names: {body_names}')

            motion_data = {
                "fps": fps,
                "root_pos": root_pos,
                "root_rot": root_rot,
                "dof_pos": dof_pos,
                "local_body_pos": local_body_pos,
                "link_body_list": body_names,
            }
            with open(save_path, "wb") as f:
                pickle.dump(motion_data, f)
            print(f"PKL文件已保存到: {save_path}")

        _m.qpos_to_motion_data = patched_qpos_to_motion_data
        try:
            from main_csv_to_pkl import csv_to_pkl
            csv_to_pkl(
                csv_file=params["csv_file"],
                xml_file=params["xml_file"],
                pkl_file=params["pkl_file"],
                fps=params["fps"],
            )
        finally:
            _m.qpos_to_motion_data = original_fn
