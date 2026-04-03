#!/bin/bash
# PM01 运动可视化便捷脚本

WORKSPACE="/home/abo/rl_workspace/motion_target"
cd "$WORKSPACE"

PYTHON="/home/abo/miniconda3/envs/zqsa01/bin/python"
XML_FILE="$WORKSPACE/pm01_description/xml/serial_pm_v2_merged.xml"

echo "=============================================="
echo "PM01 运动可视化工具"
echo "=============================================="
echo ""

# 如果没有提供参数，列出可用的文件
if [ $# -eq 0 ]; then
    echo "可用的 PKL 文件:"
    echo ""
    find input_twist_pkl/data -name "*.pkl" -type f | while read file; do
        # 尝试获取文件信息
        $PYTHON -c "
import joblib
import os
try:
    data = joblib.load('$file')
    if 'fps' in data and 'dof_pos' in data:
        fps = data['fps']
        frames = data['dof_pos'].shape[0]
        dofs = data['dof_pos'].shape[1]
        basename = os.path.basename('$file')
        print(f'  ✓ {basename}')
        print(f'    帧数: {frames}, FPS: {fps}, 关节: {dofs}')
except Exception as e:
    pass
" 2>/dev/null
    done
    echo ""
    echo "用法: bash scripts/vis.sh <pkl文件名>"
    echo "例如: bash scripts/vis.sh hmr4d_results_29local.pkl"
    exit 0
fi

# 获取文件名
MOTION_FILE="$1"

# 如果不是完整路径，则在 input_twist_pkl/data 中查找
if [ ! -f "$MOTION_FILE" ]; then
    MOTION_FILE="$WORKSPACE/input_twist_pkl/data/$MOTION_FILE"
fi

if [ ! -f "$MOTION_FILE" ]; then
    echo "❌ 文件不存在: $MOTION_FILE"
    exit 1
fi

echo "可视化文件: $MOTION_FILE"
echo "XML 模型: $XML_FILE"
echo "速度倍率: ${2:-1.0}"
echo ""
echo "启动可视化器..."
echo "=============================================="

$PYTHON vis_motion/vis_mujoco_motion.py \
  --motion_file "$MOTION_FILE" \
  --xml_file "$XML_FILE" \
  --speed_scale "${2:-1.0}"
