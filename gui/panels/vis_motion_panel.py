import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
                               QComboBox, QDoubleSpinBox, QStackedWidget,
                               QWidget, QLabel)

from gui.widgets.subprocess_runner import SubprocessPanel
from gui.widgets.file_picker import FilePicker

# 默认资源路径
_DEFAULT_XML = os.path.join(_PROJECT_ROOT, 'pm01_description', 'xml', 'serial_pm_v2_merged.xml')
_DEFAULT_URDF = os.path.join(_PROJECT_ROOT, 'pm01_description', 'urdf', 'serial_pm_v2.urdf')

# 机器人类型 → 可用显示软件
_VIEWER_OPTIONS = {
    "PM01": ["Mujoco", "IsaacGym"],
    "H1":   ["IsaacGym"],
}


class VisMotionPanel(SubprocessPanel):
    """运动可视化：选择机器人类型和显示软件，回放 PKL 运动数据。"""

    PANEL_TITLE = "运动可视化"
    PANEL_GROUP = "Visualization"
    IS_SUBPROCESS = True

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        # ── 运动数据文件 ──
        self._motion_file = FilePicker("运动数据文件:", filter="PKL files (*.pkl)")
        layout.addWidget(self._motion_file)

        # ── 显示配置 ──
        config_group = QGroupBox("显示配置")
        config_form = QFormLayout(config_group)

        self._robot_combo = QComboBox()
        self._robot_combo.addItems(list(_VIEWER_OPTIONS.keys()))
        self._robot_combo.currentTextChanged.connect(self._on_robot_changed)

        self._viewer_combo = QComboBox()

        config_form.addRow("机器人类型:", self._robot_combo)
        config_form.addRow("显示软件:", self._viewer_combo)
        layout.addWidget(config_group)

        # ── 可视化参数（动态切换区域）──
        param_group = QGroupBox("可视化参数")
        param_layout = QVBoxLayout(param_group)

        self._param_stack = QStackedWidget()

        # Page 0: PM01 + Mujoco 参数
        self._pm01_mujoco = self._build_pm01_mujoco_params()
        self._param_stack.addWidget(self._pm01_mujoco)

        # Page 1: PM01 + IsaacGym 参数
        self._pm01_isaacgym = self._build_pm01_isaacgym_params()
        self._param_stack.addWidget(self._pm01_isaacgym)

        # Page 2: H1 + IsaacGym 参数
        self._h1_isaacgym = self._build_h1_isaacgym_params()
        self._param_stack.addWidget(self._h1_isaacgym)

        param_layout.addWidget(self._param_stack)
        layout.addWidget(param_group)

        # ── 连接切换信号 ──
        self._viewer_combo.currentTextChanged.connect(self._on_viewer_changed)
        self._on_robot_changed(self._robot_combo.currentText())

        # ── 启动/终止按钮 ──
        self._build_subprocess_controls(layout)

    # ── 参数页构建 ──────────────────────────────────────────────────────

    def _build_pm01_mujoco_params(self):
        w = QWidget()
        form = QFormLayout(w)
        self._mj_speed = QDoubleSpinBox()
        self._mj_speed.setRange(0.1, 10.0)
        self._mj_speed.setValue(1.0)
        self._mj_speed.setSingleStep(0.1)
        self._mj_xml = FilePicker("XML 模型文件:", filter="XML files (*.xml)", default=_DEFAULT_XML)
        form.addRow("播放速度:", self._mj_speed)
        form.addRow(self._mj_xml)
        return w

    def _build_pm01_isaacgym_params(self):
        w = QWidget()
        form = QFormLayout(w)
        self._ig_speed = QDoubleSpinBox()
        self._ig_speed.setRange(0.1, 10.0)
        self._ig_speed.setValue(1.0)
        self._ig_speed.setSingleStep(0.1)
        self._ig_preset = QComboBox()
        self._ig_preset.addItems(["all", "lower_body", "upper_body", "legs_only", "arms_only", "key_points"])
        self._ig_urdf = FilePicker("URDF 文件:", filter="URDF files (*.urdf)", default=_DEFAULT_URDF)
        form.addRow("播放速度:", self._ig_speed)
        form.addRow("关节预设:", self._ig_preset)
        form.addRow(self._ig_urdf)
        return w

    def _build_h1_isaacgym_params(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        notice = QLabel(
            "注意：H1 可视化依赖 phc / smpl_sim 库，\n"
            "且运动文件路径当前硬编码在脚本中。\n"
            "请确保相关库已安装，并已在脚本中配置数据路径。"
        )
        notice.setWordWrap(True)
        notice.setStyleSheet("color: #CC6600; padding: 8px;")
        self._h1_speed = QDoubleSpinBox()
        self._h1_speed.setRange(0.1, 10.0)
        self._h1_speed.setValue(1.0)
        self._h1_speed.setSingleStep(0.1)
        form = QFormLayout()
        form.addRow("播放速度:", self._h1_speed)
        layout.addWidget(notice)
        layout.addLayout(form)
        layout.addStretch()
        return w

    # ── 联动切换 ──────────────────────────────────────────────────────

    def _on_robot_changed(self, robot_type):
        """切换机器人类型时，更新可用的显示软件列表。"""
        viewers = _VIEWER_OPTIONS.get(robot_type, [])
        self._viewer_combo.blockSignals(True)
        self._viewer_combo.clear()
        self._viewer_combo.addItems(viewers)
        self._viewer_combo.blockSignals(False)
        self._on_viewer_changed(self._viewer_combo.currentText())

    def _on_viewer_changed(self, viewer_type):
        """切换显示软件时，显示对应的参数页。"""
        robot = self._robot_combo.currentText()
        if robot == "PM01" and viewer_type == "Mujoco":
            self._param_stack.setCurrentIndex(0)
        elif robot == "PM01" and viewer_type == "IsaacGym":
            self._param_stack.setCurrentIndex(1)
        elif robot == "H1" and viewer_type == "IsaacGym":
            self._param_stack.setCurrentIndex(2)

    # ── SubprocessPanel 接口 ──────────────────────────────────────────

    def get_params(self):
        robot = self._robot_combo.currentText()
        viewer = self._viewer_combo.currentText()
        params = {
            "motion_file": self._motion_file.path(),
            "robot_type": robot,
            "viewer_type": viewer,
        }
        if robot == "PM01" and viewer == "Mujoco":
            params["speed_scale"] = self._mj_speed.value()
            params["xml_file"] = self._mj_xml.path()
        elif robot == "PM01" and viewer == "IsaacGym":
            params["speed_scale"] = self._ig_speed.value()
            params["joint_preset"] = self._ig_preset.currentText()
            params["asset_file"] = self._ig_urdf.path()
        elif robot == "H1" and viewer == "IsaacGym":
            params["speed_scale"] = self._h1_speed.value()
        return params

    def validate(self):
        p = self.get_params()
        robot, viewer = p["robot_type"], p["viewer_type"]

        if robot != "H1":
            if not p["motion_file"]:
                return False, "请选择运动数据文件"
            if not os.path.exists(p["motion_file"]):
                return False, "运动数据文件不存在: " + p["motion_file"]

        if robot == "PM01" and viewer == "Mujoco":
            if not p.get("xml_file"):
                return False, "请选择 XML 模型文件"
            if not os.path.exists(p["xml_file"]):
                return False, "XML 文件不存在: " + p["xml_file"]
        elif robot == "PM01" and viewer == "IsaacGym":
            if not p.get("asset_file"):
                return False, "请选择 URDF 文件"
            if not os.path.exists(p["asset_file"]):
                return False, "URDF 文件不存在: " + p["asset_file"]

        return True, ""

    def build_command(self, params):
        python = sys.executable
        robot = params["robot_type"]
        viewer = params["viewer_type"]

        if robot == "PM01" and viewer == "Mujoco":
            script = os.path.join(_PROJECT_ROOT, "vis_motion", "vis_mujoco_motion.py")
            args = [
                script,
                "--motion_file", params["motion_file"],
                "--xml_file", params["xml_file"],
                "--speed_scale", str(params["speed_scale"]),
            ]
        elif robot == "PM01" and viewer == "IsaacGym":
            script = os.path.join(_PROJECT_ROOT, "vis_motion", "vis_pm01_motion.py")
            args = [
                script,
                "--motion_file", params["motion_file"],
                "--asset_file", params["asset_file"],
                "--joint_preset", params["joint_preset"],
                "--speed_scale", str(params["speed_scale"]),
            ]
        elif robot == "H1" and viewer == "IsaacGym":
            script = os.path.join(_PROJECT_ROOT, "vis_motion", "vis_isaacgym_motion.py")
            args = [script]
            if params.get("speed_scale", 1.0) != 1.0:
                args.extend(["--speed_scale", str(params["speed_scale"])])
        else:
            return python, ["--version"]

        return python, args
