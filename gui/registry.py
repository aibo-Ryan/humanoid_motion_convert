"""
面板注册表 —— 唯一的扩展入口。

添加新功能只需两步：
  1. 在 gui/panels/ 下创建新的 panel 文件（继承 BasePanel 或 SubprocessPanel）
  2. 在本文件末尾追加一行 PanelEntry(...)

MainWindow 会自动读取此列表并创建对应的标签页，无需修改框架其他代码。
"""

from dataclasses import dataclass
from typing import Type

from gui.base_panel import BasePanel


@dataclass
class PanelEntry:
    cls: Type[BasePanel]   # panel 类
    tab_label: str         # 标签页文字
    tab_group: str = ""    # 可选分组标识（备用，当前未用于渲染）


# ── 当前已注册的面板 ──────────────────────────────────────────────────────────

from gui.panels.pkl_to_csv_panel     import PklToCsvPanel
from gui.panels.csv_to_pkl_panel     import CsvToPklPanel
from gui.panels.pkl_resample_panel   import PklResamplePanel
from gui.panels.csv_resample_panel   import CsvResamplePanel
from gui.panels.isaaclab_npz_panel   import IsaaclabNpzPanel
from gui.panels.mjlab_npz_base_panel import MjlabNpzBasePanel
from gui.panels.mjlab_npz_full_panel import MjlabNpzFullPanel
from gui.panels.load_data_panel      import LoadDataPanel
from gui.panels.csv_inspect_panel    import CsvInspectPanel
from gui.panels.vis_motion_panel     import VisMotionPanel

PANEL_REGISTRY: list = [
    PanelEntry(PklToCsvPanel,      "PKL → CSV",           "Conversion"),
    PanelEntry(CsvToPklPanel,      "CSV → PKL",           "Conversion"),
    PanelEntry(PklResamplePanel,   "PKL 重采样",           "Resampling"),
    PanelEntry(CsvResamplePanel,   "CSV 重采样",           "Resampling"),
    PanelEntry(IsaaclabNpzPanel,   "IsaacLab NPZ→CSV",    "Import"),
    PanelEntry(MjlabNpzBasePanel,  "MJLab NPZ→CSV",  "Import"),
    PanelEntry(MjlabNpzFullPanel,  "MJLab NPZ→CSV Full",  "Import"),
    PanelEntry(LoadDataPanel,      "PKL 数据检查",         "Utilities"),
    PanelEntry(CsvInspectPanel,    "CSV 数据检查",         "Utilities"),
    PanelEntry(VisMotionPanel,    "运动可视化",           "Visualization"),

    # ── 未来扩展示例（取消注释并创建对应 panel 文件即可）──────────────────────
    # from gui.panels.sim2sim_panel import Sim2SimPanel
    # PanelEntry(Sim2SimPanel,  "Mujoco 仿真录制",  "Simulation"),
]
