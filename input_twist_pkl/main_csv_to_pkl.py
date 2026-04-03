import numpy as np
import pickle
import pandas as pd
import torch
from kinematics_model import KinematicsModel



def qpos_to_motion_data(qpos_list,xml_file,save_path,fps):
    qpos_list = np.array(qpos_list)

    # Initialize the forward kinematics
    device = "cuda:0"
    kinematics_model = KinematicsModel(xml_file, device=device)

    root_pos = qpos_list[:, :3]
    root_rot = qpos_list[:, 3:7]
    # root_rot[:, [0, 1, 2, 3]] = root_rot[:, [1, 2, 3, 0]]
    dof_pos = qpos_list[:, 7:]
    num_frames = root_pos.shape[0]

    # obtain local body pos
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
    HEIGHT_ADJUST = False
    PERFRAME_ADJUST = False
    if HEIGHT_ADJUST:
        body_pos, _ = kinematics_model.forward_kinematics(
            torch.from_numpy(root_pos).to(device=device, dtype=torch.float),
            torch.from_numpy(root_rot).to(device=device, dtype=torch.float),
            torch.from_numpy(dof_pos).to(device=device, dtype=torch.float)
        )
        ground_offset = 0.00
        if not PERFRAME_ADJUST:
            lowest_height = torch.min(body_pos[..., 2]).item()
            root_pos[:, 2] = root_pos[:, 2] - lowest_height + ground_offset
        else:
            for i in range(root_pos.shape[0]):
                lowest_body_part = torch.min(body_pos[i, :, 2])
                root_pos[i, 2] = root_pos[i, 2] - lowest_body_part + ground_offset

    print("local_body_pos:", local_body_pos)
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

def csv_to_pkl(csv_file, xml_file, pkl_file=None, fps=100):
    """
    将CSV文件转换回pkl格式
    CSV格式: 3列base位置 + 4列姿态 + 24列关节角度 = 31列
    
    Args:
        csv_file: 输入的csv文件路径
        pkl_file: 输出的pkl文件路径(可选，默认与输入文件同名)
        fps: 帧率(默认100)
    """
    # 读取CSV文件
    df = pd.read_csv(csv_file, header=None)
    data = df.values
    
    print(f"CSV data shape: {data.shape}")
    
    # 提取数据
    root_pos = data[:, :3]      # 前3列: 位置
    root_rot = data[:, 3:7]     # 中间4列: 姿态
    dof_pos = data[:, 7:]       # 后24列: 关节角度
    
    print(f"root_pos shape: {root_pos.shape}")
    print(f"root_rot shape: {root_rot.shape}")
    print(f"dof_pos shape: {dof_pos.shape}")

    qpos_list = []
    for i in range(data.shape[0]):
        qpos_list.append(data[i,:])
    print("qpos_list shape:", len(qpos_list))
    # 构造pkl数据结构
    # motion_data = {
    #     "fps": fps,
    #     "root_pos": root_pos,
    #     "root_rot": root_rot,
    #     "dof_pos": dof_pos,
    #     "local_body_pos": np.zeros((len(data), 29, 3)),  # 29个身体部位，每个3D位置
    #     "link_body_list": ['LINK_BASE', 'LINK_HIP_PITCH_L', 'LINK_HIP_ROLL_L', 'LINK_HIP_YAW_L', 'LINK_KNEE_PITCH_L', 'LINK_ANKLE_PITCH_L', 'LINK_ANKLE_ROLL_L', 'LINK_FOOT_L', 'LINK_HIP_PITCH_R', 'LINK_HIP_ROLL_R', 'LINK_HIP_YAW_R', 'LINK_KNEE_PITCH_R', 'LINK_ANKLE_PITCH_R', 'LINK_ANKLE_ROLL_R', 'LINK_FOOT_R', 'LINK_TORSO_YAW', 'LINK_SHOULDER_PITCH_L', 'LINK_SHOULDER_ROLL_L', 'LINK_SHOULDER_YAW_L', 'LINK_ELBOW_PITCH_L', 'LINK_ELBOW_YAW_L', 'LINK_ELBOW_END_L', 'LINK_SHOULDER_PITCH_R', 'LINK_SHOULDER_ROLL_R', 'LINK_SHOULDER_YAW_R', 'LINK_ELBOW_PITCH_R', 'LINK_ELBOW_YAW_R', 'LINK_ELBOW_END_R', 'LINK_HEAD_YAW']
    # }
    
    # 设置输出文件路径
    if pkl_file is None:
        # pkl_file = csv_file.replace(".csv", "_edit.pkl")
        pkl_file = csv_file.replace(".csv", ".pkl")

    qpos_to_motion_data(qpos_list=qpos_list,xml_file=xml_file,save_path=pkl_file,fps=fps)
    

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="将CSV文件转换为PKL运动数据格式")
    parser.add_argument('--csv_file', type=str, 
                        default="/home/abo/rl_workspace/_dataset/mujoco_motions_pm01/pm01_motion_walk_backward_resampled_30fps.csv",
                        help='输入的CSV文件路径')
    parser.add_argument('--xml_file', type=str,
                        default="pm01_description/xml/serial_pm_v2_merged.xml",
                        help='MuJoCo XML模型文件路径')
    parser.add_argument('--pkl_file', type=str, default=None,
                        help='输出的PKL文件路径（默认：CSV文件名替换为.pkl）')
    parser.add_argument('--fps', type=int, default=30,
                        help='帧率（默认30）')
    
    args = parser.parse_args()
    
    # 转换
    csv_to_pkl(csv_file=args.csv_file, xml_file=args.xml_file, pkl_file=args.pkl_file, fps=args.fps)