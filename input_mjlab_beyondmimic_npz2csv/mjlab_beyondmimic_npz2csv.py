'''
完整的转换
--- 数据形状检查 ---
Key: joint_pos       | 原始: (417, 24)    -> 处理后: (417, 24)
Key: joint_vel       | 原始: (417, 24)    -> 处理后: (417, 24)
Key: body_pos_w      | 原始: (417, 29, 3) -> 处理后: (417, 87)
Key: body_quat_w     | 原始: (417, 29, 4) -> 处理后: (417, 116)
Key: body_lin_vel_w  | 原始: (417, 29, 3) -> 处理后: (417, 87)
Key: body_ang_vel_w  | 原始: (417, 29, 3) -> 处理后: (417, 87)
'''

import numpy as np
import pandas as pd
import os
import sys

def export_all_to_one_csv(npz_path, output_csv_name):
    # 1. 加载数据
    if not os.path.exists(npz_path):
        print(f"错误：找不到文件 {npz_path}")
        return
    
    try:
        data = np.load(npz_path)
        print(f"正在处理: {npz_path}")
        
        # 2. 安全提取 FPS (修复 DeprecationWarning)
        # 如果是数组取第一个元素，如果是标量直接取值
        fps_raw = data['fps']
        if isinstance(fps_raw, np.ndarray) and fps_raw.size >= 1:
            fps = float(fps_raw.item())
        else:
            fps = float(fps_raw)

        # 3. 定义需要提取的键顺序 (必须与 C++ 读取顺序一致)
        # 顺序: JointPos | JointVel | BodyPos | BodyQuat | BodyLinVel | BodyAngVel
        keys_to_stack = [
            'joint_pos', 
            'joint_vel', 
            'body_pos_w', 
            'body_quat_w', 
            'body_lin_vel_w', 
            'body_ang_vel_w'
        ]
        
        # 4. 准备数据列表，并修复维度问题 (修复 ValueError)
        arrays_list = []
        rows_count = None
        
        print("--- 数据形状检查 ---")
        for key in keys_to_stack:
            if key not in data:
                print(f"错误: npz 中缺少键 {key}")
                return
            
            arr = data[key]
            original_shape = arr.shape
            
            # 关键修复逻辑：如果维度 > 2 (例如 (417, 1, 3))，强制转换为 (417, 3)
            if arr.ndim > 2:
                # reshape(行数, -1) 会自动把剩下的维度展平
                arr = arr.reshape(arr.shape[0], -1)
            
            # 确保是 2D (N, 1) 而不是 1D (N,)，防止拼接出错
            if arr.ndim == 1:
                arr = arr.reshape(-1, 1)
                
            arrays_list.append(arr)
            print(f"Key: {key:<15} | 原始: {str(original_shape):<12} -> 处理后: {arr.shape}")
            
            # 检查行数是否对齐
            if rows_count is None:
                rows_count = arr.shape[0]
            elif arr.shape[0] != rows_count:
                print(f"错误: {key} 的行数 ({arr.shape[0]}) 与之前的行数 ({rows_count}) 不一致！")
                return

        # 5. 横向拼接
        full_matrix = np.hstack(arrays_list)
        
        # 6. 构建 DataFrame
        df = pd.DataFrame(full_matrix)
        
        # 7. 插入 FPS 到第一行 (第一列存 FPS，其余补 0)
        # 构造一行全是 0 的数据
        metadata_row = np.zeros((1, full_matrix.shape[1]))
        metadata_row[0, 0] = fps
        df_meta = pd.DataFrame(metadata_row)
        
        # 8. 合并并保存
        final_df = pd.concat([df_meta, df], ignore_index=True)
        
        final_df.to_csv(output_csv_name, index=False, header=False, float_format='%.6f')
        
        print(f"\n成功导出到: {output_csv_name}")
        print(f"FPS: {fps}")
        print(f"数据矩阵形状: {full_matrix.shape} (不含FPS行)")

    except Exception as e:
        print(f"处理过程中发生未知错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 设置输入输出路径
    npz_path = "/home/abo/rl_workspace/motion_target/input_mjlab_beyondmimic_csv_npz/walking_forward_4steps_02_100hz.npz"  # 输入的npz文件路径
    csv_path = "motion_data.csv"  # 输出的csv文件路径
    
    # 转换文件
    # convert_npz_to_csv(npz_path, csv_path)
    export_all_to_one_csv(npz_path, csv_path)
    print(f"转换完成！CSV文件已保存至: {csv_path}")
