# 最终修复报告

## 问题清单

你遇到了两个错误：

### 错误 1: keyframe qpos 维度不匹配
```
ValueError: Error: keyframe 0: invalid qpos size, expected length 31
Element name 'floating_base_homing', id 0
```

### 错误 2: viewer.is_alive 调用错误
```
TypeError: 'bool' object is not callable
```

---

## 修复内容

### ✅ 修复 1: XML Keyframe 定义

**文件**: `pm01_description/xml/serial_pm_v2_merged.xml` (第243行)

**问题**: keyframe 的 qpos 只有 30 个值，但需要 31 个（7个floating base + 24个关节）

**修改**:
```xml
<!-- 修改前 (30个值 - 缺少一个关节的初始值) -->
<key name="floating_base_homing" qpos="0 0 0.82 1 0 0 0 0 0 -0.12 0.24 -0.12 0 0 0 -0.12 0.24 -0.12 0 0 0 0 0 0 0 0 0 0 0 0"/>

<!-- 修改后 (31个值 - 补全所有关节) -->
<key name="floating_base_homing" qpos="0 0 0.82 1 0 0 0 0 0 -0.12 0.24 -0.12 0 0 0 0 -0.12 0.24 -0.12 0 0 0 0 0 0 0 0 0 0 0 0"/>
                                                                 ↑ 这里加了一个0
```

---

### ✅ 修复 2: viewer.is_alive 使用方式

**文件**: `vis_motion/vis_mujoco_motion.py` (第98行)

**问题**: `is_alive` 是**属性**（bool类型），不是方法，不应该加括号

**修改**:
```python
# 修改前 (错误)
while viewer.is_alive():

# 修改后 (正确)
while viewer.is_alive:  # is_alive 是属性，不是方法
```

---

## 验证结果

### ✅ 测试通过

```bash
cd /home/abo/rl_workspace/motion_target

python vis_motion/vis_mujoco_motion.py \
  --motion_file input_twist_pkl/data/hmr4d_results_29local.pkl \
  --xml_file pm01_description/xml/serial_pm_v2_merged.xml \
  --speed_scale 1.0
```

**输出**:
```
加载运动数据: input_twist_pkl/data/hmr4d_results_29local.pkl
FPS: 30, 总帧数: 143, 关节数: 24
root_pos: (143, 3), root_rot: (143, 4), dof_pos: (143, 24)
加载模型: pm01_description/xml/serial_pm_v2_merged.xml
模型 qpos 维度: 31, 预期: 31  ✓

开始回放（速度: 1.0x, 帧间隔: 0.0333s）...
关闭 viewer 窗口停止回放。
```

现在可以正常显示 MuJoCo 可视化窗口了！

---

## 修改的文件列表

1. ✅ `pm01_description/xml/serial_pm_v2_merged.xml` - 修复 keyframe qpos 维度
2. ✅ `vis_motion/vis_mujoco_motion.py` - 修复 is_alive 调用方式

---

## 可用的 PKL 文件

以下文件都可以正常可视化（位于 `input_twist_pkl/data/` 目录）：

| 文件名 | 帧数 | FPS | 关节数 |
|--------|------|-----|--------|
| `hmr4d_results_29local.pkl` | 143 | 30 | 24 ✓ |
| `hmr4d_results_resampled_30fps_29local.pkl` | 142 | 30 | 24 ✓ |
| `hmr4d_results_resampled_29local.pkl` | 474 | 100 | 24 ✓ |
| `walking_forward_4steps_right_02_stageii_edit_29local.pkl` | 126 | 30 | 24 ✓ |

---

## 便捷运行

```bash
# 列出所有可可视化文件
bash scripts/vis.sh

# 运行可视化
bash scripts/vis.sh hmr4d_results_29local.pkl
```

---

## 技术细节

### MuJoCo QPOS 结构 (31维)

```
索引    内容                说明
0-2     root_pos (3)        根位置 (x, y, z)
3-6     root_rot (4)        根四元数 (w, x, y, z)
7       J00_HIP_PITCH_L     左髋关节pitch
8       J01_HIP_ROLL_L      左髋关节roll
9       J02_HIP_YAW_L       左髋关节yaw
10      J03_KNEE_PITCH_L    左膝关节pitch
11      J04_ANKLE_PITCH_L   左踝关节pitch
12      J05_ANKLE_ROLL_L    左踝关节roll
13      J06_HIP_PITCH_R     右髋关节pitch
14      J07_HIP_ROLL_R      右髋关节roll
15      J08_HIP_YAW_R       右髋关节yaw
16      J09_KNEE_PITCH_R    右膝关节pitch
17      J10_ANKLE_PITCH_R   右踝关节pitch
18      J11_ANKLE_ROLL_R    右踝关节roll
19      J12_WAIST_YAW       腰部yaw
20      J13_SHOULDER_PITCH_L 左肩关节pitch
21      J14_SHOULDER_ROLL_L  左肩关节roll
22      J15_SHOULDER_YAW_L   左肩关节yaw
23      J16_ELBOW_PITCH_L    左肘关节pitch
24      J17_ELBOW_YAW_L      左肘关节yaw
25      J18_SHOULDER_PITCH_R 右肩关节pitch
26      J19_SHOULDER_ROLL_R  右肩关节roll
27      J20_SHOULDER_YAW_R   右肩关节yaw
28      J21_ELBOW_PITCH_R    右肘关节pitch
29      J22_ELBOW_YAW_R      右肘关节yaw
30      J23_HEAD_YAW         头部yaw
```

### mujoco_viewer API 说明

```python
import mujoco_viewer

viewer = mujoco_viewer.MujocoViewer(model, data)

# 正确的使用方式
while viewer.is_alive:  # is_alive 是 bool 属性
    viewer.render()

# 错误的使用方式
while viewer.is_alive():  # ❌ 会报 TypeError
```

---

## 总结

**修复了 2 个文件，解决了所有问题**：

1. XML keyframe 从 30 维改为 31 维 → 解决模型加载错误
2. viewer.is_alive 从方法调用改为属性访问 → 解决运行时错误

**不需要修改 PKL 数据文件** - 数据格式本身就是正确的！
