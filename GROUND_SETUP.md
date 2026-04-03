# 添加地面到 MuJoCo 可视化

## 问题

MuJoCo 可视化场景中没有地面，机器人看起来像是悬空在虚空中。

## 解决方案

在 XML 模型文件中添加地面几何体和材质。

## 修改内容

### 1. 添加地面几何体 (worldbody 部分)

**文件**: `pm01_description/xml/serial_pm_v2_merged.xml` (第77-81行)

```xml
<worldbody>
    <!-- Ground plane -->
    <geom name="ground" type="plane" size="0 0 0.05" pos="0 0 0" quat="1 0 0 0" 
          material="groundplane" contype="1" conaffinity="1" condim="3" priority="1" 
          friction="0.8 0.02 0.01"/>
    
    <light name="spotlight" mode="targetbodycom" target="LINK_BASE" pos="0 -1 2"/>
    ...
</worldbody>
```

**参数说明**:
- `type="plane"`: 平面类型（无限延伸的地面）
- `size="0 0 0.05"`: 地面厚度（plane类型的size[2]决定可见厚度）
- `pos="0 0 0"`: 位于世界坐标原点
- `material="groundplane"`: 引用地面材质
- `contype="1" conaffinity="1"`: 启用碰撞检测
- `friction="0.8 0.02 0.01"`: 摩擦系数（滑动、滚动、扭转）

### 2. 添加地面材质 (asset 部分)

**文件**: `pm01_description/xml/serial_pm_v2_merged.xml` (第74-79行)

```xml
<asset>
    <include file="assets.xml"/>
    
    <!-- Ground material -->
    <texture name="texplane" type="2d" builtin="checker" rgb1="0.2 0.3 0.4" rgb2="0.1 0.2 0.3" 
             width="512" height="512" mark="cross" markrgb="0.8 0.8 0.8"/>
    <material name="groundplane" texture="texplane" texrepeat="4 4" texuniform="true" 
              reflectance="0.2"/>
</asset>
```

**参数说明**:
- `texture`: 棋盘格纹理
  - `rgb1="0.2 0.3 0.4"`: 第一种颜色（深蓝灰）
  - `rgb2="0.1 0.2 0.3"`: 第二种颜色（更深的蓝灰）
  - `width="512" height="512"`: 纹理分辨率
  - `mark="cross"`: 添加十字标记
  
- `material`: 材质属性
  - `texrepeat="4 4"`: 纹理重复4x4次
  - `reflectance="0.2"`: 20%反射率

## 验证结果

```
✓ 模型加载成功!
  nq (qpos维度): 31
  ngeom (几何体数量): 40
  ✓ 找到地面几何体: ground (id=0)
    类型: 0 (0=plane)
    位置: [0. 0. 0.]
```

## 自定义地面样式

### 样式 1: 灰色纯色地面

```xml
<asset>
    <material name="groundplane" rgba="0.5 0.5 0.5 1" reflectance="0.1"/>
</asset>

<worldbody>
    <geom name="ground" type="plane" size="0 0 0.05" pos="0 0 0" 
          material="groundplane"/>
</worldbody>
```

### 样式 2: 绿色草地

```xml
<asset>
    <texture name="texplane" type="2d" builtin="checker" rgb1="0.2 0.6 0.2" rgb2="0.15 0.5 0.15" 
             width="512" height="512"/>
    <material name="groundplane" texture="texplane" texrepeat="8 8"/>
</asset>
```

### 样式 3: 木色地板

```xml
<asset>
    <texture name="texplane" type="2d" builtin="checker" rgb1="0.7 0.5 0.3" rgb2="0.6 0.4 0.25" 
             width="512" height="512"/>
    <material name="groundplane" texture="texplane" texrepeat="2 4" reflectance="0.3"/>
</asset>
```

### 样式 4: 白色网格地面（适合调试）

```xml
<asset>
    <material name="groundplane" rgba="1 1 1 1"/>
</asset>

<worldbody>
    <geom name="ground" type="plane" size="0 0 0.01" pos="0 0 0" 
          material="groundplane" rgba="1 1 1 0.3"/>
</worldbody>
```

## 地面高度调整

如果机器人站在地面上时位置不对，可以调整地面的 `pos` 参数：

```xml
<!-- 地面降低 0.1 米 -->
<geom name="ground" type="plane" size="0 0 0.05" pos="0 0 -0.1" .../>
```

或者调整机器人的初始高度（keyframe中的 root_pos_z）：

```xml
<!-- 机器人初始高度改为 0.9 米 -->
<key name="floating_base_homing" qpos="0 0 0.9 1 0 0 0 ..."/>
```

## MuJoCo 地面最佳实践

1. **plane 类型**: 用于无限延伸的地面（性能最优）
2. **box 类型**: 用于有限大小的平台
3. **collision 设置**: 确保 `contype` 和 `conaffinity` 都设为 1 以启用碰撞
4. **摩擦系数**: 典型值 `0.8 0.02 0.01`（滑动、滚动、扭转）

## 运行可视化

```bash
cd /home/abo/rl_workspace/motion_target

python vis_motion/vis_mujoco_motion.py \
  --motion_file input_twist_pkl/data/hmr4d_results_29local.pkl \
  --xml_file pm01_description/xml/serial_pm_v2_merged.xml
```

现在你应该能看到带有棋盘格纹理的地面了！
