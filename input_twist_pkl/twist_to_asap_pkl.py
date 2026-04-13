"""
TWIST PKL → ASAP PKL 转换工具

将 TWIST 格式的 PKL 文件转换为 ASAP 格式的 PKL 文件。

TWIST 格式 (pickle):
{
    "fps": int,
    "root_pos": (N, 3),
    "root_rot": (N, 4),        # quaternion [w, x, y, z]
    "dof_pos": (N, 24),
    "local_body_pos": (N, 29, 3),
    "link_body_list": [str]    # 29 link names
}

ASAP 格式 (joblib):
{
    "<motion_name>": {
        "fps": int,
        "root_trans_offset": (N, 3),
        "root_rot": (N, 4),
        "dof": (N, 24),
        "joint_vel": (N, 24),
        "body_pos_w": (N, 29, 3),
        "body_quat_w": (N, 29, 4),
        "body_lin_vel_w": (N, 29, 3),
        "body_ang_vel_w": (N, 29, 3),
        "pose_aa": (N, 29, 3),
        "source_format": str
    }
}

转换说明:
- root_pos → root_trans_offset
- root_rot → root_rot (保持不变)
- dof_pos → dof
- local_body_pos → body_pos_w
- 速度字段 (joint_vel, body_lin_vel_w, body_ang_vel_w) 通过有限差分计算
- body_quat_w: 通过正向运动学 (FK) 从 dof_pos 计算每个 body 的全局四元数
- pose_aa 使用 local_body_pos 作为近似
- FPS 默认转换为 50 (ASAP 标准帧率)
"""

import os
import sys
from pathlib import Path

import numpy as np
import pickle
import joblib
import torch


def compute_velocity(data, dt):
    """
    通过中心差分计算速度，边界使用前向/后向差分。

    Args:
        data: numpy array, shape (N, ...)
        dt: 时间步长 (秒)

    Returns:
        vel: numpy array, shape (N, ...), 与输入相同
    """
    N = data.shape[0]
    vel = np.zeros_like(data)

    if N == 1:
        return vel

    # 内部点: 中心差分
    vel[1:-1] = (data[2:] - data[:-2]) / (2 * dt)

    # 边界点: 前向/后向差分
    vel[0] = (data[1] - data[0]) / dt
    vel[-1] = (data[-1] - data[-2]) / dt

    return vel


def twist_to_asap(input_file, output_file=None, target_fps=50, motion_name=None, xml_file=None):
    """
    将 TWIST PKL 文件转换为 ASAP PKL 格式。

    Args:
        input_file: 输入的 TWIST PKL 文件路径
        output_file: 输出的 ASAP PKL 文件路径 (可选，默认与输入文件同名)
        target_fps: 目标帧率 (默认 50，ASAP 标准)
        motion_name: 运动名称 (可选，默认从文件名提取)
        xml_file: MuJoCo XML 文件路径 (用于 FK 计算 body_quat_w)
    """
    # 1. 加载 TWIST PKL 文件
    print(f"正在加载 TWIST PKL 文件: {input_file}")
    with open(input_file, 'rb') as f:
        twist_data = pickle.load(f)

    # 提取必要字段
    def to_numpy(x):
        """Convert tensor or numpy to numpy array."""
        if hasattr(x, 'cpu'):  # PyTorch tensor
            return x.cpu().numpy()
        return np.array(x)

    root_pos = to_numpy(twist_data["root_pos"]).astype(np.float32)       # (N, 3)
    root_rot = to_numpy(twist_data["root_rot"]).astype(np.float32)       # (N, 4)
    # 注意：TWIST 和 ASAP 格式都使用 [x, y, z, w] 四元数约定
    # MuJoCo 使用 [w, x, y, z]，可视化时会在 vis_mujoco_motion.py 中转换
    dof_pos = to_numpy(twist_data["dof_pos"]).astype(np.float32)         # (N, 24)
    local_body_pos = to_numpy(twist_data["local_body_pos"]).astype(np.float32)  # (N, 29, 3)

    num_frames = root_pos.shape[0]
    source_fps = twist_data.get("fps", 30)

    print(f"  源帧率: {source_fps} FPS")
    print(f"  帧数: {num_frames}")
    print(f"  root_pos shape: {root_pos.shape}")
    print(f"  root_rot shape: {root_rot.shape}")
    print(f"  dof_pos shape: {dof_pos.shape}")
    print(f"  local_body_pos shape: {local_body_pos.shape}")

    # 2. 计算时间步长
    dt = 1.0 / target_fps

    # 3. 计算速度字段
    joint_vel = compute_velocity(dof_pos, dt)                           # (N, 24)
    body_lin_vel = compute_velocity(local_body_pos, dt)                 # (N, 29, 3)

    # 角速度：基于 root_rot 四元数差分计算 (简化版，使用有限差分)
    # 注意：这里使用 root_rot 的差分来近似角速度
    body_ang_vel = np.zeros((num_frames, 29, 3), dtype=np.float32)
    # 对于根节点，使用 root_pos 差分作为近似
    root_ang_vel = compute_velocity(root_pos, dt)  # (N, 3) - 实际上是线速度
    # 将所有 body 的角速度初始化为根节点的近似值
    for i in range(29):
        body_ang_vel[:, i, :] = root_ang_vel

    # 4. 构造 body_quat_w 和 body_pos_w - 使用正向运动学 (FK) 计算
    print("\n正在通过 FK 计算 body_pos_w 和 body_quat_w...")
    if xml_file is None:
        # 默认 XML 路径
        project_root = Path(__file__).parent.parent
        xml_file = str(project_root / 'pm01_description' / 'xml' / 'serial_pm_v2_merged.xml')

    if not os.path.exists(xml_file):
        print(f"  ⚠️  XML 文件不存在: {xml_file}")
        print(f"  使用 local_body_pos 作为 body_pos_w 的近似，root_rot 作为 body_quat_w 的近似")
        body_pos_w = local_body_pos
        body_quat_w = np.tile(root_rot[:, np.newaxis, :], (1, 29, 1))
    else:
        print(f"  使用 XML 文件: {xml_file}")
        try:
            from kinematics_model import KinematicsModel

            # 选择设备 (CPU/GPU)
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            print(f"  使用设备: {device}")

            kinematics_model = KinematicsModel(xml_file, device=device)

            # 转换数据到 torch tensor
            root_pos_torch = torch.from_numpy(root_pos).to(device=device, dtype=torch.float)
            root_rot_torch = torch.from_numpy(root_rot).to(device=device, dtype=torch.float)
            dof_pos_torch = torch.from_numpy(dof_pos).to(device=device, dtype=torch.float)

            # FK 计算
            with torch.no_grad():
                body_pos_fk, body_rot_fk = kinematics_model.forward_kinematics(
                    root_pos_torch,
                    root_rot_torch,
                    dof_pos_torch
                )

            # 转换回 numpy - 使用 FK 计算的世界坐标！
            body_pos_w = body_pos_fk.cpu().numpy().astype(np.float32)
            body_quat_w = body_rot_fk.cpu().numpy().astype(np.float32)

            print(f"  ✓ body_pos_w shape: {body_pos_w.shape}")
            print(f"  ✓ body_quat_w shape: {body_quat_w.shape}")

            # 验证四元数范数
            quat_norms = np.linalg.norm(body_quat_w, axis=-1)
            if not np.allclose(quat_norms, 1.0, atol=1e-5):
                print(f"  ⚠️  WARNING: 四元数范数不接近 1! 范围: [{quat_norms.min():.6f}, {quat_norms.max():.6f}]")
                body_quat_w = body_quat_w / quat_norms[..., np.newaxis]
                print(f"  已归一化四元数")
            else:
                print(f"  ✓ 四元数范数检查通过")

            # 对比 FK 计算的 body_pos 与 TWIST 的 local_body_pos
            pos_diff = np.abs(body_pos_w - local_body_pos).max()
            print(f"  FK body_pos vs TWIST local_body_pos 最大差异: {pos_diff:.6f}")
            print(f"  (TWIST 的 local_body_pos 是局部坐标，FK 的是世界坐标，这是预期的)")

            # 打印第一帧的 body 位置验证
            print(f"\n  Frame 0 body positions (world coordinates):")
            for i in [0, 4, 7, 14]:  # 打印 base, knee, foot 等关键点
                print(f"    Body {i:2d}: {body_pos_w[0, i, :]}")

        except Exception as e:
            print(f"  ✗ FK 计算失败: {e}")
            print(f"  使用 local_body_pos 作为 body_pos_w 的近似")
            import traceback
            traceback.print_exc()
            body_pos_w = local_body_pos
            body_quat_w = np.tile(root_rot[:, np.newaxis, :], (1, 29, 1))

    # 5. 构造 pose_aa (axis-angle 姿态)
    # 在 ASAP 中，pose_aa 通常是 29 个关节的 axis-angle 表示
    # 对于 TWIST 转换，我们使用 body_pos_w 作为近似
    pose_aa = body_pos_w.copy()                                     # (N, 29, 3)

    # 6. 构造 ASAP 数据结构
    if motion_name is None:
        motion_name = Path(input_file).stem

    # 额外添加 qpos_full 字段，以便 vis_mujoco_motion.py 直接使用
    # qpos_full = [root_pos(3) + root_rot_mujoco(4) + dof(24)] = 31 维
    # 注意：qpos_full 中的四元数需要转换为 MuJoCo 的 [w, x, y, z] 格式
    root_rot_mujoco = root_rot[:, [3, 0, 1, 2]]  # [x, y, z, w] -> [w, x, y, z]
    qpos_full = np.concatenate([root_pos, root_rot_mujoco, dof_pos], axis=1).astype(np.float64)

    asap_data = {
        motion_name: {
            "fps": target_fps,
            "root_trans_offset": root_pos,
            "root_rot": root_rot,  # ASAP 格式保持 [x, y, z, w]
            "dof": dof_pos,
            "joint_vel": joint_vel,
            "body_pos_w": body_pos_w,
            "body_quat_w": body_quat_w,
            "body_lin_vel_w": body_lin_vel,
            "body_ang_vel_w": body_ang_vel,
            "pose_aa": pose_aa,
            "source_format": "twist_pkl",
            "qpos_full": qpos_full,  # MuJoCo 格式 [w, x, y, z]
        }
    }

    # 7. 确定输出文件路径
    if output_file is None:
        output_file = str(Path(input_file).with_suffix('_asap.pkl'))

    # 8. 保存为 ASAP 格式 (使用 joblib)
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    print(f"\n正在保存 ASAP PKL 文件: {output_file}")
    print(f"  目标帧率: {target_fps} FPS")
    print(f"  motion_name: {motion_name}")
    print(f"  qpos_full shape: {qpos_full.shape}")
    joblib.dump(asap_data, output_file)

    print(f"\n转换完成!")
    print(f"  输出文件: {output_file}")
    print(f"  数据大小: {os.path.getsize(output_file) / 1024:.1f} KB")

    return output_file


if __name__ == "__main__":
    # 示例用法
    input_pkl = "input_asap_pkl/data/pm01_walk3_subject1_twist.pkl"
    output_pkl = "input_asap_pkl/data/pm01_walk3_subject1_asap_converted.pkl"

    twist_to_asap(
        input_file=input_pkl,
        output_file=output_pkl,
        target_fps=50,
        motion_name="pm01_walk3_subject1"
    )
