正在处理: data/walk3_subject1_v2_100hz.npz

--- 每一项数据的处理 ---
Key: joint_pos       | 最终形状: (1260, 23)
Key: joint_vel       | 最终形状: (1260, 23)
Key: body_pos_w      | 原始: (1260, 24, 3)   -> ⚠️ 检测到多刚体，仅提取 Body[0] (Base)
Key: body_pos_w      | 最终形状: (1260, 3)
Key: body_quat_w     | 原始: (1260, 24, 4)   -> ⚠️ 检测到多刚体，仅提取 Body[0] (Base)
Key: body_quat_w     | 最终形状: (1260, 4)
Key: body_lin_vel_w  | 原始: (1260, 24, 3)   -> ⚠️ 检测到多刚体，仅提取 Body[0] (Base)
Key: body_lin_vel_w  | 最终形状: (1260, 3)
Key: body_ang_vel_w  | 原始: (1260, 24, 3)   -> ⚠️ 检测到多刚体，仅提取 Body[0] (Base)
Key: body_ang_vel_w  | 最终形状: (1260, 3)

--- 导出成功 ---
文件: data/walk3_subject1_v2_100hz.csv
总列数: 59 (期望值: 24+24+3+4+3+3 = 61)