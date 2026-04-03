#!/bin/bash
# 从 CSV 生成 PKL 文件的便捷脚本

WORKSPACE="/home/abo/rl_workspace/motion_target"
cd "$WORKSPACE"

# 设置Python路径
PYTHON="/home/abo/miniconda3/envs/zqsa01/bin/python"

# 输入输出文件
CSV_FILE="$WORKSPACE/input_twist_pkl/data/walking_forward_4steps_right_02_stageii_edit.csv"
XML_FILE="$WORKSPACE/pm01_description/xml/serial_pm_v2_merged.xml"

echo "=== 从 CSV 生成 PKL ==="
echo "CSV 文件: $CSV_FILE"
echo "XML 文件: $XML_FILE"

$PYTHON input_twist_pkl/main_csv_to_pkl.py \
  --csv_file "$CSV_FILE" \
  --xml_file "$XML_FILE" \
  --fps 30

echo ""
echo "=== 完成 ==="
