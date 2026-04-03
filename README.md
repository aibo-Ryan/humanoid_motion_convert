# Humanoid Motion Convert

PM01 人形机器人运动数据处理与可视化工具，支持多种格式转换、重采样和仿真可视化。

## GUI 界面

![GUI Preview](doc/gui.png)

## 快速开始

```bash
conda activate zqsa01
python -m gui.main
```

## 功能模块

### 1. 数据格式转换

| 格式 | 用途 | 说明 |
|------|------|------|
| PKL | twist/ASAP | 原生格式，包含完整运动信息 |
| CSV | 霆天软件 | 31列 BeyondMimic 格式 |
| NPZ | IsaacLab/MJLab | 仿真输出格式 |

### 2. PKL 格式规范 (twist)

```
FPS             : 30
root_pos        : (N, 3)      # 基座位置
root_rot        : (N, 4)      # 四元数 [w, x, y, z]
dof_pos         : (N, 24)     # 24个关节角度
local_body_pos  : (N, 29, 3)  # 29个身体连杆位置
link_body_list  : list[str]   # 连杆名称列表
```

### 3. CSV 格式规范

31 列数据，BeyondMimic 格式：
```
root_x, root_y, root_z, root_qw, root_qx, root_qy, root_qz, j0...j23
```

### 4. ASAP 格式规范

```
FPS             : 50
root_trans_offset : (N, 3)
pose_aa         : (N, 29, 3)   # 轴角
dof             : (N, 24)
root_rot        : (N, 4)
body_pos_w      : (N, 29, 3)
body_quat_w     : (N, 29, 4)
body_lin_vel_w  : (N, 29, 3)
body_ang_vel_w  : (N, 29, 3)
joint_vel       : (N, 24)
```

## 主要脚本

| 脚本 | 功能 |
|------|------|
| `sim2motion/sim2sim_pm01.py` | Mujoco 仿真录制 (GUI) |
| `input_twist_pkl/main_pkl_to_csv.py` | PKL → CSV |
| `input_twist_pkl/main_csv_to_pkl.py` | CSV → PKL |
| `input_twist_pkl/main_pkl_resample.py` | PKL 重采样 |
| `vis_motion/vis_pm01_motion.py` | IsaacGym 可视化 |

## 注意事项

- CSV 格式与 MJLab/BeyondMimic 的 CSV 维度不同
- 四元数统一使用 `[w, x, y, z]` 顺序
- 默认帧率：100 Hz (dt=0.001, decimation=10)

## 依赖

- PyTorch
- PyQt5 (GUI)
- IsaacGym (可视化)
- Mujoco (仿真录制)
