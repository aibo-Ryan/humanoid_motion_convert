# 无状态估计的处理：
mjlab的npz是24个关节
正在处理: /home/abo/rl_workspace/motion_target/input_mjlab_beyondmimic_csv_npz/walking_forward_4steps_02_100hz.npz
--- 数据形状检查 ---
Key: joint_pos       | 原始: (417, 24)    
Key: joint_vel       | 原始: (417, 24)    
Key: body_pos_w      | 原始: (417, 29, 3) 
Key: body_quat_w     | 原始: (417, 29, 4) 
Key: body_lin_vel_w  | 原始: (417, 29, 3) 
Key: body_ang_vel_w  | 原始: (417, 29, 3) 

成功导出到: motion_data.csv
--- 每一项数据的处理 ---
Key: joint_pos       | 最终形状: (417, 24)
Key: joint_vel       | 最终形状: (417, 24)
Key: body_pos_w      | 最终形状: (417, 3)
Key: body_quat_w     | 最终形状: (417, 4)
Key: body_lin_vel_w  | 最终形状: (417, 3)
Key: body_ang_vel_w  | 最终形状: (417, 3)

--- 导出成功 ---
文件: input_mjlab_beyondmimic_csv_npz/walking_forward_4steps_02_100hz.csv
总列数: 61 (期望值: 24+24+3+4+3+3 = 61)

FPS: 100.0
数据矩阵形状: (417, 425) (不含FPS行)