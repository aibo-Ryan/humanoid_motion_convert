"""
统一的 PKL 运动数据加载工具。

支持四种文件格式：joblib / pickle / torch / numpy
支持两种数据结构：
  - 标准扁平结构：{fps, root_pos, root_rot, dof_pos, ...}
  - ASAP 嵌套结构：{motion_name: {fps, root_trans_offset, dof, root_rot, ...}}

字段自动归一化（ASAP → 标准）：
  root_trans_offset → root_pos
  dof               → dof_pos
"""

import os
import pickle
import sys
import numpy as np

# 兼容性修复：numpy 2.0 将 numpy.core 重命名为 numpy._core
# 需要在导入pickle之前创建模块别名
if not hasattr(np, '_core') and hasattr(np, 'core'):
    # 创建模块别名
    sys.modules['numpy._core'] = np.core
    sys.modules['numpy._core.multiarray'] = np.core.multiarray
    np._core = np.core

# ASAP 格式 → 标准格式的字段映射
_FIELD_MAP = {
    "root_trans_offset": "root_pos",
    "dof": "dof_pos",
}


def load_pkl(path: str, normalize_keys: bool = True) -> dict:
    """
    加载 PKL 运动数据文件，自动检测格式。

    Args:
        path: pkl 文件路径
        normalize_keys: 是否将 ASAP 字段名归一化为标准名称（默认 True）

    Returns:
        dict: 运动数据字典，包含 fps, root_pos, root_rot, dof_pos 等字段
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"文件不存在: {path}")

    data = _load_file(path)

    # 处理嵌套结构：{motion_name: {fps, ...}} → 取第一个
    if isinstance(data, dict) and "fps" not in data:
        nested = {k: v for k, v in data.items() if isinstance(v, dict) and "fps" in v}
        if nested:
            name = list(nested.keys())[0]
            print(f"检测到嵌套结构，使用子项: {name}")
            data = nested[name]

    # 归一化字段名
    if normalize_keys and isinstance(data, dict):
        for old_key, new_key in _FIELD_MAP.items():
            if old_key in data and new_key not in data:
                data[new_key] = data.pop(old_key)

    return data


def _load_file(path: str):
    """按优先级尝试多种加载方式。"""

    # 方式 1: joblib
    try:
        import joblib
        data = joblib.load(path)
        print(f"（以 joblib 方式加载）")
        return data
    except ImportError:
        pass
    except Exception:
        pass

    # 方式 2: 标准 pickle
    try:
        with open(path, "rb") as f:
            data = pickle.load(f)
        print(f"（以 pickle 方式加载）")
        return data
    except (ModuleNotFoundError, pickle.UnpicklingError):
        pass

    # 方式 3: torch
    try:
        import torch
        try:
            data = torch.load(path, map_location="cpu", weights_only=False)
        except TypeError:
            data = torch.load(path, map_location="cpu")
        print(f"（以 torch.load 方式加载）")
        return data
    except Exception:
        pass

    # 方式 4: numpy
    try:
        data = np.load(path, allow_pickle=True).item()
        print(f"（以 numpy 方式加载）")
        return data
    except Exception as e:
        raise RuntimeError(
            f"无法加载文件 {path}，尝试了 joblib / pickle / torch / numpy 四种方式均失败。\n最后错误: {e}")
