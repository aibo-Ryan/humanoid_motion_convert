'''
--- 每一项数据的处理 ---
Key: joint_pos       | 最终形状: (417, 24)
Key: joint_vel       | 最终形状: (417, 24)
Key: body_pos_w      | 原始: (417, 29, 3)    -> ⚠️ 检测到多刚体，仅提取 Body[0] (Base)
Key: body_pos_w      | 最终形状: (417, 3)
Key: body_quat_w     | 原始: (417, 29, 4)    -> ⚠️ 检测到多刚体，仅提取 Body[0] (Base)
Key: body_quat_w     | 最终形状: (417, 4)
Key: body_lin_vel_w  | 原始: (417, 29, 3)    -> ⚠️ 检测到多刚体，仅提取 Body[0] (Base)
Key: body_lin_vel_w  | 最终形状: (417, 3)
Key: body_ang_vel_w  | 原始: (417, 29, 3)    -> ⚠️ 检测到多刚体，仅提取 Body[0] (Base)
Key: body_ang_vel_w  | 最终形状: (417, 3)

--- 导出成功 ---
文件: input_mjlab_beyondmimic_csv_npz/walking_forward_4steps_02_100hz.csv
总列数: 61 (期望值: 24+24+3+4+3+3 = 61)
'''
import numpy as np
import pandas as pd
import os
import sys

def export_all_to_one_csv(npz_path, output_csv_name):
    if not os.path.exists(npz_path):
        print(f"错误：找不到文件 {npz_path}")
        return
    
    try:
        data = np.load(npz_path)
        print(f"正在处理: {npz_path}")
        
        # 1. 提取 FPS
        fps_raw = data['fps']


        motion_quat = data['body_quat_w']
        motion_base_quat = motion_quat[:, 0, :]

        fps = float(fps_raw.item()) if isinstance(fps_raw, np.ndarray) and fps_raw.size >= 1 else float(fps_raw)

        # 2. 定义键顺序 (必须严格对应 C++ 读取顺序)
        keys_to_stack = [
            'joint_pos',        # (N, 24)
            'joint_vel',        # (N, 24)
            'body_pos_w',       # (N, 29, 3) -> 需要切片取 [:, 0, :]
            'body_quat_w',      # (N, 29, 4) -> 需要切片取 [:, 0, :]
            'body_lin_vel_w',   # (N, 29, 3) -> 需要切片取 [:, 0, :]
            'body_ang_vel_w'    # (N, 29, 3) -> 需要切片取 [:, 0, :]
        ]
        
        arrays_list = []
        rows_count = None
        
        print(f"\n--- 每一项数据的处理 ---")
        for key in keys_to_stack:
            if key not in data:
                print(f"错误: 缺少键 {key}")
                return
            
            arr = data[key]
            original_shape = arr.shape
            
            # --- 核心修正逻辑 ---
            # 如果是 3 维数据 (Frames, Bodies, Dim)，说明包含所有 29 个连杆
            # 我们只取 Index 0 (通常是 Base/Pelvis)
            if arr.ndim == 3:
                print(f"Key: {key:<15} | 原始: {str(original_shape):<15} -> ⚠️ 检测到多刚体，仅提取 Body[0] (Base)")
                arr = arr[:, 0, :] # 只取第 0 个刚体
            # ------------------
            
            # 确保是 2D
            if arr.ndim == 1:
                arr = arr.reshape(-1, 1)
                
            arrays_list.append(arr)
            print(f"Key: {key:<15} | 最终形状: {arr.shape}")
            
            # 检查帧数对齐
            if rows_count is None:
                rows_count = arr.shape[0]
            elif arr.shape[0] != rows_count:
                print(f"错误: {key} 行数不对齐！")
                return

        # 3. 拼接与保存
        full_matrix = np.hstack(arrays_list)
        df = pd.DataFrame(full_matrix)
        
        # 插入 FPS 头
        metadata_row = np.zeros((1, full_matrix.shape[1]))
        metadata_row[0, 0] = fps
        df_meta = pd.DataFrame(metadata_row)
        final_df = pd.concat([df_meta, df], ignore_index=True)
        
        final_df.to_csv(output_csv_name, index=False, header=False, float_format='%.6f')
        
        print(f"\n--- 导出成功 ---")
        print(f"文件: {output_csv_name}")
        print(f"总列数: {full_matrix.shape[1]} (期望值: 23+23+3+4+3+3 = 59)")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        npz_file = sys.argv[1]
    else:
        npz_file = "/home/abo/rl_workspace/motion_target/input_isaaclab_beyondmimic_csv_npz/data/walk3_subject1_v2_100hz.npz" # 修改为你的实际路径
    
    csv_out = npz_file.replace(".npz", ".csv")
    export_all_to_one_csv(npz_file, csv_out)