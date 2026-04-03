#!/bin/bash

# 加载 conda 的 shell 函数
source /home/abo/miniconda3/etc/profile.d/conda.sh

# 激活环境
conda activate zqsa01

# 创建临时 rcfile，先加载默认配置，再设置环境
TEMP_RC="/tmp/bashrc_conda_$$"
cat > "$TEMP_RC" << 'INNERSCRIPT'
# 加载用户默认配置
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi

# 设置 LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/home/abo/miniconda3/envs/zqsa01/lib:$LD_LIBRARY_PATH

# 确保环境已激活
conda activate zqsa01 2>/dev/null || true

# 清理临时文件
rm -f "/tmp/bashrc_conda_$$"
INNERSCRIPT

# 清除 LD_LIBRARY_PATH，避免影响新 bash
unset LD_LIBRARY_PATH

# 启动交互式 bash，使用临时 rcfile
exec bash --rcfile "$TEMP_RC" -i
