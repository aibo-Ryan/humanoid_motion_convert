# 四元数格式转换说明

## 问题

PKL 文件中的四元数使用 **xyzw** 格式，但 MuJoCo 使用 **wxyz** 格式。如果不进行转换，机器人的初始姿态和旋转会完全错误。

## 检测结果

```
原始四元数 [0]: [ 0.04776823  0.08560964 -0.24253384  0.96517694]
                                           ↑ 最后一个值接近1，说明是 xyzw 格式

转换后四元数 [0]: [ 0.96517694  0.04776823  0.08560964 -0.24253384]
                  ↑ w 移到了第一位，现在是 wxyz 格式
```

## 转换逻辑

**文件**: `vis_motion/vis_mujoco_motion.py` (第60-81行)

```python
# 检查四元数格式并转换
first_quat = root_rot_raw[0]
if abs(first_quat[3]) > 0.9:  # xyzw 格式（w在最后）
    print("（检测到 xyzw 四元数格式，转换为 MuJoCo 的 wxyz 格式）")
    # xyzw -> wxyz: [x, y, z, w] -> [w, x, y, z]
    root_rot = root_rot_raw[:, [3, 0, 1, 2]]
elif abs(first_quat[0]) > 0.9:  # wxyz 格式（w在第一位）
    print("（检测到 wxyz 四元数格式，无需转换）")
    root_rot = root_rot_raw
else:
    print("（警告：无法确定四元数格式，假设是 wxyz）")
    root_rot = root_rot_raw
```

## 四元数格式对照

| 系统/库 | 格式 | 说明 |
|---------|------|------|
| **MuJoCo** | `w, x, y, z` | 实部在前 |
| **IsaacGym/IsaacSim** | `x, y, z, w` | 实部在后 |
| **ROS** | `x, y, z, w` | 实部在后 |
| **PyTorch3D** | `w, x, y, z` | 实部在前 |
| **SciPy** | 可配置 | 默认 `x, y, z, w` |

## 转换公式

### xyzw → wxyz
```python
quat_wxyz = quat_xyzw[:, [3, 0, 1, 2]]
```

### wxyz → xyzw
```python
quat_xyzw = quat_wxyz[:, [1, 2, 3, 0]]
```

## 判断方法

检查四元数的第一个和最后一个元素：

```python
quat = [q0, q1, q2, q3]

if abs(q3) > 0.9:
    # 最后一个元素接近±1 → xyzw 格式
    # 因为单位四元数 [0,0,0,1] 表示无旋转
    format = "xyzw"
elif abs(q0) > 0.9:
    # 第一个元素接近±1 → wxyz 格式
    # 因为单位四元数 [1,0,0,0] 表示无旋转
    format = "wxyz"
```

## 为什么需要转换？

四元数表示旋转：`q = w + xi + yj + zk`

- **xyzw 格式**: `[x, y, z, w]` - 向量部分在前，标量部分在后
- **wxyz 格式**: `[w, x, y, z]` - 标量部分在前，向量部分在后

如果不转换：
- 会把 `x` 当成 `w`，`w` 当成 `z`
- 导致旋转轴和角度完全错误
- 机器人可能出现：
  - 初始姿态倾斜
  - 旋转方向相反
  - 关节位置错乱

## 坐标系约定

### MuJoCo 世界坐标系

```
     Z (向上)
     |
     |
     +----- Y (右)
    /
   X (前)
```

- **X**: 前向
- **Y**: 右向  
- **Z**: 上向（重力方向为负）

### 数据中的坐标系

根据 PKL 数据分析：
- `root_pos[0] = [-0.003, -0.008, 0.805]`
  - X ≈ 0（前后位置）
  - Y ≈ 0（左右位置）
  - Z ≈ 0.8m（高度）

这说明数据使用的坐标系与 MuJoCo **一致**（都是右手坐标系，Z向上）。

## 验证清单

运行可视化前，确认：

- [x] 四元数格式已转换为 wxyz
- [x] 位置坐标与 MuJoCo 坐标系一致
- [x] 地面已添加到 XML 模型
- [x] keyframe qpos 维度正确（31维）

## 完整的数据流

```
CSV/PKL 文件
    ↓ (xyzw 格式)
    ↓
检测: abs(quat[3]) > 0.9? → 是 → xyzw 格式
    ↓
转换: quat[:, [3, 0, 1, 2]]
    ↓ (wxyz 格式)
    ↓
赋值给 data.qpos[3:7]
    ↓
MuJoCo 正向运动学
    ↓
可视化（正确的姿态）
```

## 测试输出示例

```
加载运动数据: input_twist_pkl/data/hmr4d_results_29local.pkl
FPS: 30, 总帧数: 143, 关节数: 24
root_pos: (143, 3), root_rot: (143, 4), dof_pos: (143, 24)
（检测到 xyzw 四元数格式，转换为 MuJoCo 的 wxyz 格式）
转换后 - root_pos: (143, 3), root_rot: (143, 4), dof_pos: (143, 24)
第一帧四元数(MuJoCo wxyz): [ 0.96517694  0.04776823  0.08560964 -0.24253384]
加载模型: pm01_description/xml/serial_pm_v2_merged.xml
模型 qpos 维度: 31, 预期: 31

开始回放（速度: 1.0x, 帧间隔: 0.0333s）...
```
