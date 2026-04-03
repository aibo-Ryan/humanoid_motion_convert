"""
Mujoco 运动数据回放工具 — PM01 机器人

用法：
    python vis_motion/vis_mujoco_motion.py --motion_file <path.pkl> [--xml_file <path.xml>] [--speed_scale 1.0]

支持 joblib / pickle / torch / numpy 格式的 PKL 文件（通过 pkl_loader 自动检测）。
"""

import argparse
import time
import sys
import os
import numpy as np

# 确保 pkl_loader 可用
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
_TWIST_PKL_DIR = os.path.join(_PROJECT_ROOT, 'input_twist_pkl')
if _TWIST_PKL_DIR not in sys.path:
    sys.path.insert(0, _TWIST_PKL_DIR)

import mujoco
import mujoco_viewer
from pkl_loader import load_pkl


def main():
    parser = argparse.ArgumentParser(description="Mujoco PM01 运动回放")
    parser.add_argument('--motion_file', type=str, required=True, help="PKL 运动数据文件路径")
    parser.add_argument('--xml_file', type=str,
                        default=os.path.join(_PROJECT_ROOT, 'pm01_description', 'xml', 'serial_pm_v2_merged.xml'),
                        help="Mujoco XML 模型文件路径")
    parser.add_argument('--speed_scale', type=float, default=1.0, help="播放速度倍率（默认 1.0）")
    args = parser.parse_args()

    # 加载运动数据
    print(f"加载运动数据: {args.motion_file}")
    motion = load_pkl(args.motion_file)

    fps = motion['fps']

    # 检查是否有预处理的 qpos_full 数据
    if 'qpos_full' in motion:
        print("（检测到 qpos_full 字段，使用修复后的数据）")
        qpos_full = np.array(motion['qpos_full'], dtype=np.float64)
        num_frames = qpos_full.shape[0]
        num_dofs = qpos_full.shape[1] - 7  # 减去 floating base 的 7 个自由度

        root_pos = qpos_full[:, :3]
        root_rot = qpos_full[:, 3:7]
        dof_pos = qpos_full[:, 7:]

        print(f"FPS: {fps}, 总帧数: {num_frames}, 关节数: {num_dofs}")
        print(f"qpos_full: {qpos_full.shape}")
    else:
        # 传统方式：分别加载各个字段
        root_pos = np.array(motion['root_pos'], dtype=np.float64)
        root_rot_raw = np.array(motion['root_rot'], dtype=np.float64)
        dof_pos = np.array(motion['dof_pos'], dtype=np.float64)
        num_frames = root_pos.shape[0]
        num_dofs = dof_pos.shape[1]

        print(f"FPS: {fps}, 总帧数: {num_frames}, 关节数: {num_dofs}")
        print(f"root_pos: {root_pos.shape}, root_rot: {root_rot_raw.shape}, dof_pos: {dof_pos.shape}")
        
        # 检查四元数格式并转换
        # MuJoCo 使用 wxyz 格式，但数据可能是 xyzw 格式
        # 判断方法：如果最后一个元素接近1或-1，说明是 xyzw 格式
        first_quat = root_rot_raw[0]
        if abs(first_quat[3]) > 0.9:  # xyzw 格式
            print("（检测到 xyzw 四元数格式，转换为 MuJoCo 的 wxyz 格式）")
            # xyzw -> wxyz: [x, y, z, w] -> [w, x, y, z]
            root_rot = root_rot_raw[:, [3, 0, 1, 2]]
        elif abs(first_quat[0]) > 0.9:  # wxyz 格式
            print("（检测到 wxyz 四元数格式，无需转换）")
            root_rot = root_rot_raw
        else:
            print("（警告：无法确定四元数格式，假设是 wxyz）")
            root_rot = root_rot_raw

        print(f"转换后 - root_pos: {root_pos.shape}, root_rot: {root_rot.shape}, dof_pos: {dof_pos.shape}")
        print(f"第一帧四元数(MuJoCo wxyz): {root_rot[0]}")

    # 初始化 Mujoco
    print(f"加载模型: {args.xml_file}")
    model = mujoco.MjModel.from_xml_path(args.xml_file)
    data = mujoco.MjData(model)

    # 检查 qpos 维度匹配
    expected_qpos = 7 + num_dofs  # 3(pos) + 4(quat) + N(dof)
    print(f"模型 qpos 维度: {model.nq}, 预期: {expected_qpos}")
    
    if model.nq != expected_qpos:
        print(f"\n❌ 错误: qpos 维度不匹配!")
        print(f"   模型期望: {model.nq}")
        print(f"   数据提供: {expected_qpos}")
        print(f"\n请运行以下脚本修复数据:")
        print(f"   python scripts/fix_pkl_for_mujoco.py {args.motion_file}")
        sys.exit(1)

    # 初始化 viewer
    viewer = mujoco_viewer.MujocoViewer(model, data)
    viewer.cam.distance = 3.0
    viewer.cam.azimuth = 90
    viewer.cam.elevation = -45
    viewer.cam.lookat[:] = np.array([0.0, -0.25, 0.824])

    # 回放循环
    dt = 1.0 / (fps * args.speed_scale)
    frame = 0
    print(f"\n开始回放（速度: {args.speed_scale}x, 帧间隔: {dt:.4f}s）...")
    print("关闭 viewer 窗口停止回放。")

    try:
        while viewer.is_alive:  # is_alive 是属性，不是方法
            t_start = time.time()

            # 赋值 qpos: [pos(3), quat(4), dof(N)]
            data.qpos[:3] = root_pos[frame]
            data.qpos[3:7] = root_rot[frame]
            data.qpos[7:7 + num_dofs] = dof_pos[frame]

            mujoco.mj_forward(model, data)
            viewer.render()

            # 帧率控制
            elapsed = time.time() - t_start
            sleep_time = dt - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

            frame = (frame + 1) % num_frames

            if frame == 0:
                print("回放循环...")
    except KeyboardInterrupt:
        print("\n用户中断")
    finally:
        viewer.close()
        print("回放结束。")


if __name__ == "__main__":
    main()
