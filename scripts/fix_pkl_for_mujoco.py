"""
修复 PKL 运动数据以适配 MuJoCo XML 模型。

问题：
  - PKL 文件：24个关节 DOF
  - MuJoCo XML：31个 qpos（7个floating base + 24个关节）
  - PKL 中的 root_rot 可能是 XYZW 格式，但 MuJoCo 需要 wxyz 格式

修复内容：
  1. 在 dof_pos 前插入 7 维 floating base qpos（位置+四元数）
  2. 转换四元数格式（如果需要）
  3. 保存修复后的数据
"""

import argparse
import joblib
import numpy as np
from pathlib import Path


def fix_pkl_for_mujoco(input_path, output_path=None, verbose=True):
    """修复 PKL 文件以适配 MuJoCo XML 模型。"""
    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path.with_name(input_path.stem + '_fixed' + input_path.suffix)
    
    # 加载数据
    if verbose:
        print(f"加载数据: {input_path}")
    data = joblib.load(input_path)
    
    # 检查基本结构
    fps = data['fps']
    root_pos = np.array(data['root_pos'], dtype=np.float64)
    root_rot = np.array(data['root_rot'], dtype=np.float64)
    dof_pos = np.array(data['dof_pos'], dtype=np.float64)
    
    num_frames = root_pos.shape[0]
    num_dofs = dof_pos.shape[1]
    
    if verbose:
        print(f"原始数据:")
        print(f"  FPS: {fps}")
        print(f"  帧数: {num_frames}")
        print(f"  root_pos: {root_pos.shape}")
        print(f"  root_rot: {root_rot.shape}")
        print(f"  dof_pos: {dof_pos.shape}")
        print(f"  DOF数量: {num_dofs}")
    
    # 检查四元数格式
    # MuJoCo 使用 wxyz 格式，检查第一个四元数
    first_quat = root_rot[0]
    quat_norm = np.linalg.norm(first_quat)
    
    if verbose:
        print(f"\n四元数检查:")
        print(f"  第一个四元数: {first_quat}")
        print(f"  范数: {quat_norm:.6f}")
    
    # 如果四元数范数接近1，但w分量（第4个）不是最大的，可能是 xyzw 格式
    # MuJoCo 约定：wxyz，通常初始姿态是 [1, 0, 0, 0]
    # 如果第4个元素接近1，说明是 wxyz 格式
    # 如果第1-3个元素有较大值而第4个接近0，可能是 xyzw 格式
    if abs(first_quat[3]) > 0.9:  # w 在第4位（索引3），是 wxyz 格式
        if verbose:
            print(f"  ✓ 检测到 wxyz 格式（MuJoCo 格式）")
        quat_mujoco = root_rot
    elif abs(first_quat[0]) > 0.9:  # w 在第1位（索引0），是 xyzw 格式
        if verbose:
            print(f"  ✗ 检测到 xyzw 格式，需要转换为 wxyz")
        # xyzw -> wxyz
        quat_mujoco = root_rot[:, [3, 0, 1, 2]]
    else:
        if verbose:
            print(f"  ? 无法确定格式，假设是 wxyz")
        quat_mujoco = root_rot
    
    # 构建完整的 qpos 数据 [root_pos(3) + root_rot(4) + dof_pos(24)]
    # MuJoCo XML 中的 keyframe 显示 qpos 结构是：
    # [x, y, z, qw, qx, qy, qz, joint0, joint1, ..., joint23]
    qpos_full = np.zeros((num_frames, 7 + num_dofs), dtype=np.float64)
    qpos_full[:, :3] = root_pos
    qpos_full[:, 3:7] = quat_mujoco
    qpos_full[:, 7:] = dof_pos
    
    if verbose:
        print(f"\n修复后:")
        print(f"  qpos_full: {qpos_full.shape}")
        print(f"  结构: [pos(3) + quat(4) + dof({num_dofs})] = {7 + num_dofs}")
        
        # 显示第一帧的详细信息
        print(f"\n第一帧 qpos 样例:")
        print(f"  位置: {qpos_full[0, :3]}")
        print(f"  四元数: {qpos_full[0, 3:7]}")
        print(f"  关节(前6个): {qpos_full[0, 7:13]}")
    
    # 保存修复后的数据
    output_path = Path(output_path)
    output_data = {
        'fps': fps,
        'root_pos': root_pos,
        'root_rot': quat_mujoco,
        'dof_pos': dof_pos,
        'qpos_full': qpos_full,  # 完整的 qpos 向量
        'num_dofs': num_dofs,
        'qpos_size': 7 + num_dofs,
    }
    
    # 保留原始数据中的其他字段
    for key in data:
        if key not in output_data:
            output_data[key] = data[key]
    
    joblib.dump(output_data, output_path)
    
    if verbose:
        print(f"\n✓ 已保存到: {output_path}")
    
    return output_data


def main():
    parser = argparse.ArgumentParser(description="修复 PKL 运动数据以适配 MuJoCo XML 模型")
    parser.add_argument('input', help='输入 PKL 文件路径')
    parser.add_argument('--output', '-o', default=None, help='输出文件路径（默认：输入文件名_fixed.pkl）')
    parser.add_argument('--quiet', '-q', action='store_true', help='减少输出信息')
    
    args = parser.parse_args()
    
    fix_pkl_for_mujoco(args.input, args.output, verbose=not args.quiet)


if __name__ == '__main__':
    main()
