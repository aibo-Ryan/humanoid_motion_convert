#!/bin/bash
# 完整的解决方案：从CSV生成PKL并可视化

WORKSPACE="/home/abo/rl_workspace/motion_target"
cd "$WORKSPACE"

# 设置Python路径
PYTHON="/home/abo/miniconda3/envs/zqsa01/bin/python"

# 输入输出文件
CSV_FILE="$WORKSPACE/input_twist_pkl/data/walking_forward_4steps_right_02_stageii_edit.csv"
XML_FILE="$WORKSPACE/pm01_description/xml/serial_pm_v2_merged.xml"
PKL_FILE="$WORKSPACE/input_twist_pkl/data/walking_forward_4steps_right_02_stageii_edit.pkl"

echo "=============================================="
echo "步骤 1: 从 CSV 生成 PKL"
echo "=============================================="
echo "CSV 文件: $CSV_FILE"
echo "XML 文件: $XML_FILE"
echo "输出 PKL: $PKL_FILE"
echo ""

$PYTHON input_twist_pkl/main_csv_to_pkl.py \
  --csv_file "$CSV_FILE" \
  --xml_file "$XML_FILE" \
  --pkl_file "$PKL_FILE" \
  --fps 30

if [ $? -ne 0 ]; then
    echo "❌ PKL 生成失败！"
    exit 1
fi

echo ""
echo "=============================================="
echo "步骤 2: 修复 PKL 以适配 MuJoCo"
echo "=============================================="

$PYTHON scripts/fix_pkl_for_mujoco.py "$PKL_FILE"

if [ $? -ne 0 ]; then
    echo "❌ PKL 修复失败！"
    exit 1
fi

echo ""
echo "=============================================="
echo "步骤 3: 可视化运动"
echo "=============================================="

FIXED_PKL="${PKL_FILE%.pkl}_fixed.pkl"
$PYTHON vis_motion/vis_mujoco_motion.py \
  --motion_file "$FIXED_PKL" \
  --xml_file "$XML_FILE" \
  --speed_scale 1.0

echo ""
echo "=============================================="
echo "完成！"
echo "=============================================="
