import pickle
import numpy as np
import pandas as pd
import os

from types import ModuleType
import numpy as np
import sys
# Patch sys.modules to fake missing modules from numpy 2.x
class FakeModule(ModuleType):
    def __init__(self, name, real=None):
        super().__init__(name)
        if real:
            self.__dict__.update(real.__dict__)

# Patch potentially missing modules
sys.modules['numpy._core'] = FakeModule('numpy._core', np.core if hasattr(np, 'core') else np)
sys.modules['numpy._core.multiarray'] = FakeModule('numpy._core.multiarray', getattr(np.core, 'multiarray', None))

def pkl_to_csv(input_file, output_file=None, output_fps=None):
    """
    将pkl文件转换为csv格式
    CSV格式: 3列base位置 + 4列姿态 + 24列关节角度 = 31列
    
    Args:
        input_file: 输入的pkl文件路径
        output_file: 输出的csv文件路径(可选，默认与输入文件同名)
        output_fps: 输出帧率(可选，如果不插值则使用原帧率)
    """
    # 加载pkl文件（支持 joblib / pickle / torch / numpy 格式）
    from pkl_loader import load_pkl
    motion_data = load_pkl(input_file)

    # 提取数据（字段名已由 load_pkl 自动归一化）
    root_pos = motion_data["root_pos"]  # (N, 3)
    root_rot = motion_data["root_rot"]  # (N, 4)
    dof_pos = motion_data["dof_pos"]    # (N, 24)
    
    # 检查数据维度
    print(f"root_pos shape: {root_pos.shape}")
    print(f"root_rot shape: {root_rot.shape}")
    print(f"dof_pos shape: {dof_pos.shape}")
    
    # 合并数据: 前3列位置 + 4列姿态 + 24列关节角度 = 31列
    motion_data_combined = np.concatenate([
        root_pos,
        root_rot,
        dof_pos
    ], axis=1)
    
    print(f"Combined shape: {motion_data_combined.shape}")

    df = pd.DataFrame(motion_data_combined)

    # 设置输出文件路径
    if output_file is None:
        output_file = input_file.replace(".pkl", ".csv")
    
    # 保存为CSV（不包含索引和列名）
    df.to_csv(output_file, index=False, header=False)
    print(f"CSV文件已保存到: {output_file}")
    print(f"总帧数: {len(df)}")
    print(f"总列数: {len(df.columns)}")

if __name__ == "__main__":
    # 输入pkl文件路径
    input_file = "input_twist_pkl/data/squat_hand/hmr4d_results.pkl"
    
    # 输出csv文件路径(可选)
    # output_file = "input_twist_pkl/data/gvhmr_walk1.csv"
    
    # 转换
    pkl_to_csv(input_file)
